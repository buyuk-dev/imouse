"""
Mouse Server (Must be running on the device which will be controlled using the app).
"""
import sys
from pathlib import Path
project_root_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(project_root_path)

import threading
import time
import socket

import numpy as np
from pynput.mouse import Controller, Button
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from common.command import Command
from collections import deque


class PlottingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # Allows thread to be automatically closed on main program exit
        self.dx_data = deque(np.zeros(1000), maxlen=1000)
        self.dy_data = deque(np.zeros(1000), maxlen=1000)
        self.running = True

    def add_data(self, dx, dy):
        # This method simulates receiving new data
        self.dx_data.append(dx)
        self.dy_data.append(dy)

    def run(self):
        desired_width_px = 2000
        desired_height_px = 800
        dpi = 100 
        figsize_inches = (desired_width_px / dpi, desired_height_px / dpi)

        fig, axs = plt.subplots(2, figsize=figsize_inches)
        fig.suptitle('Real-time Movement Commands')
        
        def animate(i):
            axs[0].cla()
            axs[1].cla()
            axs[0].plot(self.dx_data, label='DX')
            axs[1].plot(self.dy_data, label='DY')
            axs[0].legend(loc='upper left')
            axs[1].legend(loc='upper left')
            axs[0].set_title("X Axis Movement")
            axs[1].set_title("Y Axis Movement")
            axs[0].set_ylim(-2.0, 2.0)
            axs[1].set_ylim(-2.0, 2.0)
        
        ani = FuncAnimation(fig, animate, interval=100)
        plt.show()

    def stop(self):
        self.running = False


class MouseController:

    def __init__(self):
        self.mouse = Controller()

    def apply_command(self, command: Command):
        print(command.asjson())
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

            self.plot_thread = PlottingThread()
            self.plot_thread.start()

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

        self.plot_thread.add_data(cmd.dx, -cmd.dy)
        self.controller.apply_command(cmd)


if __name__ == '__main__':
    app = MouseServerApp()

    while True:
        app.run()