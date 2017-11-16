import uvloop
from typing import Any, Optional, Tuple, Type, Union
from rapid import Scene
from rapid.net import AddrInfo, handle, tcp, udp

__all__ = [
    "AbstractMessage", "Client",
    "handle"
]

CLS_BY_TYPE = {}
TYPE_SIZE_BYTES = 1
TCP_MESSAGE_DATA_SIZE_BYTES = 2
MAX_MESSAGE_TYPES = 256 ** TYPE_SIZE_BYTES

client_classes = {
    "tcp": tcp.RoutingClient,
    "udp": udp.RoutingClient
}
server_classes = {
    "tcp": tcp.Server,
    "udp": udp.Server
}
serializers = {
    "tcp": tcp.MessageSerializer(
        type_size_bytes=TYPE_SIZE_BYTES,
        data_size_bytes=TCP_MESSAGE_DATA_SIZE_BYTES,
        byteorder="big"),
    "udp": udp.MessageSerializer(
        type_size_bytes=TYPE_SIZE_BYTES,
        byteorder="big")
}

MessageProtocol = Union[tcp.MessageProtocol, udp.MessageProtocol]


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

    def pack(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def unpack(cls, message_data: bytes) -> "AbstractMessage":
        raise NotImplementedError


def _unpack(message_type: int, message_data: bytes) -> Tuple[Type[AbstractMessage], Any]:
    message_cls = CLS_BY_TYPE[message_type]
    message = message_cls.unpack(message_data)
    return message_cls, message


class Client:
    def __init__(self, scene: Scene, host: str, port: int, mode: str="tcp") -> None:
        self.host = host
        self.port = port
        client_cls = client_classes[mode]
        serializer = serializers[mode]
        self._client = client_cls(scene, _unpack, loop=scene.window.loop, serializer=serializer)

    @property
    def connected(self):
        return self._client.connected

    def connect(self):
        assert not self.connected
        task = self._client.connect(host=self.host, port=self.port)
        self._client.loop.run_until_complete(task)

    def disconnect(self):
        assert self.connected
        task = self._client.disconnect()
        self._client.loop.run_until_complete(task)

    def send(self, message: AbstractMessage) -> None:
        assert self.connected
        self._client.send(message.message_type, message.pack())


class Server:
    def __init__(self, host: str, port: int, mode: str="tcp") -> None:
        self.host = host
        self.port = port
        server_cls = server_classes[mode]
        loop = uvloop.new_event_loop()
        serializer = serializers[mode]
        self._server = server_cls(loop=loop, serializer=serializer)
        self._initialize_server_callbacks()

    def _initialize_server_callbacks(self):
        def on_recv_message_connector(type: int, data: bytes, protocol: MessageProtocol, addr: AddrInfo=None):
            _, message = _unpack(type, data)
            self.on_recv_message(message, protocol, addr)
        self._server.on_recv_message = on_recv_message_connector

        self._server.on_connection_made = self.on_connection_made
        self._server.on_connection_lost = self.on_connection_lost

    def start(self):
        task = self._server.start(host=self.host, port=self.port)
        self._server.loop.run_until_complete(task)
        self._server.loop.run_forever()

    def stop(self):
        task = self._server.stop()
        self._server.loop.run_until_complete(task)

    # noinspection PyMethodMayBeStatic
    def send(
            self,
            message: AbstractMessage,
            protocol: MessageProtocol,
            addr: Optional[AddrInfo]=None) -> None:
        assert self._server.running
        protocol.send(message.message_type, message.pack(), addr=addr)

    def on_recv_message(
            self,
            message: AbstractMessage,
            protocol: Union[tcp.MessageProtocol, udp.MessageProtocol],
            addr: Optional[AddrInfo]=None) -> None:
        pass

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        pass

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        pass
