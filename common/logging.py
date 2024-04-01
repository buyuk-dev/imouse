import logging

from numpy.typing import NDArray

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name):
    return logging.getLogger(name)

def get_vec_info_str(header: str, vec: NDArray) -> str:
    return f"{header}: " + " | ".join([f"{x:.3f}" for x in vec])

