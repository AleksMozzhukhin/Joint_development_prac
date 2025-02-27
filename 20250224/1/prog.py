import sys
import cowsay

class MUD:
    def __init__(self):
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}

    def process_command(self, command):
        if not command:
            return

        parts = command.strip().split()
        cmd = parts[0].lower()

        if cmd in ["up", "down", "left", "right"]:
            self.move_player(cmd)
        elif cmd == "addmon":
            if len(parts) < 4:
                print("Invalid arguments")
                return

            try:
                x = int(parts[1])
                y = int(parts[2])
                hello = parts[3]
                self.add_monster(x, y, hello)
            except ValueError:
                print("Invalid arguments")
        else:
            print("Invalid command")

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

        # Check if there's a monster at the new position
        if (self.player_x, self.player_y) in self.monsters:
            self.encounter(self.player_x, self.player_y)

    def add_monster(self, x, y, hello):
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            print("Invalid arguments")
            return

        if (x, y) in self.monsters:
            print(f"Added monster to ({x}, {y}) saying {hello}")
            print("Replaced the old monster")
        else:
            print(f"Added monster to ({x}, {y}) saying {hello}")

        self.monsters[(x, y)] = hello

    def encounter(self, x, y):
        if (x, y) in self.monsters:
            monster_hello = self.monsters[(x, y)]
            print(cowsay.cowsay(monster_hello))

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