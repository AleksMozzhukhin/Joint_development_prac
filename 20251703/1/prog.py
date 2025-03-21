import sys
import cowsay
import shlex
import cmd


class MUD(cmd.Cmd):
    prompt = "> "
    intro = "<<< Welcome to Python-MUD 0.1 >>>"

    def __init__(self):
        super().__init__()
        self.grid_size = 10
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}
        self.weapons = {
            "sword": 10,
            "spear": 15,
            "axe": 20
        }

    def do_up(self, arg):
        """Move player up one position"""
        self.move_player("up")

    def do_down(self, arg):
        """Move player down one position"""
        self.move_player("down")

    def do_left(self, arg):
        """Move player left one position"""
        self.move_player("left")

    def do_right(self, arg):
        """Move player right one position"""
        self.move_player("right")

    def do_addmon(self, arg):
        """Add monster to the map: addmon name hp health coords x y hello "message" """
        try:
            parts = shlex.split(arg)
            self.process_addmon(parts)
        except ValueError:
            print("Invalid command syntax")

    def do_attack(self, arg):
        """Attack a monster at the current position with weapon: attack <monster_name> with <weapon>"""
        if (self.player_x, self.player_y) not in self.monsters:
            print("No monster here")
            return
        else:
            self.process_attack(arg)

    def process_attack(self, arg):
        args = shlex.split(arg) if arg else []
        weapon = "sword"
        monster_name_arg = None

        i = 0
        while i < len(args):
            if args[i].lower() == "with" and i + 1 < len(args):
                weapon = args[i + 1].lower()
                i += 2
            else:
                monster_name_arg = args[i]
                i += 1

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        current_monster_name, monster_hello, monster_hp = self.monsters[(self.player_x, self.player_y)]

        if monster_name_arg and monster_name_arg != current_monster_name:
            print(f"No {monster_name_arg} here")
            return

        damage = min(self.weapons[weapon], monster_hp)

        print(f"Attacked {current_monster_name}, damage {damage} hp")

        monster_hp -= damage

        if monster_hp == 0:
            print(f"{current_monster_name} died")
            del self.monsters[(self.player_x, self.player_y)]
        else:
            print(f"{current_monster_name} now has {monster_hp}")
            self.monsters[(self.player_x, self.player_y)] = (current_monster_name, monster_hello, monster_hp)

    def complete_attack(self, text, line, begidx, endidx):
        """Auto-complete для команды attack"""
        args = shlex.split(line[:begidx]) if line[:begidx].strip() else []

        available_monsters = cowsay.list_cows()
        if "jgsbat" not in available_monsters:
            available_monsters.append("jgsbat")

        if (self.player_x, self.player_y) in self.monsters:
            current_monster = self.monsters[(self.player_x, self.player_y)][0]
            if current_monster not in available_monsters:
                available_monsters.append(current_monster)

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

    def do_quit(self, arg):
        """Exit the game"""
        return True

    def do_exit(self, arg):
        """Exit the game"""
        return True


def main():
    MUD().cmdloop()


if __name__ == "__main__":
    main()
