import sys
from pathlib import Path

# Include path to common module
project_root_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(project_root_path)

import signal
import time
from multiprocessing import Queue
from multiprocessing.managers import BaseManager
import threading

import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)

from pyqt_plotter import Plotter
from config import PlotConfig


class QueueManager(BaseManager):
    pass


class QueueServerThread(threading.Thread):

    def __init__(self, address, authkey):
        super().__init__()
        self.queue = Queue()
        QueueManager.register("get_queue", callable=lambda: self.queue)
        self.address = address
        self.authkey = authkey
        logger.info("Initializing queue server...")

    def run(self):
        logger.info("Running queue server...")
        queue_manager = QueueManager(address=self.address, authkey=self.authkey.encode())
        server = queue_manager.get_server()
        server.serve_forever()


def main(config: PlotConfig):
    logger.info("Address: %s : %d", *config.get_address())
    queue_server = QueueServerThread(config.get_address(), config.authkey)
    queue_server.start()
    logger.info("Starting queue server...")

    time.sleep(1.0)
    queue_manager = QueueManager(config.get_address(), config.authkey.encode())
    logger.info("Connecting to queue server...")

    queue_manager.connect()
    logger.info("Queue server connected.")

    queue = queue_manager.get_queue()

    logger.info("Starting plotter...")
    plotter = Plotter(config, queue)
    plotter.run()


if __name__ == '__main__':
    try:
        # config = PlotConfig.from_json()
        config = PlotConfig(figsize=(800, 600), dpi=100, npoints=1000, scale=[-1.0, 1.0], refresh_interval=100, address="localhost:50001", authkey="abc")
        main(config)
    except:
        logger.exception("Plotter exception occured.")
        exit(1)
