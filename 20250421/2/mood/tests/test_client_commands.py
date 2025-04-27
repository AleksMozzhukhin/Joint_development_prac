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

        self.mock_socket_constructor.return_value = self.mock_socket_instance

        initial_responses = [
            b"Welcome, TestUser! You are now connected to the MUD.\n",
            f"{const.RESP_WEAPONS}: sword 10 axe 20\n".encode(),
            b"Unexpected recv call response\n"
        ]
        self.mock_socket_instance.recv.side_effect = iter(initial_responses)

        self.mock_readline_patcher = patch('readline.get_line_buffer', return_value="")
        self.mock_readline = self.mock_readline_patcher.start()

        self.held_stdout = io.StringIO()

        try:
            with patch('builtins.print'):
                sendall_calls_before = self.mock_socket_instance.sendall.call_count
                recv_calls_before = self.mock_socket_instance.recv.call_count

                self.client = MUDClient(host='test_host', port=12345, username='TestUser')

                sendall_calls_after = self.mock_socket_instance.sendall.call_count
                recv_calls_after = self.mock_socket_instance.recv.call_count
                if (sendall_calls_after - sendall_calls_before != 2) or \
                        (recv_calls_after - recv_calls_before != 2):
                    print("WARNING setUp: Unexpected number of socket calls during MUDClient init!")

        except SystemExit as e:
            self.fail(f"MUDClient initialization failed with SystemExit: {e}")
        except Exception as e:
            self.fail(f"MUDClient initialization failed with Exception: {e}")

        self.mock_socket_instance.sendall.reset_mock()
        self.mock_socket_instance.recv.reset_mock()

        self.mock_socket_instance.recv.side_effect = None
        self.mock_socket_instance.recv.return_value = b''

        self.client.running = True
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
        expected_response = f"{const.RESP_MOVED}: 0 -1\n".encode()
        self.mock_socket_instance.recv.return_value = expected_response

        self.client.onecmd("up")

        self.mock_socket_instance.sendall.assert_called_once_with(b"move 0 -1\n")

    def test_move_down_command(self):
        """Тест: команда 'down' преобразуется в 'move 0 1'."""
        self.mock_socket_instance.recv.return_value = f"{const.RESP_MOVED}: 0 1\n".encode()

        self.client.onecmd("down")
        self.mock_socket_instance.sendall.assert_called_once_with(b"move 0 1\n")

    def test_addmon_command_valid_1(self):
        """Тест: валидная команда 'addmon' преобразуется корректно (случай 1)."""
        user_input = 'addmon Dragon coords 1 2 hp 100 hello "Roar!"'
        expected_protocol_command = b'addmon Dragon 1 2 "Roar!" 100\n'
        self.mock_socket_instance.recv.return_value = f"{const.RESP_ADDED}: Dragon 1 2 Roar!\n".encode()

        self.client.onecmd(user_input)
        self.mock_socket_instance.sendall.assert_called_once_with(expected_protocol_command)

    def test_addmon_command_valid_2(self):
        """Тест: валидная команда 'addmon' преобразуется корректно (случай 2 - другой порядок)."""
        user_input = 'addmon Goblin hp 25 hello "Yarr" coords 5 5'
        expected_protocol_command = b'addmon Goblin 5 5 "Yarr" 25\n'
        self.mock_socket_instance.recv.return_value = f"{const.RESP_ADDED}: Goblin 5 5 Yarr\n".encode()

        self.client.onecmd(user_input)
        self.mock_socket_instance.sendall.assert_called_once_with(expected_protocol_command)

    def test_addmon_command_invalid_params_missing_hp(self):
        """Тест: команда 'addmon' с пропущенным параметром 'hp'."""
        user_input = 'addmon Orc coords 3 3 hello "Waaagh!"'

        with patch('sys.stdout', new=self.held_stdout) as fake_stdout:
            self.client.onecmd(user_input)
        self.mock_socket_instance.sendall.assert_not_called()
        output = fake_stdout.getvalue().strip()
        self.assertIn("Invalid arguments: missing required parameters", output)

    def test_addmon_command_invalid_params_bad_coords(self):
        """Тест: команда 'addmon' с неверным количеством координат."""
        user_input = 'addmon Troll coords 7 hp 50 hello "Grrr"'

        with patch('sys.stdout', new=self.held_stdout) as fake_stdout:
            self.client.onecmd(user_input)

        self.mock_socket_instance.sendall.assert_not_called()
        output = fake_stdout.getvalue().strip()
        self.assertTrue(
            "Invalid arguments" in output or "invalid literal for int()" in output or "IndexError" in output)

    def test_addmon_command_invalid_params_negative_hp(self):
        """Тест: команда 'addmon' с отрицательным hp."""
        user_input = 'addmon Skeleton coords 0 0 hp -10 hello "Clack"'

        with patch('sys.stdout', new=self.held_stdout) as fake_stdout:
            self.client.onecmd(user_input)

        self.mock_socket_instance.sendall.assert_not_called()
        output = fake_stdout.getvalue().strip()
        self.assertIn("Invalid arguments: hitpoints must be positive", output)


if __name__ == '__main__':
    unittest.main()
