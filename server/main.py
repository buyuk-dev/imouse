"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""
import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)

from multiprocessing import Queue, Process
import signal
import socket

from pynput.mouse import Button, Controller

from common.command import Command
from config import MouseServerConfig
import plotter


class MouseController:

    def __init__(self):
        self.mouse = Controller()
        self.mouse_speed = 100.0

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
        self.config = server_config
        self.controller = MouseController()
        self.is_running = False
        self.plotter_data_queue = plotter_data_queue

    def get_address(self):
        addr, port = self.config.address.split(":")
        return addr, int(port)

    def wait_for_connection(self, server_socket:socket.socket):
        server_socket.settimeout(5.0)
        server_socket.bind(self.get_address())
        server_socket.listen()

        logger.info("Server waiting for connection...")
        connection, address = server_socket.accept()
        logger.info("Connection accepted from %s", address)

        return connection

    def run(self):
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
    

    def step(self, connection):
        cmd = Command.recv(connection)
        #logger.debug("Command received: %s", str(cmd))
        self.plotter_data_queue.put(cmd.move)
        self.controller.apply_command(cmd)


if __name__ == "__main__":
    config = MouseServerConfig.from_json()
    logger.info(str(config))

    # Start plotter process
    plotter_data_queue = Queue()
    plotter_process:Process = Process(target=plotter.main, args=(config.plot, plotter_data_queue))
    plotter_process.start()

    def signal_handler(sig, frame):
        logger.info("Signal received, stopping...")
        if plotter_process.is_alive():
            plotter_process.terminate()
            plotter_process.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start mouse server
    app = MouseServerApp(config, plotter_data_queue)
    while True:
        app.run()
