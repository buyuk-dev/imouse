from dataclasses import dataclass, asdict
import json
from socket import socket
from typing import List


@dataclass
class Command:
    """
    Represents mouse command, which can include:
    - move: 3D mouse move vector
    - dscroll: mouse wheel scroll change
    - click: buttons clicks

    Provides convenience method to serialize command as string.
    """
    move: 'List[float]'
    #dscroll:'Optional[int]'
    click: 'List[bool]'
    plot_data: 'List[List[float]]'

    def asjson(self) -> str:
        """
        Convert self to json string.
        """
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str) -> 'Command':
        data = json.loads(json_str)
        return Command(**data)

    def send(self, connection:socket):
        """
        Encode command as json and send over socket.
        """
        connection.sendall(self.asjson().encode('utf-8'))

    @classmethod
    def recv(cls, connection:socket):
        data = connection.recv(1024)
        data = data.decode('utf-8')
        connection.sendall("ACK".encode("utf-8"))
        return cls.from_json(data)

    @classmethod
    def wait_for_ack(cls, connection:socket):
        ack = connection.recv(8).decode('utf-8')
        if ack == "ACK":
            return True
        else:
            return False
