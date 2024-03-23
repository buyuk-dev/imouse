"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""

import sys
from pathlib import Path

# Include path to common module
project_root_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(project_root_path)

import logging
import socket
from multiprocessing import Queue, Process
import signal

from pynput.mouse import Button, Controller

from common.command import Command
from config import MouseServerConfig

import plotter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



class MouseController:

    def __init__(self):
        self.mouse = Controller()

    def apply_command(self, command: Command):
        self.mouse.move(command.move[0], command.move[1])


class MouseServerApp:

    def __init__(self, server_config: MouseServerConfig, plotter_data_queue: Queue):
        self.config = server_config
        self.controller = MouseController()
        self.is_running = False
        self.plotter_data_queue = plotter_data_queue

    def get_address(self):
        addr, port = self.config.address.split(":")
        return addr, int(port)

    def wait_for_connection(self, server_socket):
        server_socket.bind(self.get_address())
        server_socket.listen()

        logger.info("Server waiting for connection...")
        connection, address = server_socket.accept()
        logger.info("Connection accepted from %s", address)

        return connection

    def run(self):
        logger.info("Server is running.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            connection = self.wait_for_connection(server_socket)

            self.is_running = True
            while self.is_running:
                try:
                    self.step(connection)
                except Exception as e:
                    logger.exception(
                        "Server encountered an error while executing step function."
                    )
                    self.is_running = False

    def step(self, connection):
        cmd = Command.recv(connection)
        logger.debug("Command received: %s", str(cmd))

        self.plotter_data_queue.put(cmd.move)
        self.controller.apply_command(cmd)


if __name__ == "__main__":
    config = MouseServerConfig.from_json()
    logger.info(str(config))

    # Start plotter process
    plotter_data_queue = Queue()
    plotter_process:Process = Process(target=plotter.main, args=(config.plot, plotter_data_queue), daemon=True)
    plotter_process.start()

    def signal_handler(sig, frame):
        logger.info("Signal received, stopping...")
        plotter_process.terminate()
        plotter_process.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start mouse server
    app = MouseServerApp(config, plotter_data_queue)
    while True:
        app.run()
