"""Модуль серверной части игры MOOD.

Этот модуль содержит реализацию серверной логики многопользовательской текстовой игры MOOD.
Он обрабатывает подключения клиентов, управляет состоянием игры и взаимодействует с игроками.
"""

import asyncio
import shlex
import random
import os
import gettext
from babel.support import Translations
from ..common import constants as const

games = {}  # экземпляры игр для разных пользователей
clients = {}  # соответствие writer -> username
usernames = set()
global_monsters = {}
moving_monsters_enabled = True  # По умолчанию режим бродячих монстров включен
client_locales = {}  # соответствие writer -> locale

locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
translations = {
    'en': gettext.NullTranslations(),  # Для английского используем исходные строки
    'ru_RU.UTF8': gettext.translation('messages', locale_dir, ['ru'], fallback=True)
}


async def broadcast_message(message, exclude_writer=None):
    """
    Отправить сообщение всем подключенным клиентам, кроме исключенного.

    Функция проходит по всем подключенным клиентам и отправляет им указанное сообщение
    с учетом локали каждого клиента.

    Args:
        message: Сообщение для отправки.
        exclude_writer: Клиент, которому не нужно отправлять сообщение.
    """
    to_remove = []

    for writer, username in clients.items():
        if writer != exclude_writer:
            try:
                # Получаем локаль клиента
                locale = client_locales.get(writer, 'en')
                translator = get_translator(locale)

                # Переводим сообщение
                translated_message = translator.gettext(message)

                writer.write(f"{translated_message}\n".encode())
                await writer.drain()
            except Exception as e:
                print(f"Error broadcasting to {username}: {e}")
                to_remove.append(writer)

    for writer in to_remove:
        username = clients.get(writer)
        if username:
            print(f"Removing disconnected client: {username}")
            if username in usernames:
                usernames.remove(username)
            if username in games:
                del games[username]
            if writer in client_locales:
                del client_locales[writer]
            del clients[writer]


async def move_monsters():
    """
    Периодически перемещать случайных монстров в случайном направлении.

    Эта асинхронная функция запускается как отдельная задача и каждые 30 секунд
    выбирает случайного монстра и пытается переместить его в случайном направлении.
    Если выбранное направление занято другим монстром, функция выбирает другого монстра
    и направление, пока не найдет свободную клетку.
    При успешном перемещении всем игрокам отправляется сообщение о движении монстра.
    Если на новой позиции находятся игроки, инициируется "энкаунтер".
    """
    while True:
        await asyncio.sleep(30)  # Ждем 30 секунд

        # Проверяем, включен ли режим бродячих монстров
        if not moving_monsters_enabled:
            continue

        if not global_monsters:  # Если нет монстров, пропускаем
            continue

        # Выбираем случайного монстра и пытаемся его переместить
        success = False
        attempts = 0
        max_attempts = 10 * len(global_monsters)  # Ограничиваем количество попыток

        while not success and attempts < max_attempts:
            attempts += 1

            # Получаем список позиций всех монстров
            monster_positions = list(global_monsters.keys())
            if not monster_positions:
                break

            # Выбираем случайного монстра
            monster_pos = random.choice(monster_positions)
            monster_name, monster_hello, monster_hp = global_monsters[monster_pos]

            # Выбираем случайное направление (dx, dy)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # right, left, down, up
            direction = random.choice(directions)
            dx, dy = direction

            # Определяем новую позицию
            new_x = (monster_pos[0] + dx) % const.GRID_SIZE
            new_y = (monster_pos[1] + dy) % const.GRID_SIZE
            new_pos = (new_x, new_y)

            # Проверяем, свободна ли новая позиция
            if new_pos in global_monsters:
                continue  # Позиция занята другим монстром, пробуем ещё раз

            # Перемещаем монстра
            del global_monsters[monster_pos]
            global_monsters[new_pos] = (monster_name, monster_hello, monster_hp)

            # Определяем строковое представление направления
            direction_str = "right" if dx == 1 else "left" if dx == -1 else "down" if dy == 1 else "up"

            # Отправляем сообщение всем игрокам
            await broadcast_message(f"{const.RESP_BROADCAST}: {monster_name} moved one cell {direction_str}")

            # Проверяем, есть ли игроки на новой позиции монстра
            affected_players = []
            for username, game in games.items():
                if game.player_x == new_x and game.player_y == new_y:
                    affected_players.append(username)

            # Если есть игроки, вызываем "энкаунтер"
            for username in affected_players:
                for writer, name in clients.items():
                    if name == username:
                        writer.write(f"{const.RESP_ENCOUNTER}: {monster_name} {monster_hello}\n".encode())
                        await writer.drain()

            success = True


def get_translator(locale='en'):
    """
    Получить объект перевода для указанной локали.

    Args:
        locale: Имя локали.

    Returns:
        gettext.NullTranslations or gettext.GNUTranslations: Объект для перевода строк.
    """
    return translations.get(locale, translations['en'])

class MUDGame:
    """
    Класс для управления игровым процессом конкретного игрока.

    Этот класс хранит состояние игры для одного пользователя и
    обрабатывает команды, которые приходят от клиента.
    """

    def __init__(self, username=None):
        """
        Инициализировать игру для пользователя.

        Создает новую игру с указанным именем пользователя и начальными параметрами.

        Args:
            username: Имя игрока.
        """
        self.grid_size = const.GRID_SIZE
        self.player_x = 0
        self.player_y = 0
        self.weapons = dict(const.DEFAULT_WEAPONS)
        self.username = username  # Сохраняем имя пользователя

    def handle_command(self, command):
        """
        Обработать команду от клиента.

        Разбирает команду на части и вызывает соответствующий обработчик.

        Args:
            command: Строка с командой от клиента.

        Returns:
            tuple: Пара (ответ клиенту, широковещательное сообщение).
        """
        parts = shlex.split(command)
        if not parts:
            return f"{const.RESP_ERROR}: Empty command", None

        cmd = parts[0].lower()

        if cmd == const.CMD_MOVE:
            return self.handle_move(parts[1:]), None
        elif cmd == const.CMD_ADDMON:
            return self.handle_addmon(parts[1:])
        elif cmd == const.CMD_ATTACK:
            return self.handle_attack(parts[1:])
        elif cmd == const.CMD_GET_WEAPONS:
            return self.handle_get_weapons(), None
        elif cmd == const.CMD_SAYALL:
            return self.handle_sayall(parts[1:])
        elif cmd == const.CMD_MOVEMONSTERS:
            return self.handle_movemonsters(parts[1:])
        elif cmd == const.CMD_LOCALE:
            return f"{const.RESP_ERROR}: Locale command cannot be processed here", None
        else:
            return f"{const.RESP_ERROR}: Unknown command {cmd}", None

    def handle_movemonsters(self, args):
        """
        Обработать команду включения/выключения режима бродячих монстров.
        """
        global moving_monsters_enabled

        if not args or len(args) != 1:
            return f"{const.RESP_ERROR}: Invalid parameters. Use 'on' or 'off'", None

        mode = args[0].lower()
        if mode == "on":
            moving_monsters_enabled = True
            return "Moving monsters: on", f"{const.RESP_BROADCAST}: User '{self.username}' turned monster movement ON"
        elif mode == "off":
            moving_monsters_enabled = False
            return "Moving monsters: off", f"{const.RESP_BROADCAST}: User '{self.username}' turned monster movement OFF"
        else:
            return f"{const.RESP_ERROR}: Invalid parameter. Use 'on' or 'off'", None

    def handle_sayall(self, args):
        """
        Обработать команду отправки сообщения всем игрокам.

        Args:
            args: Аргументы команды sayall.

        Returns:
            tuple: Пара (ответ клиенту, широковещательное сообщение).
        """
        if not args:
            return f"{const.RESP_ERROR}: Empty message", None

        message = args[0] if len(args) == 1 else " ".join(args)
        broadcast_msg = f"{const.RESP_BROADCAST}: {self.username}: {message}"

        # Отправляем подтверждение отправителю
        return f"{const.RESP_SAYALL}: Message sent", broadcast_msg

    def handle_move(self, args):
        """
        Обработать команду перемещения игрока.

        Перемещает игрока на указанное смещение и проверяет, есть ли на новой
        позиции монстры для инициирования "энкаунтера".

        Args:
            args: Аргументы команды move.

        Returns:
            str: Ответ клиенту.
        """
        if len(args) != 2:
            return f"{const.RESP_ERROR}: Invalid move parameters"

        try:
            dx = int(args[0])
            dy = int(args[1])
        except ValueError:
            return f"{const.RESP_ERROR}: Invalid move parameters"

        self.player_x = (self.player_x + dx) % self.grid_size
        self.player_y = (self.player_y + dy) % self.grid_size

        response = f"{const.RESP_MOVED}: {self.player_x} {self.player_y}"

        position = (self.player_x, self.player_y)
        if position in global_monsters:
            monster_name, monster_hello, monster_hp = global_monsters[position]
            response += f"\n{const.RESP_ENCOUNTER}: {monster_name} {monster_hello}"

        return response

    def handle_addmon(self, args):
        """
        Обработать команду добавления монстра.
        """
        if len(args) != 5:
            return f"{const.RESP_ERROR}: Invalid addmon parameters", None

        try:
            monster_name = args[0]
            x = int(args[1])
            y = int(args[2])
            hello_string = args[3]
            hitpoints = int(args[4])

            if hitpoints <= 0:
                return f"{const.RESP_ERROR}: hitpoints must be positive", None

            if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
                return f"{const.RESP_ERROR}: Invalid coordinates", None

            position = (x, y)
            replaced = position in global_monsters
            global_monsters[position] = (monster_name, hello_string, hitpoints)

            result = f"{const.RESP_ADDED}: {monster_name} {x} {y} {hello_string}"

            # Сообщение для локализации
            broadcast_msg = (
                f"{const.RESP_BROADCAST}: User '{self.username}' added monster "
                f"'{monster_name}' with {hitpoints} HP at ({x}, {y})"
            )

            if replaced:
                result += " (replaced old monster)"

            return result, broadcast_msg
        except ValueError:
            return f"{const.RESP_ERROR}: Invalid addmon parameters", None

    def handle_attack(self, args):
        """
        Обработать команду атаки монстра.
        """
        if len(args) != 2:
            return f"{const.RESP_ERROR}: Invalid attack parameters", None

        try:
            monster_name = args[0]
            damage = int(args[1])

            position = (self.player_x, self.player_y)
            if position not in global_monsters:
                return f"{const.RESP_ERROR}: No monster here", None

            current_monster_name, monster_hello, monster_hp = global_monsters[position]

            if monster_name != current_monster_name:
                return f"{const.RESP_ERROR}: No {monster_name} here", None

            actual_damage = min(damage, monster_hp)
            monster_hp -= actual_damage

            weapon_name = "unknown weapon"
            for w_name, w_damage in self.weapons.items():
                if w_damage == damage:
                    weapon_name = w_name
                    break

            # Сообщения для локализации с поддержкой множественного числа для HP
            if monster_hp <= 0:
                del global_monsters[position]
                broadcast_msg = (
                    f"{const.RESP_BROADCAST}: User '{self.username}' attacked "
                    f"'{current_monster_name}' with {weapon_name}, dealing {actual_damage} HP. "
                    f"{current_monster_name} was killed!"
                )
                result = (
                    f"{const.RESP_ATTACK}: {current_monster_name} {actual_damage} 0 "
                    f"{const.RESP_KILLED}"
                )
            else:
                global_monsters[position] = (
                    current_monster_name, monster_hello, monster_hp
                )
                broadcast_msg = (
                    f"{const.RESP_BROADCAST}: User '{self.username}' attacked "
                    f"'{current_monster_name}' with {weapon_name}, dealing {actual_damage} HP. "
                    f"{current_monster_name} has {monster_hp} HP left."
                )
                result = f"{const.RESP_ATTACK}: {current_monster_name} {actual_damage} {monster_hp}"

            return result, broadcast_msg
        except ValueError:
            return f"{const.RESP_ERROR}: Invalid attack parameters", None

    def handle_get_weapons(self):
        """
        Получить список доступных оружий и их урон.

        Returns:
            str: Строка со списком оружия и урона.
        """
        weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in self.weapons.items())
        return f"{const.RESP_WEAPONS}: {weapons_list}"


async def handle_client(reader, writer):
    """
    Обработать соединение с клиентом.
    """
    client_addr = "{}:{}".format(*writer.get_extra_info('peername'))
    print(f"Connection attempt: {client_addr}")
    username = None

    try:
        # Установка локали по умолчанию для нового клиента
        client_locales[writer] = 'en'
        data = await reader.readline()
        if not data:
            writer.close()
            return

        message = data.decode().strip()
        parts = shlex.split(message)

        if len(parts) < 2 or parts[0].lower() != const.CMD_LOGIN:
            writer.write(
                f"{const.RESP_ERROR}: Invalid login format. "
                f"Use '{const.CMD_LOGIN} username'\n".encode()
            )
            await writer.drain()
            writer.close()
            return

        username = parts[1]

        if username in usernames:
            writer.write(
                f"{const.RESP_ERROR}: Username '{username}' is already taken\n".encode()
            )
            await writer.drain()
            writer.close()
            return

        usernames.add(username)
        clients[writer] = username
        games[username] = MUDGame(username)

        writer.write(f"Welcome, {username}! You are now connected to the MUD.\n".encode())
        await writer.drain()

        weapons_list = " ".join(
            f"{weapon} {damage}" for weapon, damage in games[username].weapons.items()
        )
        writer.write(f"{const.RESP_WEAPONS}: {weapons_list}\n".encode())
        await writer.drain()

        await broadcast_message(
            f"{const.RESP_BROADCAST}: User '{username}' has joined the MUD.",
            exclude_writer=writer
        )

        print(f"User '{username}' connected from {client_addr}")

        # Обработка команд клиента
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            print(f"Received from {username}: {message}")

            if message.lower() == const.CMD_QUIT or message.lower() == const.CMD_EXIT:
                break
            elif message.lower() == const.CMD_GET_WEAPONS:
                print(f"Sending weapons to {username}")
                weapons_list = " ".join(
                    f"{weapon} {damage}" for weapon, damage in games[username].weapons.items()
                )
                writer.write(f"{const.RESP_WEAPONS}: {weapons_list}\n".encode())
                await writer.drain()
            elif message.lower().startswith(const.CMD_LOCALE):
                # Обработка команды locale
                parts = message.split(" ", 1)
                if len(parts) == 2:
                    locale_name = parts[1].strip()
                    # Проверяем, поддерживается ли локаль
                    if locale_name in translations:
                        client_locales[writer] = locale_name
                        # Переводим сообщение ответа с учетом локали
                        translator = get_translator(locale_name)
                        response = translator.gettext("Set up locale: {}").format(locale_name)
                        writer.write(f"{response}\n".encode())
                    else:
                        writer.write(f"Unsupported locale: {locale_name}\n".encode())
                    await writer.drain()
                else:
                    writer.write("Invalid locale format\n".encode())
                    await writer.drain()
            else:
                response, broadcast_msg = games[username].handle_command(message)
                # Переводим ответ с учетом локали клиента
                locale = client_locales.get(writer, 'en')
                translator = get_translator(locale)
                translated_response = translator.gettext(response)

                writer.write(f"{translated_response}\n".encode())
                await writer.drain()

                if broadcast_msg:
                    await broadcast_message(broadcast_msg, exclude_writer=writer)

    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")
    finally:
        if username and username in usernames:
            print(f"User '{username}' disconnected")

            await broadcast_message(
                f"{const.RESP_BROADCAST}: User '{username}' has left the MUD.",
                exclude_writer=writer
            )

            usernames.remove(username)
            if username in games:
                del games[username]

        if writer in clients:
            del clients[writer]

        writer.close()
        await writer.wait_closed()


async def start_server(host=const.DEFAULT_HOST, port=const.DEFAULT_PORT):
    """
    Запустить сервер MOOD.

    Создает и запускает сервер на указанном хосте и порту.

    Args:
        host: Хост для прослушивания.
        port: Порт для прослушивания.

    Returns:
        asyncio.Server: Объект сервера.
    """
    server = await asyncio.start_server(handle_client, host, port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'MOOD Server started on {addrs}')

    return server


async def run_server(host=const.DEFAULT_HOST, port=const.DEFAULT_PORT):
    """
    Запустить сервер и держать его работающим.

    Запускает сервер и задачу перемещения монстров и ожидает их выполнения.

    Args:
        host: Хост для прослушивания.
        port: Порт для прослушивания.
    """
    server = await start_server(host, port)

    # Запускаем задачу для перемещения монстров
    monster_mover = asyncio.create_task(move_monsters())

    try:
        async with server:
            await server.serve_forever()
    finally:
        monster_mover.cancel()
        try:
            await monster_mover
        except asyncio.CancelledError:
            pass
