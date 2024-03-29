"""
This module can be used to test plotter application.
It connects to the plotter queue server and produces random data.
"""

import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)

import time
from multiprocessing.managers import BaseManager
from config import PlotConfig
from numpy.random import random


class QueueManager(BaseManager):
    pass


def main():
    config = PlotConfig.from_json()

    logger.info("Initializing queue manager...")
    QueueManager.register("get_queue")
    queue_manager = QueueManager(
        address=config.get_address(), authkey=config.authkey.encode()
    )

    logger.info("Connecting to queue server...")
    queue_manager.connect()

    logger.info("Queue server connected.")
    queue = queue_manager.get_queue()

    is_running = True
    while is_running:
        try:
            logger.info("sending data packet...")
            queue.put(random(3).tolist())
            time.sleep(0.1)
        except ConnectionResetError:
            logger.info("Plotter server disconnected.")
            is_running = False



if __name__ == "__main__":
    main()
