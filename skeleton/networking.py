"""
Simplified networking model requires messages to subclass AbstractMessage
"""
import asyncio
import uvloop
from typing import Optional, Union

from rapid.networking import tcp


CLS_BY_TYPE = {}
SERIALIZER = tcp.MessageSerializer(
    type_size_bytes=1,
    data_size_bytes=2,
    byteorder="big"
)
MAX_MESSAGE_TYPES = 8 ** SERIALIZER.type_size_bytes


def unpack(type: int, data: bytes):
    message_cls = CLS_BY_TYPE[type]
    return message_cls, message_cls.unpack(data)


class AbstractMessage:
    message_type: int

    def __init_subclass__(cls, **kwargs):
        type = cls.message_type
        assert isinstance(type, int), f"{cls}.message_type must be an int between [0, {MAX_MESSAGE_TYPES})"
        assert type not in CLS_BY_TYPE, f"messages have same type: {CLS_BY_TYPE[type]}, {cls}"
        assert 0 <= type < MAX_MESSAGE_TYPES, (
            f"skeleton.networking.serializer supports at most "
            f"{MAX_MESSAGE_TYPES} different message types")
        CLS_BY_TYPE[type] = cls

    @classmethod
    def pack(cls, message: dict) -> bytes:
        raise NotImplementedError

    @classmethod
    def unpack(cls, message_data: bytes) -> dict:
        raise NotImplementedError

    @classmethod
    def send(cls, protocol: Union[tcp.Client, tcp.MessageProtocol], message: dict):
        data = cls.pack(message)
        protocol.send(cls.message_type, data)


class Server(tcp.clients.Server):
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
        if loop is None:
            loop = uvloop.new_event_loop()
        super().__init__(loop, SERIALIZER)

    def run(self, host, port):
        self.loop.run_until_complete(self.start(host=host, port=port))
        self.loop.run_forever()


def attach_routing_client(scene) -> tcp.RoutingClient:
    client = tcp.RoutingClient(scene, unpack, loop=scene.window.loop, serializer=SERIALIZER)
    scene.client = client
    return client
