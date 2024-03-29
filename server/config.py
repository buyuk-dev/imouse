from pydantic import BaseModel
from typing import Optional, Tuple
from pathlib import Path
import json


class MouseServerConfig(BaseModel):
    address: str

    @classmethod
    def from_json(cls, path="settings.json") -> "MouseServerConfig":
        path = Path(path)
        data = json.loads(path.read_text())
        return MouseServerConfig(**data)
