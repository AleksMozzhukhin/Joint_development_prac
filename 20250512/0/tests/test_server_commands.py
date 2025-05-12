import unittest
import multiprocessing
import time
import socket
import sys
import os
import asyncio

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mood.server.game_server import run_server
from mood.common import constants as const

TEST_HOST = 'localhost'
TEST_PORT = 65433
TEST_USER = "testuser"


def server_runner(host, port):
    """Target function for the server process."""
    try:
        print(f"Test server runner: Starting server on {host}:{port}")
        asyncio.run(run_server(host, port))
        print("Test server runner: Server stopped.")
    except Exception as e:
        print(f"Test server runner: Error running server: {e}")
        # Optionally re-raise or handle specific errors if needed
    finally:
        print(f"Test server runner: Exiting process.")


class TestServerCommands(unittest.TestCase):
    """Integration tests for MOOD server commands."""

    server_process = None
    client_socket = None

    @classmethod
    def setUpClass(cls):
        """Start the server before running any tests in this class."""
        print("\nSetting up test class: Starting server process...")
        cls.server_process = multiprocessing.Process(
            target=server_runner,
            args=(TEST_HOST, TEST_PORT),
            daemon=True
        )
        cls.server_process.start()
        print(f"Server process started (PID: {cls.server_process.pid}). Waiting for server to initialize...")
        time.sleep(2)
        print("Server should be ready.")

    @classmethod
    def tearDownClass(cls):
        """Stop the server after all tests in this class have run."""
        print("\nTearing down test class: Terminating server process...")
        if cls.server_process and cls.server_process.is_alive():
            cls.server_process.terminate()
            cls.server_process.join(timeout=2)
            if cls.server_process.is_alive():
                print("Warning: Server process did not terminate gracefully, killing.")
                cls.server_process.kill()
            print("Server process stopped.")
        else:
            print("Server process already stopped or not started.")

    def setUp(self):
        """Set up for each test method: Connect client and login."""
        print(f"\n--- Setting up test: {self._testMethodName} ---")
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Connecting client to {TEST_HOST}:{TEST_PORT}...")
            self.client_socket.connect((TEST_HOST, TEST_PORT))
            self.client_socket.settimeout(3.0)
            print("Client connected. Logging in...")

            try:
                initial_data = self.client_socket.recv(1024).decode()
                print(f"Initial server data: <<<{initial_data.strip()}>>>")
            except socket.timeout:
                print("No initial data received (timeout).")

            login_cmd = f"{const.CMD_LOGIN} {TEST_USER}\n"
            print(f"Sending login: {login_cmd.strip()}")
            self.client_socket.sendall(login_cmd.encode())

            response = self.client_socket.recv(1024).decode()
            print(f"Login response: <<<{response.strip()}>>>")
            self.assertTrue(response.startswith("Welcome") or const.RESP_WEAPONS in response,
                            "Login failed or did not receive expected welcome/weapon info")
            try:
                response2 = self.client_socket.recv(1024).decode()
                print(f"Additional login response data: <<<{response2.strip()}>>>")
                self.assertTrue(const.RESP_WEAPONS in response or const.RESP_WEAPONS in response2,
                                "Did not receive weapon list after login")
            except socket.timeout:
                self.assertTrue(const.RESP_WEAPONS in response, "Did not receive weapon list after login (timeout)")

            print("Login successful.")

        except ConnectionRefusedError:
            print(f"ERROR: Connection refused. Is the server running on {TEST_HOST}:{TEST_PORT}?")
            self.fail(f"Could not connect to server at {TEST_HOST}:{TEST_PORT}")
        except Exception as e:
            print(f"ERROR during setup: {e}")
            self.tearDown()
            self.fail(f"Exception during test setup: {e}")

    def tearDown(self):
        """Tear down after each test method: Close client connection."""
        print(f"--- Tearing down test: {self._testMethodName} ---")
        if self.client_socket:
            print("Closing client socket...")
            self.client_socket.close()
            self.client_socket = None
            print("Client socket closed.")

    def send_recv(self, command):
        """Helper method to send a command and receive the response."""
        if not self.client_socket:
            self.fail("Client socket is not connected.")
        try:
            full_command = f"{command}\n"
            print(f"Sending command: {command}")
            self.client_socket.sendall(full_command.encode())
            response = self.client_socket.recv(2048).decode().strip()
            print(f"Received response: <<<{response}>>>")
            return response
        except socket.timeout:
            print("ERROR: Socket timeout waiting for response.")
            self.fail(f"Timeout receiving response for command: {command}")
        except Exception as e:
            print(f"ERROR: Exception during send/recv: {e}")
            self.fail(f"Exception sending/receiving command '{command}': {e}")

    def test_01_add_monster(self):
        """Test adding a monster to the map."""
        print("Executing test: add_monster")
        cmd = f'{const.CMD_ADDMON} dragon 1 1 "Roar" 10'
        response = self.send_recv(cmd)
        self.assertTrue(response.startswith(f"{const.RESP_ADDED}: dragon 1 1 Roar"),
                        f"Unexpected response for addmon: {response}")
        print("Add monster test PASSED.")

    def test_02_move_and_encounter(self):
        """Test moving to a monster's location and triggering an encounter."""
        print("Executing test: move_and_encounter")
        monster_name = "goblin"
        monster_hello = "Yarr!"
        cmd_add = f'{const.CMD_ADDMON} {monster_name} 0 1 "{monster_hello}" 5'
        response_add = self.send_recv(cmd_add)
        self.assertTrue(response_add.startswith(f"{const.RESP_ADDED}: {monster_name}"),
                        f"Failed to add monster for move test: {response_add}")

        cmd_move = f"{const.CMD_MOVE} 0 1"  # down
        response_move = self.send_recv(cmd_move)

        expected_moved = f"{const.RESP_MOVED}: 0 1"
        expected_encounter = f"{const.RESP_ENCOUNTER}: {monster_name} {monster_hello}"

        self.assertIn(expected_moved, response_move, "Move confirmation missing")
        self.assertIn(expected_encounter, response_move, "Encounter message missing")
        print("Move and encounter test PASSED.")

    def test_03_attack_monster(self):
        """Test attacking a monster and checking HP reduction and death."""
        print("Executing test: attack_monster")
        monster_name = "ogre"
        monster_hello = "Ugh?"
        monster_hp = 15
        cmd_add = f'{const.CMD_ADDMON} {monster_name} 1 0 "{monster_hello}" {monster_hp}'
        response_add = self.send_recv(cmd_add)
        self.assertTrue(response_add.startswith(f"{const.RESP_ADDED}: {monster_name}"),
                        f"Failed to add monster for attack test: {response_add}")

        cmd_move = f"{const.CMD_MOVE} 1 0"  # right
        response_move = self.send_recv(cmd_move)
        expected_moved = f"{const.RESP_MOVED}: 1 0"
        expected_encounter = f"{const.RESP_ENCOUNTER}: {monster_name} {monster_hello}"
        self.assertIn(expected_moved, response_move, "Move confirmation missing before attack")
        self.assertIn(expected_encounter, response_move, "Encounter message missing before attack")

        attack_damage = 10
        cmd_attack1 = f"{const.CMD_ATTACK} {monster_name} {attack_damage}"
        response_attack1 = self.send_recv(cmd_attack1)

        hp_after_attack1 = monster_hp - attack_damage
        expected_attack1 = f"{const.RESP_ATTACK}: {monster_name} {attack_damage} {hp_after_attack1}"
        self.assertEqual(response_attack1, expected_attack1, "First attack response incorrect")

        cmd_attack2 = f"{const.CMD_ATTACK} {monster_name} {attack_damage}"
        response_attack2 = self.send_recv(cmd_attack2)

        actual_damage2 = min(attack_damage, hp_after_attack1)
        hp_after_attack2 = hp_after_attack1 - actual_damage2
        expected_attack2 = f"{const.RESP_ATTACK}: {monster_name} {actual_damage2} {hp_after_attack2} {const.RESP_KILLED}"
        self.assertEqual(response_attack2, expected_attack2, "Killing blow attack response incorrect")
        print("Attack monster test PASSED.")


if __name__ == '__main__':
    print("Starting MOOD Server Command Integration Tests")
    multiprocessing.freeze_support()
    unittest.main()
