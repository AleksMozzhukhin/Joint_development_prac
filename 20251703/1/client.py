import cmd
import shlex
import socket
import cowsay
import sys


class MUDClient(cmd.Cmd):
    prompt = "> "
    intro = "<<< Welcome to Python-MUD Client 0.1 >>>"

    def __init__(self, host='localhost', port=65432):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.weapons = {}

        # Подключаемся к серверу
        self.connect()


    def connect(self):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)


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

    # Проверяем аргументы командной строки для указания host:port
    if len(sys.argv) > 1:
        server_addr = sys.argv[1].split(':')
        host = server_addr[0]
        if len(server_addr) > 1:
            port = int(server_addr[1])

    try:
        MUDClient(host, port).cmdloop()
    except KeyboardInterrupt:
        print("\nExiting game...")


if __name__ == "__main__":
    main()