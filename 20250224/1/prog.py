import sys


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

    def move_player(self, cmd):
        print(f'Done command: {cmd}')

    def add_monster(self, x, y, hello):
        print(f"Added monster to ({x}, {y}) saying {hello}")


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