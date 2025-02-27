import sys


class MUD:
    def __init__(self):
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}

    def process_command(self, command):
        print(command)
        return


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