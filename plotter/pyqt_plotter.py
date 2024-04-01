"""
Data visualization module for iMouse using PyQt5 and pyqtgraph frameworks.
"""

import sys
import common.logging as logging

logger = logging.get_logger(__name__)

import numpy as np
from collections import deque

from config import PlotConfig
from multiprocessing import Queue

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import pyqtgraph


class PlotterWindow(QMainWindow):
    """
    Intented to be run as a separate process due to matplotlib restrictions regarding running in main thread.
    """

    def __init__(self, plot_config: PlotConfig, data_queue: Queue):
        super().__init__()

        self.config = plot_config
        self.queue = data_queue
        self.window_title = self.config.window_title

        self.axes = self.config.axes
        self.data = [
            deque(np.zeros(self.config.npoints), maxlen=self.config.npoints)
            for _ in self.axes
        ]

        self.initialize_ui()

    def initialize_ui(self):
        self.graph_widget = pyqtgraph.GraphicsLayoutWidget()
        self.setCentralWidget(self.graph_widget)

        self.plots = []
        self.curves = []

        for index, title in enumerate(self.axes):
            plot = self.graph_widget.addPlot(row=index, col=0)
            plot.setTitle(title)
            plot.setYRange(min=self.config.scale[0], max=self.config.scale[1])
            curve = plot.plot(pen=pyqtgraph.mkPen(width=2))
            self.plots.append(plot)
            self.curves.append(curve)

            if index < len(self.axes):
                self.graph_widget.nextRow()

        self.setWindowTitle(self.window_title)
        self.resize(*self.config.figsize)

        self.timer = QTimer()
        self.timer.setInterval(self.config.refresh_interval)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def add_data(self, vec):
        logger.info(f"adding data to plot: {vec}")
        for data, new_data in zip(self.data, vec):
            data.append(new_data)

    def update_plot(self):
        while not self.queue.empty():
            new_data = self.queue.get()
            self.add_data(new_data)
            logger.debug(f"received data: {new_data}")

        for curve, data in zip(self.curves, self.data):
            curve.setData(data)


class Plotter:
    """
    Wrapper class to run PlotterWindow in QApplication.
    """

    def __init__(self, plot_config: PlotConfig, data_queue: Queue):
        self.app = QApplication(sys.argv)
        self.plotter_window = PlotterWindow(plot_config, data_queue)

    def run(self):
        self.plotter_window.show()
        self.app.exec_()
