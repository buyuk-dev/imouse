"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""

import sys
from pathlib import Path

# Include path to common module
project_root_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(project_root_path)

import json
import logging
import socket
import threading
from collections import deque
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from pydantic import BaseModel
from pynput.mouse import Button, Controller

from common.command import Command


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PlotConfig(BaseModel):
    figsize: Tuple[int, int]
    dpi: int
    npoints: int
    scale: Tuple[float, float]
    refresh_interval: int


class MouseServerConfig(BaseModel):
    plot: PlotConfig
    address: str

    @classmethod
    def from_json(cls, path="settings.json") -> "MouseServerConfig":
        path = Path(path)
        data = json.loads(path.read_text())
        return MouseServerConfig(**data)


class PlottingThread(threading.Thread):
    def __init__(self, plot_config: PlotConfig):
        threading.Thread.__init__(self)
        self.config = plot_config
        self.daemon = True
        self.running = True
        self.dx_data = deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)
        self.dy_data = deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)

    def add_data(self, dx, dy):
        self.dx_data.append(dx)
        self.dy_data.append(dy)

    def get_figsize(self):
        w, h = self.config.figsize
        dpi = self.config.dpi
        return (w / dpi, h / dpi)

    def run(self):
        fig, axs = plt.subplots(2, figsize=self.get_figsize())
        fig.suptitle("Real-time Movement Commands")

        def animate(i):
            axs[0].cla()
            axs[1].cla()
            axs[0].plot(self.dx_data, label="DX")
            axs[1].plot(self.dy_data, label="DY")
            axs[0].legend(loc="upper left")
            axs[1].legend(loc="upper left")
            axs[0].set_title("X Axis Movement")
            axs[1].set_title("Y Axis Movement")
            axs[0].set_ylim(*self.config.scale)
            axs[1].set_ylim(*self.config.scale)

        ani = FuncAnimation(fig, animate, interval=self.config.refresh_interval)
        plt.show()

    def stop(self):
        self.running = False
        plt.close()


class MouseController:

    def __init__(self):
        self.mouse = Controller()

    def apply_command(self, command: Command):
        self.mouse.move(command.dx, command.dy)


class MouseServerApp:

    def __init__(self, server_config: MouseServerConfig):
        self.config = server_config
        self.controller = MouseController()
        self.is_running = False

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
            self.plot_thread = PlottingThread(self.config.plot)
            self.plot_thread.start()

            self.is_running = True
            while self.is_running:
                try:
                    self.step(connection)
                except Exception as e:
                    logger.exception(
                        "Server encountered an error while executing step function."
                    )
                    self.is_running = False

            self.plot_thread.stop()
            self.plot_thread.join()

    def step(self, connection):
        cmd = Command.recv(connection)
        logger.debug("Command received: %s", str(cmd))

        self.plot_thread.add_data(cmd.dx, -cmd.dy)
        self.controller.apply_command(cmd)


if __name__ == "__main__":
    config = MouseServerConfig.from_json()
    logger.info(str(config))

    app = MouseServerApp(config)

    while True:
        app.run()
