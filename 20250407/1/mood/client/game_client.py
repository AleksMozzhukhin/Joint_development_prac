"""Модуль клиентской части игры MOOD."""

import cmd
import shlex
import socket
import cowsay
import sys
import readline
import threading
from ..common import constants as const


class MUDClient(cmd.Cmd):
    """Класс клиента для игры MOOD."""

    prompt = "> "
    intro = "<<< Welcome to MOOD (MUD with cowsay) Client 0.2.0 >>>"

    def __init__(self, host=const.DEFAULT_HOST, port=const.DEFAULT_PORT, username=None):
        """
        Инициализировать клиента.

        Args:
            host: Адрес сервера.
            port: Порт сервера.
            username: Имя пользователя.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.weapons = {}
        self.username = username or "Unknown"
        self.running = True

        self.connect()

        self.receiver_thread = threading.Thread(target=self.receive_messages)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

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
            response = self.socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            print(f"Error communicating with server: {e}")
            return f"{const.RESP_ERROR}: Connection failed"

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


def start_client(host=const.DEFAULT_HOST, port=const.DEFAULT_PORT, username=None):
    """
    Запустить клиента MOOD.

    Args:
        host: Адрес сервера.
        port: Порт сервера.
        username: Имя пользователя.
    """
    if not username:
        print("Username required")
        sys.exit(1)

    try:
        client = MUDClient(host, port, username)
        client.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting game...")
