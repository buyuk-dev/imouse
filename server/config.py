from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json


class MouseServerConfig(BaseModel):
    address: str
    mouse_speed: int
    plotter_address: Optional[str]
    plotter_authkey: Optional[str]

    @classmethod
    def from_json(cls, path="config/settings.json") -> "MouseServerConfig":
        path = Path(path)
        data = json.loads(path.read_text())
        return MouseServerConfig(**data)
