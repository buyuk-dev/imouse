from multiprocessing import Queue
from multiprocessing.managers import BaseManager

from pyqt_plotter import Plotter
from config import PlotConfig

from common.network_utils import parse_address
import common.logger_config as logger_config
logger = logger_config.get_logger(__name__)



class QueueManager(BaseManager):
    queue = Queue()


def get_shared_queue():
    return QueueManager.queue


QueueManager.register("get_queue", callable=get_shared_queue)


class QueueServer:

    def __init__(self, address, authkey):
        self.queue = Queue()
        self.queue_manager = QueueManager(address=address, authkey=authkey.encode())
        logger.info("Initializing queue server...")

    def start(self):
        logger.info("Running queue server...")
        self.queue_manager.start()

    def stop(self):
        logger.info("Stopping queue server...")
        self.queue_manager.shutdown()
        logger.info("Queue server stopped.")


def main(config: PlotConfig):
    address = parse_address(config.address)
    logger.info("Address: %s : %d", *address)
    queue_server = QueueServer(address, config.authkey)
    queue_server.start()

    queue_manager = QueueManager(address, config.authkey.encode())
    queue_manager.connect()
    queue = queue_manager.get_queue()

    logger.info("Starting plotter...")
    plotter = Plotter(config, queue)
    plotter.run()

    queue_server.stop()


if __name__ == "__main__":
    try:
        config = PlotConfig.from_json()
        main(config)
    except:
        logger.exception("Plotter exception occured.")
        exit(1)
