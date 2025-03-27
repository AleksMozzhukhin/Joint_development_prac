import asyncio
import shlex

games = {}  # экземпляры игр для разных пользователей
clients = {}  # соответствие writer -> username
usernames = set()
global_monsters = {}


async def broadcast_message(message, exclude_writer=None):
    """Отправляет сообщение всем подключенным клиентам, кроме исключенного"""
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
    def __init__(self, username=None):
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.weapons = {
            "sword": 10,
            "spear": 15,
            "axe": 20
        }
        self.username = username  # Сохраняем имя пользователя

    def handle_command(self, command):
        """Обрабатывает команды от клиента и возвращает (ответ, широковещательное сообщение)"""
        parts = shlex.split(command)
        if not parts:
            return "ERROR: Empty command", None

        cmd = parts[0].lower()

        if cmd == "move":
            return self.handle_move(parts[1:]), None
        elif cmd == "addmon":
            return self.handle_addmon(parts[1:])
        elif cmd == "attack":
            return self.handle_attack(parts[1:])
        elif cmd == "get_weapons":
            return self.handle_get_weapons(), None
        else:
            return f"ERROR: Unknown command {cmd}", None

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

        position = (self.player_x, self.player_y)
        if position in global_monsters:
            monster_name, monster_hello, monster_hp = global_monsters[position]
            response += f"\nENCOUNTER: {monster_name} {monster_hello}"

        return response

    def handle_addmon(self, args):
        """Обрабатывает команду добавления монстра"""
        if len(args) != 5:
            return "ERROR: Invalid addmon parameters", None

        try:
            monster_name = args[0]
            x = int(args[1])
            y = int(args[2])
            hello_string = args[3]
            hitpoints = int(args[4])

            if hitpoints <= 0:
                return "ERROR: hitpoints must be positive", None

            if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
                return "ERROR: Invalid coordinates", None

            position = (x, y)
            replaced = position in global_monsters
            global_monsters[position] = (monster_name, hello_string, hitpoints)

            result = f"ADDED: {monster_name} {x} {y} {hello_string}"

            broadcast_msg = f"BROADCAST: User '{self.username}' added monster '{monster_name}' with {hitpoints} HP at ({x}, {y})"

            if replaced:
                result += " (replaced old monster)"

            return result, broadcast_msg

        except ValueError:
            return "ERROR: Invalid addmon parameters", None

    def handle_attack(self, args):
        """Обрабатывает команду атаки монстра"""
        if len(args) != 2:
            return "ERROR: Invalid attack parameters", None

        try:
            monster_name = args[0]
            damage = int(args[1])

            position = (self.player_x, self.player_y)
            if position not in global_monsters:
                return "ERROR: No monster here", None

            current_monster_name, monster_hello, monster_hp = global_monsters[position]

            if monster_name != current_monster_name:
                return f"ERROR: No {monster_name} here", None

            actual_damage = min(damage, monster_hp)
            monster_hp -= actual_damage

            weapon_name = "unknown weapon"
            for w_name, w_damage in self.weapons.items():
                if w_damage == damage:
                    weapon_name = w_name
                    break

            broadcast_msg = f"BROADCAST: User '{self.username}' attacked '{current_monster_name}' with {weapon_name}, dealing {actual_damage} damage."

            if monster_hp <= 0:
                del global_monsters[position]
                broadcast_msg += f" {current_monster_name} was killed!"
                result = f"ATTACK: {current_monster_name} {actual_damage} 0 KILLED"
            else:
                global_monsters[position] = (current_monster_name, monster_hello, monster_hp)
                broadcast_msg += f" {current_monster_name} has {monster_hp} HP left."
                result = f"ATTACK: {current_monster_name} {actual_damage} {monster_hp}"

            return result, broadcast_msg
        except ValueError:
            return "ERROR: Invalid attack parameters", None

    def handle_get_weapons(self):
        """Возвращает список доступных оружий и их урон"""
        weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in self.weapons.items())
        return f"WEAPONS: {weapons_list}"


async def handle_client(reader, writer):
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

        if len(parts) < 2 or parts[0].lower() != "login":
            writer.write("ERROR: Invalid login format. Use 'login username'\n".encode())
            await writer.drain()
            writer.close()
            return

        username = parts[1]

        if username in usernames:
            writer.write(f"ERROR: Username '{username}' is already taken\n".encode())
            await writer.drain()
            writer.close()
            return

        usernames.add(username)
        clients[writer] = username
        games[username] = MUDGame(username)

        writer.write(f"Welcome, {username}! You are now connected to the MUD.\n".encode())
        await writer.drain()

        weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in games[username].weapons.items())
        writer.write(f"WEAPONS: {weapons_list}\n".encode())
        await writer.drain()

        await broadcast_message(f"BROADCAST: User '{username}' has joined the MUD.", exclude_writer=writer)

        print(f"User '{username}' connected from {client_addr}")

        # Обработка команд клиента
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            print(f"Received from {username}: {message}")

            if message.lower() == "quit" or message.lower() == "exit":
                break
            elif message.lower() == "get_weapons":
                print(f"Sending weapons to {username}")
                weapons_list = " ".join(f"{weapon} {damage}" for weapon, damage in games[username].weapons.items())
                writer.write(f"WEAPONS: {weapons_list}\n".encode())
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

            await broadcast_message(f"BROADCAST: User '{username}' has left the MUD.", exclude_writer=writer)

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