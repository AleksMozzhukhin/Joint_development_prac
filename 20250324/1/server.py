import asyncio
import shlex


class MUDGame:
    def __init__(self):
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}
        self.weapons = {
            "sword": 10,
            "spear": 15,
            "axe": 20
        }

    def handle_command(self, command):
        """Обрабатывает команды от клиента и возвращает ответ"""
        parts = shlex.split(command)
        if not parts:
            return "ERROR: Empty command"

        cmd = parts[0].lower()

        if cmd == "move":
            return self.handle_move(parts[1:])
        elif cmd == "addmon":
            return self.handle_addmon(parts[1:])
        elif cmd == "attack":
            return self.handle_attack(parts[1:])
        elif cmd == "get_weapons":
            return self.handle_get_weapons()
        else:
            return f"ERROR: Unknown command {cmd}"

    def handle_move(self, args):
        """Обрабатывает команду перемещения игрока"""
        if len(args) != 2:
            return "ERROR: Invalid move parameters"

        try:
            dx = int(args[0])
            dy = int(args[1])
        except ValueError:
            return "ERROR: Invalid move parameters"

        self.player_x = (self.player_x + dx) % self.grid_size
        self.player_y = (self.player_y + dy) % self.grid_size

        response = f"MOVED: {self.player_x} {self.player_y}"

        # Проверяем, есть ли в этой позиции монстр
        if (self.player_x, self.player_y) in self.monsters:
            monster_name, monster_hello, monster_hp = self.monsters[(self.player_x, self.player_y)]
            response += f"\nENCOUNTER: {monster_name} {monster_hello}"

        return response

    def handle_addmon(self, args):
        """Обрабатывает команду добавления монстра"""
        if len(args) != 5:
            return "ERROR: Invalid addmon parameters"

        try:
            monster_name = args[0]
            x = int(args[1])
            y = int(args[2])
            hello_string = args[3]
            hitpoints = int(args[4])

            if hitpoints <= 0:
                return "ERROR: hitpoints must be positive"

            if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
                return "ERROR: Invalid coordinates"

            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (monster_name, hello_string, hitpoints)

            if replaced:
                return f"ADDED: {monster_name} {x} {y} {hello_string} (replaced old monster)"
            else:
                return f"ADDED: {monster_name} {x} {y} {hello_string}"

        except ValueError:
            return "ERROR: Invalid addmon parameters"

    def handle_attack(self, args):
        """Обрабатывает команду атаки монстра"""
        if len(args) != 2:
            return "ERROR: Invalid attack parameters"

        monster_name = args[0]
        damage = int(args[1])

        if (self.player_x, self.player_y) not in self.monsters:
            return "ERROR: No monster here"

        current_monster_name, monster_hello, monster_hp = self.monsters[(self.player_x, self.player_y)]

        if monster_name != current_monster_name:
            return f"ERROR: No {monster_name} here"

        actual_damage = min(damage, monster_hp)
        monster_hp -= actual_damage

        if monster_hp == 0:
            del self.monsters[(self.player_x, self.player_y)]
            return f"ATTACK: {current_monster_name} {actual_damage} 0 KILLED"
        else:
            self.monsters[(self.player_x, self.player_y)] = (current_monster_name, monster_hello, monster_hp)
            return f"ATTACK: {current_monster_name} {actual_damage} {monster_hp}"

    def handle_get_weapons(self):
        """Возвращает список доступных оружий и их урон"""
        weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in self.weapons.items())
        return f"WEAPONS: {weapons_list}"


# Глобальные игровые экземпляры для разных клиентов
games = {}
clients = {}  # соответствие writer -> username
usernames = set()


async def handle_client(reader, writer):
    client_addr = "{}:{}".format(*writer.get_extra_info('peername'))
    print(f"Connection attempt: {client_addr}")
    username = None

    try:
        # Получаем имя пользователя
        data = await reader.readline()
        if not data:
            writer.close()
            return

        message = data.decode().strip()
        parts = shlex.split(message)

        if len(parts) < 2 or parts[0].lower() != "login":
            writer.write("ERROR: Invalid login format. Use 'login username'\n".encode())
            await writer.drain()
            writer.close()
            return

        username = parts[1]

        # Проверка уникальности имени
        if username in usernames:
            writer.write(f"ERROR: Username '{username}' is already taken\n".encode())
            await writer.drain()
            writer.close()
            return

        # Сохраняем информацию о клиенте
        usernames.add(username)
        clients[writer] = username
        games[username] = MUDGame()  # Создаем экземпляр игры для пользователя

        writer.write(f"Welcome, {username}! You are now connected to the MUD.\n".encode())
        await writer.drain()

        print(f"User '{username}' connected from {client_addr}")

        # Обработка остальных команд от клиента
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            print(f"Received from {username}: {message}")

            if message.lower() == "quit" or message.lower() == "exit":
                break

            response = games[username].handle_command(message)
            writer.write(f"{response}\n".encode())
            await writer.drain()

    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")
    finally:
        if username and username in usernames:
            print(f"User '{username}' disconnected")
            usernames.remove(username)
            if username in games:
                del games[username]

        if writer in clients:
            del clients[writer]

        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_client, '0.0.0.0', 65432)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'MUD Server started on {addrs}')

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())