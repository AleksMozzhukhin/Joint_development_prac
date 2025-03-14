import sys
import cowsay
import shlex


class MUD:
    def __init__(self):
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}

    def process_command(self, command):
        if not command:
            return

        try:
            parts = shlex.split(command.strip())
        except ValueError:
            print("Invalid command syntax")
            return

        if not parts:
            return

        cmd = parts[0].lower()

        if cmd in ["up", "down", "left", "right"]:
            self.move_player(cmd)
        elif cmd == "addmon":
            self.process_addmon(parts[1:])
        else:
            print("Invalid command")

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

            self.add_monster(monster_name, x, y, hello_string, hitpoints)

        except ValueError:
            print("Invalid arguments")
            return
        except IndexError:
            print("Invalid arguments")
            return

    def move_player(self, direction):
        if direction == "up":
            self.player_y = (self.player_y - 1) % self.grid_size
        elif direction == "down":
            self.player_y = (self.player_y + 1) % self.grid_size
        elif direction == "left":
            self.player_x = (self.player_x - 1) % self.grid_size
        elif direction == "right":
            self.player_x = (self.player_x + 1) % self.grid_size
        else:
            print("Invalid command")
            return

        print(f"Moved to ({self.player_x}, {self.player_y})")

        if (self.player_x, self.player_y) in self.monsters:
            self.encounter(self.player_x, self.player_y)

    def add_monster(self, name, x, y, hello, hitpoints):
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            print("Invalid arguments")
            return

        if name not in cowsay.list_cows() and name != "jgsbat":
            print("Cannot add unknown monster")
            return

        if (x, y) in self.monsters:
            print(f"Added monster {name} to ({x}, {y}) saying {hello}")
            print("Replaced the old monster")
        else:
            print(f"Added monster {name} to ({x}, {y}) saying {hello}")

        self.monsters[(x, y)] = (name, hello, hitpoints)

    def encounter(self, x, y):
        if (x, y) in self.monsters:
            monster_name, monster_hello, _ = self.monsters[(x, y)]
            if monster_name == "jgsbat":
                with open("jgsbat.cow", "r") as f:
                    cow = cowsay.read_dot_cow(f)
                print(cowsay.cowsay(monster_hello, cow=cow))
            else:
                print(cowsay.cowsay(monster_hello, cow=monster_name))

print("<<< Welcome to Python-MUD 0.1 >>>")
game = MUD()

if not sys.stdin.isatty():
    for line in sys.stdin:
        game.process_command(line)
else:
    while True:
        try:
            command = input("> ")
            game.process_command(command)
        except (KeyboardInterrupt, EOFError):
            break
