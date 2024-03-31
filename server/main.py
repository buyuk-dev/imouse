"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""
import sys
import signal
import socket

from multiprocessing import Queue
from multiprocessing.managers import BaseManager

from pynput.mouse import Button, Controller
from typing import Optional

from common.command import Command
from config import MouseServerConfig

from common.network_utils import parse_address
import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)


class QueueManager(BaseManager):
    pass


class MouseController:

    def __init__(self, mouse_speed):
        self.mouse = Controller()
        self.mouse_speed = mouse_speed

    def apply_command(self, command: Command):
        if command.click:
            if command.click[0]:
                logger.debug("lmb click")
                self.mouse.click(Button.left)

            elif command.click[1]:
                logger.debug("rmb click")
                self.mouse.click(Button.right)

        dx = int(command.move[0] * self.mouse_speed)
        dy = int(command.move[1] * self.mouse_speed)

        self.mouse.move(dx, -dy)


class MouseServerApp:

    def __init__(self, server_config: MouseServerConfig, plotter_data_queue: Queue):
        """
        Initialize server instance.
        """
        self.config = server_config
        self.controller = MouseController(mouse_speed=server_config.mouse_speed)
        self.is_running = False
        self.plotter_data_queue = plotter_data_queue

    def run_forever(self):
        """
        Run server in a forever loop.
        """
        while True:
            app.run()

    def run(self):
        """
        Wait for client connection and run processing until disconnected.
        """
        logger.info("Server is running.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            try:
                connection = self.wait_for_connection(server_socket)
            except socket.timeout:
                return

            self.is_running = True
            while self.is_running:
                try:
                    self.step(connection)
                except Exception as e:
                    logger.exception(
                        "Server encountered an error while executing step function."
                    )
                    self.is_running = False

    def step(self, connection:socket.socket):
        """
        Wait for next command and apply it.
        If plotter service was connected send data.
        """
        cmd = Command.recv(connection)

        if self.plotter_data_queue:
            self.plotter_data_queue.put(cmd.move)

        self.controller.apply_command(cmd)

    def wait_for_connection(self, server_socket:socket.socket) -> socket.socket:
        """
        Waits for a client connection. Returns connection socket.
        """
        server_socket.settimeout(5.0)
        server_socket.bind(parse_address(self.config.address))
        server_socket.listen()

        logger.info("Server waiting for connection...")
        connection, address = server_socket.accept()
        logger.info("Connection accepted from %s", address)

        return connection


def try_connect_plotter(config:MouseServerConfig) -> Optional[Queue]:
    """
    Attempt to connect to plotter service. If successful, returns Queue which can be used to feed data to it.
    """
    try:
        QueueManager.register("get_queue")
        queue_manager = QueueManager(
            address=parse_address(config.plotter_address), authkey=config.plotter_authkey.encode()
        )

        logger.info("Connecting to queue server...")
        queue_manager.connect()

        logger.info("Queue server connected.")
        plotter_data_queue = queue_manager.get_queue()
        return plotter_data_queue

    except ConnectionRefusedError:
        logger.info("Could not connect to plotter service.")
        return None


if __name__ == "__main__":
    config = MouseServerConfig.from_json()
    logger.info(str(config))

    def signal_handler(sig, frame):
        logger.info("Signal received, stopping...")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    plotter_data_queue = try_connect_plotter(config)
    app = MouseServerApp(config, plotter_data_queue)
    app.run_forever()

