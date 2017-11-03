import json
from typing import Union
from rapid.networking import Client, MessageProtocol, MessageSerializer

cls_from_type = {}
serializer = MessageSerializer(
    type_size_bytes=1,
    data_size_bytes=2,
    byteorder="big"
)


def unpack(type: int, data: bytes):
    message_cls = cls_from_type[type]
    return message_cls, message_cls.unpack(data)


class AbstractMessage:
    message_type: int

    def __init_subclass__(cls, **kwargs):
        assert cls.message_type not in cls_from_type
        cls_from_type[cls.message_type] = cls

    @classmethod
    def pack(cls, message: dict) -> bytes:
        raise NotImplementedError

    @classmethod
    def unpack(cls, message_data: bytes) -> dict:
        raise NotImplementedError

    @classmethod
    def send(cls, protocol: Union[Client, MessageProtocol], **message):
        data = cls.pack(message)
        print(f"{data}")
        protocol.send(cls.message_type, data)


class PlayerMoveAction(AbstractMessage):
    message_type = 0

    @classmethod
    def unpack(cls, message_data: bytes):
        return {
            "player_id": int.from_bytes(message_data[0:2], "big", signed=True),
            "dx": int.from_bytes(message_data[2:4], "big", signed=True),
            "dy": int.from_bytes(message_data[4:6], "big", signed=True)
        }

    @classmethod
    def pack(cls, message) -> bytes:
        return b"".join((
            message["player_id"].to_bytes(2, "big", signed=True),
            message["dx"].to_bytes(2, "big", signed=True),
            message["dy"].to_bytes(2, "big", signed=True)
        ))


class GameUpdate(AbstractMessage):
    message_type = 1

    @classmethod
    def unpack(cls, message_data: bytes):
        return json.loads(message_data.decode("utf-8"))

    @classmethod
    def pack(cls, message) -> bytes:
        return json.dumps(message).encode("utf-8")
