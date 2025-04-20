"""Общие константы для клиента и сервера MOOD."""

# Сетевые настройки по умолчанию
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 65432

# Команды протокола
CMD_LOGIN = "login"
CMD_MOVE = "move"
CMD_ADDMON = "addmon"
CMD_ATTACK = "attack"
CMD_GET_WEAPONS = "get_weapons"
CMD_SAYALL = "sayall"
CMD_QUIT = "quit"
CMD_EXIT = "exit"

# Ответы сервера
RESP_MOVED = "MOVED"
RESP_ENCOUNTER = "ENCOUNTER"
RESP_ADDED = "ADDED"
RESP_ATTACK = "ATTACK"
RESP_ERROR = "ERROR"
RESP_WEAPONS = "WEAPONS"
RESP_BROADCAST = "BROADCAST"
RESP_SAYALL = "SAYALL"
RESP_KILLED = "KILLED"

# Другие константы
GRID_SIZE = 10
DEFAULT_WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe": 20
}
