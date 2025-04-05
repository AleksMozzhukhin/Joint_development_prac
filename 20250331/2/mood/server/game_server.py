"""Модуль серверной части игры MOOD."""

import asyncio
import shlex
from ..common import constants as const

games = {}  # экземпляры игр для разных пользователей
clients = {}  # соответствие writer -> username
usernames = set()
global_monsters = {}


async def broadcast_message(message, exclude_writer=None):
    """Отправить сообщение всем подключенным клиентам, кроме исключенного.

    Args:
        message: Сообщение для отправки.
        exclude_writer: Клиент, которому не нужно отправлять сообщение.
    """
    to_remove = []

    for writer, username in clients.items():
        if writer != exclude_writer:
            try:
                writer.write(f"{message}\n".encode())
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
            del clients[writer]


class MUDGame:
    """Класс для управления игровым процессом конкретного игрока."""

    def __init__(self, username=None):
        """Инициализировать игру для пользователя.

        Args:
            username: Имя игрока.
        """
        self.grid_size = const.GRID_SIZE
        self.player_x = 0
        self.player_y = 0
        self.weapons = dict(const.DEFAULT_WEAPONS)
        self.username = username  # Сохраняем имя пользователя

    def handle_command(self, command):
        """Обработать команду от клиента.

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
        else:
            return f"{const.RESP_ERROR}: Unknown command {cmd}", None

    def handle_sayall(self, args):
        """Обработать команду отправки сообщения всем игрокам.

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
        """Обработать команду перемещения игрока.

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
        """Обработать команду добавления монстра.

        Args:
            args: Аргументы команды addmon.

        Returns:
            tuple: Пара (ответ клиенту, широковещательное сообщение).
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
        """Обработать команду атаки монстра.

        Args:
            args: Аргументы команды attack.

        Returns:
            tuple: Пара (ответ клиенту, широковещательное сообщение).
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

            broadcast_msg = (
                f"{const.RESP_BROADCAST}: User '{self.username}' attacked "
                f"'{current_monster_name}' with {weapon_name}, dealing {actual_damage} damage."
            )

            if monster_hp <= 0:
                del global_monsters[position]
                broadcast_msg += f" {current_monster_name} was killed!"
                result = (
                    f"{const.RESP_ATTACK}: {current_monster_name} {actual_damage} 0 "
                    f"{const.RESP_KILLED}"
                )
            else:
                global_monsters[position] = (
                    current_monster_name, monster_hello, monster_hp
                )
                broadcast_msg += f" {current_monster_name} has {monster_hp} HP left."
                result = f"{const.RESP_ATTACK}: {current_monster_name} {actual_damage} {monster_hp}"

            return result, broadcast_msg
        except ValueError:
            return f"{const.RESP_ERROR}: Invalid attack parameters", None

    def handle_get_weapons(self):
        """Получить список доступных оружий и их урон.

        Returns:
            str: Строка со списком оружия и урона.
        """
        weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in self.weapons.items())
        return f"{const.RESP_WEAPONS}: {weapons_list}"


async def handle_client(reader, writer):
    """Обработать соединение с клиентом.

    Args:
        reader: Объект для чтения данных от клиента.
        writer: Объект для отправки данных клиенту.
    """
    client_addr = "{}:{}".format(*writer.get_extra_info('peername'))
    print(f"Connection attempt: {client_addr}")
    username = None

    try:
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
            else:
                response, broadcast_msg = games[username].handle_command(message)

                writer.write(f"{response}\n".encode())
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
    """Запустить сервер MOOD.

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
    """Запустить сервер и держать его работающим.

    Args:
        host: Хост для прослушивания.
        port: Порт для прослушивания.
    """
    server = await start_server(host, port)

    async with server:
        await server.serve_forever()
