from dataclasses import dataclass, asdict
import json
from socket import socket
from typing import Optional


@dataclass
class Command:
    """
    Represents mouse command, which can include:
    - dx, dy: mouse movement
    - dscroll: mouse wheel scroll change
    - click: buttons clicks

    Provides convenience method to serialize command as string.
    """
    dx:int
    dy:int
    #dscroll:'Optional[int]'
    #click:'Optional[tuple[bool, bool]]'

    def asjson(self) -> str:
        """
        Convert self to json string.
        """
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str) -> 'Command':
        data = json.loads(json_str)
        return Command(**data)

    def send(self, socket:socket):
        """
        Encode command as json and send over socket.
        """
        socket.sendall(self.asjson().encode('utf-8'))

    @classmethod
    def wait_for_ack(cls, socket:socket):
        ack = socket.recv(8).decode('utf-8')
        if ack == "ACK":
            return True
        else:
            return False
