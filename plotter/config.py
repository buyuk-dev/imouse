import json
from pathlib import Path
from typing import Tuple
from pydantic import BaseModel
import argparse


class Defaults:
    DPI = 100
    FIGSIZE = (800, 600)
    NPOINTS = 1000
    SCALE = (-1.0, 1.0)
    REFRESH_INTERVAL = 100
    ADDRESS = ("0.0.0.0", 50000)
    AUTHKEY = 'abc'


class PlotConfig(BaseModel):
    figsize: Tuple[int, int]
    dpi: int
    npoints: int
    scale: Tuple[float, float]
    refresh_interval: int
    address: str
    authkey: str

    def get_address(self) -> Tuple[str, int]:
        addr, port = self.address.split(":")
        return addr, int(port)

    @classmethod
    def from_json(cls, path="config/settings.json") -> "PlotConfig":
        path = Path(path)
        data = json.loads(path.read_text())
        return PlotConfig(**data)


def config_from_args(args) -> PlotConfig:
    try:
        figsize = tuple(int(val) for val in args.figsize.split(","))
    except:
        figsize = Defaults.FIGSIZE

    try:
        scale = tuple(float(val) for val in args.scale.split(","))
    except:
        scale = Defaults.SCALE

    dpi = args.dpi or Defaults.DPI
    npoints = args.npoints or Defaults.NPOINTS
    refresh_interval = args.refresh or Defaults.REFRESH_INTERVAL
    address = args.address or Defaults.ADDRESS
    authkey = args.authkey or Defaults.AUTHKEY

    return PlotConfig(figsize=figsize, dpi=dpi, npoints=npoints, scale=scale, refresh_interval=refresh_interval, address=address, authkey=authkey)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--figsize")
    args = parser.parse_args()
    return args
