from dataclasses import dataclass

@dataclass
class Config:
    """
    Basic app config.
    """
    address:'tuple[str, int]' = ("192.168.8.24", 5000)
