"""Модуль клиентской части игры MOOD."""

import cmd
import shlex
import socket
import cowsay
import sys
import readline
import threading
import time
import os
from ..common import constants as const


class MUDClient(cmd.Cmd):
    """Класс клиента для игры MOOD."""

    prompt = "> "
    intro = "<<< Welcome to MOOD (MUD with cowsay) Client 0.2.0 >>>"

    def __init__(self, host=const.DEFAULT_HOST, port=const.DEFAULT_PORT, username=None, command_file=None):
        """
        Инициализировать клиента.

        Args:
            host: Адрес сервера.
            port: Порт сервера.
            username: Имя пользователя.
            command_file: Путь к файлу с командами для выполнения.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.weapons = {}
        self.username = username or "Unknown"
        self.running = True
        self.command_file = command_file
        self.executing_file = False

        self.connect()

        self.receiver_thread = threading.Thread(target=self.receive_messages)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

        # Если указан файл команд, выводим информацию о нем
        if self.command_file:
            print(f"Command file specified: {self.command_file}")
            # Проверяем существование файла
            if os.path.exists(self.command_file):
                print(f"Command file exists: {self.command_file}")
            else:
                print(f"WARNING: Command file not found: {self.command_file}")

    def connect(self):
        """Подключиться к серверу."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            self.socket.sendall(f"{const.CMD_LOGIN} {self.username}\n".encode())
            response = self.socket.recv(1024).decode().strip()

            if response.startswith(f"{const.RESP_ERROR}:"):
                print(response)
                self.socket.close()
                sys.exit(1)
            else:
                print(f"Logged in as {self.username}")

            self.send_command(const.CMD_GET_WEAPONS)
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)

    def receive_messages(self):
        """Асинхронно получать сообщения от сервера."""
        try:
            while self.running and self.socket:
                data = self.socket.recv(1024)
                if not data:
                    break

                message = data.decode().strip()

                if f"{const.RESP_WEAPONS}:" in message:
                    parts = message.split(f"{const.RESP_WEAPONS}: ")[1].split()
                    i = 0
                    while i < len(parts):
                        if i + 1 < len(parts):
                            self.weapons[parts[i]] = int(parts[i + 1])
                        i += 2
                    continue

                if f"{const.RESP_ENCOUNTER}:" in message:
                    parts = message.split(f"{const.RESP_ENCOUNTER}: ")
                    if len(parts) > 1:
                        encounter_parts = parts[1].split(" ", 1)
                        if len(encounter_parts) == 2:
                            monster_name = encounter_parts[0]
                            monster_message = encounter_parts[1].strip("'")

                            self.display_monster(monster_name, monster_message)
                            continue

                print(f"\n{message}\n{self.prompt}{readline.get_line_buffer()}", end="", flush=True)

        except Exception as e:
            print(f"\nError receiving messages: {e}\n{self.prompt}", end="", flush=True)
        finally:
            if self.running:
                print("\nConnection closed. Press Enter to exit.")
                self.running = False

    def get_weapons(self):
        """Получить список оружия от сервера."""
        response = self.send_command(const.CMD_GET_WEAPONS)
        parts = response.split(" ")
        if parts[0] == f"{const.RESP_WEAPONS}:":
            i = 1
            while i < len(parts):
                if i + 1 < len(parts):
                    self.weapons[parts[i]] = int(parts[i + 1])
                i += 2

    def send_command(self, command):
        """
        Отправить команду на сервер и получить ответ.

        Args:
            command: Команда для отправки.

        Returns:
            str: Ответ от сервера.
        """
        try:
            self.socket.sendall(f"{command}\n".encode())
            raw_response = self.socket.recv(1024)
            if raw_response is None:
                return f"{const.RESP_ERROR}: Connection failed (recv returned None)"
            response = raw_response.decode().strip()
            return response
        except Exception as e:
            print(f"Error communicating with server: Exception type={type(e)}, Message='{e}'")
            return f"{const.RESP_ERROR}: Connection failed"

    def do_movemonsters(self, arg):
        """
        Включить или выключить режим бродячих монстров.

        Args:
            arg: "on" для включения или "off" для выключения.
        """
        args = arg.strip().lower()
        if not args or args not in ["on", "off"]:
            print("Usage: movemonsters on|off")
            return

        response = self.send_command(f"{const.CMD_MOVEMONSTERS} {args}")
        print(response)

    def complete_movemonsters(self, text, line, begidx, endidx):
        """
        Автодополнение для команды movemonsters.

        Args:
            text: Текст для дополнения.
            line: Полная строка.
            begidx: Начальный индекс.
            endidx: Конечный индекс.

        Returns:
            list: Список вариантов автодополнения.
        """
        options = ["on", "off"]
        return [option for option in options if option.startswith(text.lower())]
    def do_up(self, arg):
        """
        Переместить игрока вверх на одну позицию.

        Args:
            arg: Аргументы команды (не используются).
        """
        response = self.send_command(f"{const.CMD_MOVE} 0 -1")
        self.handle_server_response(response)

    def do_down(self, arg):
        """
        Переместить игрока вниз на одну позицию.

        Args:
            arg: Аргументы команды (не используются).
        """
        response = self.send_command(f"{const.CMD_MOVE} 0 1")
        self.handle_server_response(response)

    def do_left(self, arg):
        """
        Переместить игрока влево на одну позицию.

        Args:
            arg: Аргументы команды (не используются).
        """
        response = self.send_command(f"{const.CMD_MOVE} -1 0")
        self.handle_server_response(response)

    def do_right(self, arg):
        """
        Переместить игрока вправо на одну позицию.

        Args:
            arg: Аргументы команды (не используются).
        """
        response = self.send_command(f"{const.CMD_MOVE} 1 0")
        self.handle_server_response(response)

    def do_sayall(self, arg):
        """
        Отправить сообщение всем игрокам.

        Args:
            arg: Текст сообщения.
        """
        if not arg:
            print("Message cannot be empty")
            return

        response = self.send_command(f"{const.CMD_SAYALL} {arg}")
        self.handle_server_response(response)

    def do_addmon(self, arg):
        """
        Добавить монстра на карту.

        Args:
            arg: Аргументы в формате: name coords x y hp health hello "message".
        """
        try:
            parts = shlex.split(arg)
            self.process_addmon(parts)
        except ValueError:
            print("Invalid command syntax")

    def process_addmon(self, args):
        """
        Обработать аргументы команды addmon.

        Args:
            args: Список аргументов.
        """
        if len(args) < 7:
            print("Invalid arguments")
            return

        try:
            monster_name = args[0]

            hello_string = None
            hitpoints = None
            x = None
            y = None

            i = 1
            while i < len(args):
                param_name = args[i].lower()

                if param_name == "hello" and i + 1 < len(args):
                    hello_string = args[i + 1]
                    i += 2
                elif param_name == "hp" and i + 1 < len(args):
                    hitpoints = int(args[i + 1])
                    if hitpoints <= 0:
                        print("Invalid arguments: hitpoints must be positive")
                        return
                    i += 2
                elif param_name == "coords" and i + 2 < len(args):
                    x = int(args[i + 1])
                    y = int(args[i + 2])
                    i += 3
                else:
                    print("Invalid arguments")
                    return

            if hello_string is None or hitpoints is None or x is None or y is None:
                print("Invalid arguments: missing required parameters")
                return

            # Отправляем команду на сервер в упрощенном формате
            command = f'{const.CMD_ADDMON} {monster_name} {x} {y} "{hello_string}" {hitpoints}'
            response = self.send_command(command)
            self.handle_server_response(response)

        except ValueError:
            print("Invalid arguments")
            return
        except IndexError:
            print("Invalid arguments")
            return

    def do_attack(self, arg):
        """
        Атаковать монстра.

        Args:
            arg: Аргументы в формате: <monster_name> with <weapon>.
        """
        args = shlex.split(arg) if arg else []
        weapon = "sword"  # Оружие по умолчанию
        monster_name = None

        i = 0
        while i < len(args):
            if args[i].lower() == "with" and i + 1 < len(args):
                weapon = args[i + 1].lower()
                i += 2
            else:
                monster_name = args[i]
                i += 1

        if not monster_name:
            print("Monster name not specified")
            return

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        # Отправляем команду на сервер
        damage = self.weapons[weapon]
        response = self.send_command(f"{const.CMD_ATTACK} {monster_name} {damage}")
        self.handle_server_response(response)

    def complete_attack(self, text, line, begidx, endidx):
        """
        Автодополнение для команды attack.

        Args:
            text: Текст для дополнения.
            line: Полная строка.
            begidx: Начальный индекс.
            endidx: Конечный индекс.

        Returns:
            list: Список вариантов автодополнения.
        """
        args = shlex.split(line[:begidx]) if line[:begidx].strip() else []

        available_monsters = cowsay.list_cows()
        if "jgsbat" not in available_monsters:
            available_monsters.append("jgsbat")

        if len(args) <= 1:
            if not text or "with".startswith(text):
                return ["with"] + [monster for monster in available_monsters if monster.startswith(text)]
            return [monster for monster in available_monsters if monster.startswith(text)]

        if len(args) == 2 and args[1] == "with":
            return [weapon for weapon in self.weapons if weapon.startswith(text)]

        if len(args) == 2 and args[1] in available_monsters:
            return ["with"] if not text or "with".startswith(text) else []

        if len(args) >= 3 and args[1] in available_monsters and args[2] == "with":
            return [weapon for weapon in self.weapons if weapon.startswith(text)]

        return []

    def handle_server_response(self, response):
        """
        Обработать ответ от сервера.

        Args:
            response: Строка ответа от сервера.
        """
        lines = response.strip().split("\n")

        for line in lines:
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue

            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if cmd == f"{const.RESP_MOVED}:":
                coords = args.split()
                if len(coords) == 2:
                    print(f"Moved to ({coords[0]}, {coords[1]})")
            elif cmd == f"{const.RESP_ENCOUNTER}:":
                enc_parts = args.split(" ", 1)
                if len(enc_parts) == 2:
                    monster_name = enc_parts[0]
                    message = enc_parts[1]
                    self.display_monster(monster_name, message)
            elif cmd == f"{const.RESP_ADDED}:":
                print(args)
            elif cmd == f"{const.RESP_ATTACK}:":
                attack_parts = args.split()
                if len(attack_parts) >= 3:
                    monster_name = attack_parts[0]
                    damage = attack_parts[1]
                    hp_left = attack_parts[2]

                    print(f"Attacked {monster_name}, damage {damage} hp")

                    if const.RESP_KILLED in args:
                        print(f"{monster_name} died")
                    else:
                        print(f"{monster_name} now has {hp_left}")
            elif cmd == f"{const.RESP_ERROR}:":
                print(args)
            elif cmd == f"{const.RESP_SAYALL}:":
                print(args)

    def display_monster(self, monster_name, message):
        """
        Отобразить монстра с использованием cowsay.

        Args:
            monster_name: Имя монстра.
            message: Сообщение от монстра.
        """
        if monster_name == "jgsbat":
            try:
                with open("jgsbat.cow", "r") as f:
                    cow = cowsay.read_dot_cow(f)
                print(cowsay.cowsay(message, cow=cow))
            except FileNotFoundError:
                print(f"Monster {monster_name} says: {message}")
        else:
            try:
                print(cowsay.cowsay(message, cow=monster_name))
            except Exception:
                print(f"Monster {monster_name} says: {message}")

    def do_quit(self, arg):
        """
        Выйти из игры.

        Args:
            arg: Аргументы команды (не используются).

        Returns:
            bool: True для выхода из цикла cmd.
        """
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        return True

    def do_exit(self, arg):
        """
        Выйти из игры (синоним для quit).

        Args:
            arg: Аргументы команды (не используются).

        Returns:
            bool: True для выхода из цикла cmd.
        """
        return self.do_quit(arg)

    def do_locale(self, arg):
        """
        Установить локаль для клиента.

        Args:
            arg: Имя локали (например, "ru_RU.UTF8").
        """
        if not arg:
            print("Usage: locale <locale_name>")
            return

        locale_name = arg.strip()
        response = self.send_command(f"{const.CMD_LOCALE} {locale_name}")
        print(response)

    def complete_locale(self, text, line, begidx, endidx):
        """
        Автодополнение для команды locale.

        Args:
            text: Текст для дополнения.
            line: Полная строка.
            begidx: Начальный индекс.
            endidx: Конечный индекс.

        Returns:
            list: Список вариантов автодополнения.
        """
        locales = ["en", "ru_RU.UTF8"]
        return [locale for locale in locales if locale.startswith(text)]

    def execute_commands_from_file(self):
        """
        Выполнить команды из файла.

        Читает команды из указанного файла и выполняет их последовательно
        с задержкой не менее 1 секунды между командами.
        """
        try:
            print(f"Starting execution of commands from file: {self.command_file}")
            self.executing_file = True

            with open(self.command_file, 'r') as f:
                commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

            print(f"Loaded {len(commands)} commands from file")

            for i, command in enumerate(commands):
                if not self.running:
                    print("Execution stopped: client is no longer running")
                    break

                print(f"Executing command {i+1}/{len(commands)}: {command}")

                # Разбираем команду как в onecmd
                line = command.strip()
                if not line:
                    continue

                # Проверяем на выход
                if line == 'quit' or line == 'exit':
                    print("Exit command detected, stopping execution")
                    self.do_quit('')
                    break

                # Разбираем команду на имя и аргументы
                cmd, arg, line = self.parseline(line)
                if not cmd:
                    print(f"Invalid command: {line}")
                    continue

                # Ищем метод-обработчик
                func = getattr(self, 'do_' + cmd, None)
                if not func:
                    print(f"Unknown command: {cmd}")
                    continue

                # Выполняем команду
                print(f"Executing: do_{cmd}({arg})")
                func(arg)

                # Задержка между командами не менее 1 секунды
                print(f"Waiting 1 second before next command...")
                time.sleep(1)

            print("Command file execution completed")

            # Завершаем работу клиента после выполнения всех команд
            print("Exiting client after command file execution")
            self.executing_file = False
            self.do_quit('')

        except FileNotFoundError:
            print(f"Error: File not found: {self.command_file}")
            self.executing_file = False
            self.do_quit('')
        except Exception as e:
            print(f"Error executing commands from file: {e}")
            self.executing_file = False
            self.do_quit('')

    def cmdloop(self, intro=None):
        """
        Запустить основной цикл обработки команд.

        Переопределяет метод cmdloop из cmd.Cmd для поддержки выполнения команд из файла.

        Args:
            intro: Вступительное сообщение.
        """
        print("Starting cmdloop")
        if self.command_file:
            print(f"Command file mode: {self.command_file}")
            # Запускаем выполнение команд из файла напрямую
            self.execute_commands_from_file()
            return
        else:
            print("Interactive mode")
            # Стандартный интерактивный режим
            return super().cmdloop(intro)


def start_client(host=const.DEFAULT_HOST, port=const.DEFAULT_PORT, username=None, command_file=None):
    """
    Запустить клиента MOOD.

    Args:
        host: Адрес сервера.
        port: Порт сервера.
        username: Имя пользователя.
        command_file: Путь к файлу с командами для выполнения.
    """
    if not username:
        print("Username required")
        sys.exit(1)

    # Проверяем расширение файла команд, если он указан
    if command_file and not command_file.endswith('.mood'):
        print("Warning: Command file should have .mood extension")

    print(f"Starting client with host={host}, port={port}, username={username}, command_file={command_file}")

    try:
        client = MUDClient(host, port, username, command_file)
        client.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting game...")