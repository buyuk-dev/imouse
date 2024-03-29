"""
This module can be used to test plotter application.
It connects to the plotter queue server and produces random data.
"""

import time
from multiprocessing.managers import BaseManager
from config import PlotConfig
from numpy.random import random


class QueueManager(BaseManager): pass


def main():
    config = PlotConfig(figsize=(800, 600), dpi=100, npoints=1000, scale=[-1.0, 1.0], refresh_interval=100, address="localhost:50001", authkey="abc")

    print("Initializing queue manager...")
    QueueManager.register("get_queue")
    queue_manager = QueueManager(address=config.get_address(), authkey=config.authkey.encode())

    print("Connecting to queue server...")
    queue_manager.connect()

    print("Queue server connected.")
    queue = queue_manager.get_queue()

    while True:
        print("sending data packet...")
        queue.put(random(3).tolist())
        time.sleep(0.1)


if __name__ == '__main__':
    main()