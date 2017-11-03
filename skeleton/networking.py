"""
Simplified networking model requires messages to subclass AbstractMessage
"""
import asyncio
import uvloop
from typing import Optional, Union
from rapid import networking
from rapid.networking import Client, MessageProtocol, MessageSerializer
from rapid.networking.routing import RoutingClient


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
    def send(cls, protocol: Union[Client, MessageProtocol], message: dict):
        data = cls.pack(message)
        protocol.send(cls.message_type, data)


class Server(networking.Server):
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
        if loop is None:
            loop = uvloop.new_event_loop()
        super().__init__(loop, serializer)

    def run(self, host, port):
        self.loop.create_task(self.start(host=host, port=port))
        self.loop.run_forever()


def attach_routing_client(scene) -> RoutingClient:
    client = RoutingClient(scene, unpack, loop=scene.window.loop, serializer=serializer)
    scene.client = client
    return client
