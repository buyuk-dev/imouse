"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""
import sys
from pathlib import Path
project_root_path = str(Path(__file__).absolute().parent.parent)
#print(project_root_path)
sys.path.append(project_root_path)

import socket
from pynput.mouse import Controller, Button

from common.command import Command


class MouseController:

    def __init__(self):
        self.mouse = Controller()

    def apply_commmand(self, command: Command):
        self.mouse.move(command.dx, command.dy)


class MouseServerApp:

    def __init__(self):
        self.controller = MouseController()
        self.address = ("0.0.0.0", 5000)
        self.is_running = False

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(self.address)
            server_socket.listen()

            print("michalski: Server started, waiting for connection...")
            connection, address = server_socket.accept()
            print(f"michalski: Connection from {address}")

            self.is_running = True
            while self.is_running:
                try:
                    self.step(connection)

                except Exception as e:
                    print(f"mmichalski: server step error: {e}")

    def step(self, connection):
        data = connection.recv(64).decode('utf-8')
        connection.sendall("ACK".encode("utf-8"))

        if not data:
            self.is_running = False
            return

        cmd = Command.from_json(data)
        self.controller.apply_command(cmd)


if __name__ == '__main__':
    app = MouseServerApp()
    app.run()