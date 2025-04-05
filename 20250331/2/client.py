import cmd
import shlex
import socket
import cowsay
import sys
import readline
import threading


class MUDClient(cmd.Cmd):
    prompt = "> "
    intro = "<<< Welcome to Python-MUD Client 0.1 >>>"

    def __init__(self, host='localhost', port=65432, username=None):
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
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            self.socket.sendall(f"login {self.username}\n".encode())
            response = self.socket.recv(1024).decode().strip()

            if response.startswith("ERROR:"):
                print(response)
                self.socket.close()
                sys.exit(1)
            else:
                print(f"Logged in as {self.username}")

            self.send_command("get_weapons")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)

    def receive_messages(self):
        """Асинхронное получение сообщений от сервера"""
        try:
            while self.running and self.socket:
                data = self.socket.recv(1024)
                if not data:
                    break

                message = data.decode().strip()

                if "WEAPONS:" in message:
                    parts = message.split("WEAPONS: ")[1].split()
                    i = 0
                    while i < len(parts):
                        if i + 1 < len(parts):
                            self.weapons[parts[i]] = int(parts[i + 1])
                        i += 2
                    continue

                if "ENCOUNTER:" in message:
                    parts = message.split("ENCOUNTER: ")
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
        """Получаем список оружия от сервера"""
        response = self.send_command("get_weapons")
        parts = response.split(" ")
        if parts[0] == "WEAPONS:":
            i = 1
            while i < len(parts):
                if i + 1 < len(parts):
                    self.weapons[parts[i]] = int(parts[i + 1])
                i += 2

    def send_command(self, command):
        """Отправка команды на сервер и получение ответа"""
        try:
            self.socket.sendall(f"{command}\n".encode())
            response = self.socket.recv(1024).decode().strip()
            return response
        except Exception as e:
            print(f"Error communicating with server: {e}")
            return "ERROR: Connection failed"

    def do_up(self, arg):
        """Move player up one position"""
        response = self.send_command("move 0 -1")
        self.handle_server_response(response)

    def do_down(self, arg):
        """Move player down one position"""
        response = self.send_command("move 0 1")
        self.handle_server_response(response)

    def do_left(self, arg):
        """Move player left one position"""
        response = self.send_command("move -1 0")
        self.handle_server_response(response)

    def do_right(self, arg):
        """Move player right one position"""
        response = self.send_command("move 1 0")
        self.handle_server_response(response)

    def do_sayall(self, arg):
        """Send a message to all players: sayall <message> or sayall "message with spaces" """
        if not arg:
            print("Message cannot be empty")
            return

        response = self.send_command(f"sayall {arg}")
        self.handle_server_response(response)

    def do_addmon(self, arg):
        """Add monster to the map: addmon name coords x y hp health hello "message" """
        try:
            parts = shlex.split(arg)
            self.process_addmon(parts)
        except ValueError:
            print("Invalid command syntax")

    def process_addmon(self, args):
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
            command = f'addmon {monster_name} {x} {y} "{hello_string}" {hitpoints}'
            response = self.send_command(command)
            self.handle_server_response(response)

        except ValueError:
            print("Invalid arguments")
            return
        except IndexError:
            print("Invalid arguments")
            return

    def do_attack(self, arg):
        """Attack a monster at the current position with weapon: attack <monster_name> with <weapon>"""
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
        response = self.send_command(f"attack {monster_name} {damage}")
        self.handle_server_response(response)

    def complete_attack(self, text, line, begidx, endidx):
        """Auto-complete для команды attack"""
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
        """Обрабатывает ответ от сервера и выводит информацию пользователю"""
        lines = response.strip().split("\n")

        for line in lines:
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue

            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "MOVED:":
                coords = args.split()
                if len(coords) == 2:
                    print(f"Moved to ({coords[0]}, {coords[1]})")
            elif cmd == "ENCOUNTER:":
                enc_parts = args.split(" ", 1)
                if len(enc_parts) == 2:
                    monster_name = enc_parts[0]
                    message = enc_parts[1]
                    self.display_monster(monster_name, message)
            elif cmd == "ADDED:":
                print(args)
            elif cmd == "ATTACK:":
                attack_parts = args.split()
                if len(attack_parts) >= 3:
                    monster_name = attack_parts[0]
                    damage = attack_parts[1]
                    hp_left = attack_parts[2]

                    print(f"Attacked {monster_name}, damage {damage} hp")

                    if "KILLED" in args:
                        print(f"{monster_name} died")
                    else:
                        print(f"{monster_name} now has {hp_left}")
            elif cmd == "ERROR:":
                print(args)
            elif cmd == "SAYALL:":
                print(args)

    def display_monster(self, monster_name, message):
        """Отображает монстра с использованием cowsay"""
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
        """Exit the game"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        return True

    def do_exit(self, arg):
        """Exit the game"""
        return self.do_quit(arg)


def main():
    host = 'localhost'
    port = 65432
    username = None

    # Проверяем аргументы командной строки для указания username и host:port
    if len(sys.argv) > 1:
        # Формат: python mymud.py username [host:port]
        username = sys.argv[1]
        if len(sys.argv) > 2:
            server_addr = sys.argv[2].split(':')
            host = server_addr[0]
            if len(server_addr) > 1:
                port = int(server_addr[1])

    if not username:
        print("Username required: python mymud.py username [host:port]")
        sys.exit(1)

    try:
        MUDClient(host, port, username).cmdloop()
    except KeyboardInterrupt:
        print("\nExiting game...")


if __name__ == "__main__":
    main()