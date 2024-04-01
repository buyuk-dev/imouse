"""
Deprecated: use pyqt_plotter instead.

Data visualisation module for iMosue implemented using Matplotlib framework.
Very inefficient, UI keeps hanging. Could improve it a bit but decided to rewrite
visualisation using pyqtgraph package.
"""

import common.logging as logging

logger = logging.get_logger(__name__)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from collections import deque

from config import PlotConfig
from multiprocessing import Queue


class Plotter:
    """
    Intented to be run as a separate process due to matplotlib restrictions regarding running in main thread.
    """

    def __init__(self, plot_config: PlotConfig, data_queue: Queue):

        self.config = plot_config
        self.queue = data_queue

        self.axes = ("x", "y", "z")
        self.data = [
            deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)
            for _ in self.axes
        ]

    def add_data(self, vec):
        logger.info(f"adding data to plot: {vec}")
        for data, new_data in zip(self.data, vec):
            data.append(new_data)

    def get_figsize(self):
        w, h = self.config.figsize
        dpi = self.config.dpi
        return (w / dpi, h / dpi)

    def run(self):
        fig, axs = plt.subplots(3, figsize=self.get_figsize())
        fig.suptitle("Real-time Movement Commands")

        def animate(i):
            while not self.queue.empty():
                data = self.queue.get()
                self.add_data(data)

            axs[0].cla()
            axs[1].cla()
            axs[2].cla()

            axs[0].plot(self.dx_data, label="DX")
            axs[1].plot(self.dy_data, label="DY")
            axs[2].plot(self.dz_data, label="DZ")

            axs[0].legend(loc="upper left")
            axs[1].legend(loc="upper left")
            axs[2].legend(loc="upper left")

            axs[0].set_title("X Axis Movement")
            axs[1].set_title("Y Axis Movement")
            axs[2].set_title("Z Axis Movement")

            axs[0].set_ylim(*self.config.scale)
            axs[1].set_ylim(*self.config.scale)
            axs[2].set_ylim(*self.config.scale)

        ani = FuncAnimation(fig, animate, interval=self.config.refresh_interval)
        plt.show()
