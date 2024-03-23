from pydantic import BaseModel
from typing import Optional, Tuple
from pathlib import Path
import json


class PlotConfig(BaseModel):
    figsize: Tuple[int, int]
    dpi: int
    npoints: int
    scale: Tuple[float, float]
    refresh_interval: int


class MouseServerConfig(BaseModel):
    plot: PlotConfig
    address: str

    @classmethod
    def from_json(cls, path="settings.json") -> "MouseServerConfig":
        path = Path(path)
        data = json.loads(path.read_text())
        return MouseServerConfig(**data)
