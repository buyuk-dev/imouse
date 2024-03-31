from typing import Tuple


def parse_address(address:str) -> Tuple[str, int]:
    try:
        addr, port = address.split(":")
        return addr, int(port)
    except:
        return None
