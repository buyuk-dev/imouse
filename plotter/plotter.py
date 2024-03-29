import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)

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
        self.data_queue = data_queue

        self.dx_data = deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)
        self.dy_data = deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)
        self.dz_data = deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)

    def add_data(self, vec):
        logger.info(f"adding data to plot: {vec}")
        self.dx_data.append(vec[0])
        self.dy_data.append(vec[1])
        self.dz_data.append(vec[2])

    def get_figsize(self):
        w, h = self.config.figsize
        dpi = self.config.dpi
        return (w / dpi, h / dpi)

    def run(self):
        fig, axs = plt.subplots(3, figsize=self.get_figsize())
        fig.suptitle("Real-time Movement Commands")

        def animate(i):
            while not self.data_queue.empty():
                data = self.data_queue.get()
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
