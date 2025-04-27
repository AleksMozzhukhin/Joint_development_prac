import unittest
from unittest.mock import patch, MagicMock, call
import sys
import io
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mood.client.game_client import MUDClient
from mood.common import constants as const

DUMMY_CMD_FILE = "dummy_commands.mood"


class TestClientCommandProcessing(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестовым методом."""
        if not os.path.exists(DUMMY_CMD_FILE):
            with open(DUMMY_CMD_FILE, 'w') as f:
                f.write("# Dummy file\n")

        self.mock_socket_patcher = patch('socket.socket')
        self.mock_socket_constructor = self.mock_socket_patcher.start()

        self.mock_socket_instance = MagicMock()

        self.mock_socket_instance.recv.side_effect = [
            b"Welcome, TestUser! You are now connected to the MUD.\n",
            f"{const.RESP_WEAPONS}: sword 10 axe 20\n".encode(),
            b"Some server message\n",
            b"",
        ]
        self.mock_socket_constructor.return_value = self.mock_socket_instance

        self.mock_readline_patcher = patch('readline.get_line_buffer', return_value="")
        self.mock_readline = self.mock_readline_patcher.start()

        self.held_stdout = io.StringIO()

        with patch('builtins.print'):
            self.client = MUDClient(host='test_host', port=12345, username='TestUser')
            self.client.running = True
            self.mock_socket_instance.sendall.reset_mock()
            self.mock_socket_instance.recv.reset_mock()  # Сбрасываем и recv

        self.client.weapons = {"sword": 10, "axe": 20}

    def tearDown(self):
        """Очистка после каждого тестового метода."""
        self.mock_socket_patcher.stop()
        self.mock_readline_patcher.stop()

        if os.path.exists(DUMMY_CMD_FILE):
            os.remove(DUMMY_CMD_FILE)

        sys.stdout = sys.__stdout__

    def test_move_up_command(self):
        """Тест: команда 'up' преобразуется в 'move 0 -1'."""
        self.mock_socket_instance.recv.return_value = f"{const.RESP_MOVED}: 0 -1\n".encode()

        self.client.onecmd("up")

        self.mock_socket_instance.sendall.assert_called_once_with(b"move 0 -1\n")

    def test_move_down_command(self):
        """Тест: команда 'down' преобразуется в 'move 0 1'."""
        self.mock_socket_instance.recv.return_value = f"{const.RESP_MOVED}: 0 1\n".encode()

        self.client.onecmd("down")
        self.mock_socket_instance.sendall.assert_called_once_with(b"move 0 1\n")


if __name__ == '__main__':
    unittest.main()
