from typing import Union
from rapid.networking import Client, MessageProtocol, MessageSerializer
import json

cls_from_type = {}
type_from_cls = {}


def unpack(type: int, data: bytes):
    obj = cls_from_type[type]()
    obj.unpack(data)
    return obj


class AbstractGameMessage:
    def pack(self) -> bytes:
        raise NotImplementedError

    def send(self, protocol: Union[Client, MessageProtocol]) -> None:
        message_type = type_from_cls[self.__class__]
        message_data = self.pack()
        protocol.send(message_type, message_data)

    def unpack(self, data: bytes) -> None:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        n = len(cls_from_type)
        cls_from_type[n] = cls
        type_from_cls[cls] = n


class PlayerMoveAction(AbstractGameMessage):
    def __init__(self, player_id=None, dx=None, dy=None):
        self.player_id = player_id
        self.dx = dx
        self.dy = dy

    def unpack(self, data: bytes) -> None:
        self.player_id = int.from_bytes(data[0:2], "big", signed=True)
        self.dx = int.from_bytes(data[2:4], "big", signed=True)
        self.dy = int.from_bytes(data[4:6], "big", signed=True)

    def pack(self) -> bytes:
        return b"".join((
            self.player_id.to_bytes(2, "big", signed=True),
            self.dx.to_bytes(2, "big", signed=True),
            self.dy.to_bytes(2, "big", signed=True)
        ))


class GameUpdate(AbstractGameMessage):
    def __init__(self, type=None, data=None):
        self.type = type
        self.data = data

    def unpack(self, data: bytes) -> None:
        obj = json.loads(data.decode("utf-8"))
        self.type = obj["type"]
        self.data = obj["data"]

    def pack(self) -> bytes:
        return json.dumps({
            "type": self.type,
            "data": self.data
        }).encode("utf-8")


serializer = MessageSerializer(
    type_size_bytes=1,
    data_size_bytes=2,
    byteorder="big"
)
