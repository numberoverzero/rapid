from ._shared import AddrInfo, MessageHandler, MessageProtocol, build_slices, get_routing_annotations_for
from typing import Any, Callable, Dict, Optional, Tuple, Type
import asyncio


class MessageSerializer:
    def __init__(self, type_size_bytes: int=1, byteorder: str="big") -> None:
        """

        :param type_size_bytes: number of bytes used to represent the message type
        :param byteorder: determines the byte order used to represent the integer
        """
        self.byteorder = byteorder
        self.type_size_bytes = type_size_bytes
        self.fixed_slices = build_slices((
            ("msg_type", type_size_bytes),
        ))

    def pack(self, type: int, data: bytes) -> bytes:
        return b"".join((
            type.to_bytes(self.type_size_bytes, self.byteorder),
            data
        ))

    def unpack(self, data: bytes) -> Tuple[int, bytes]:
        message_type = int.from_bytes(
            data[self.fixed_slices["msg_type"]],
            byteorder=self.byteorder
        )
        data_start = self.fixed_slices["_total"].stop
        message_data = data[data_start:]
        return message_type, message_data


class UDPMessageProtocol(MessageProtocol[asyncio.DatagramProtocol]):
    serializer: MessageSerializer

    def __init__(self, serializer: MessageSerializer, handler: MessageHandler) -> None:
        super().__init__(handler)
        self.serializer = serializer

    def send(self, type: int, data: bytes, addr: Optional[AddrInfo]=None) -> None:
        assert self.transport
        packed = self.serializer.pack(type, data)
        self.transport.sendto(packed, addr)

    # asyncio.DatagramProtocol =======================================================================================

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport
        self.handler.on_connection_made(self)

    def datagram_received(self, data: bytes, addr: AddrInfo):
        msg_type, msg_data = self.serializer.unpack(data)
        self.handler.on_recv_message(msg_type, msg_data, self, addr)

    def connection_lost(self, exc) -> None:
        self.transport = None
        self.handler.on_connection_lost(self)


class Client(MessageHandler):
    loop: asyncio.AbstractEventLoop
    protocol: Optional[MessageProtocol]

    def __init__(self, loop: asyncio.AbstractEventLoop, serializer: MessageSerializer) -> None:
        self.protocol_factory = lambda: UDPMessageProtocol(serializer, self)
        self.protocol = None
        self.loop = loop

    @property
    def connected(self) -> bool:
        return self.protocol is not None and self.protocol.transport is not None

    async def connect(self, *, host: str, port: int, **kwargs):
        _, self.protocol = await self.loop.create_datagram_endpoint(
            self.protocol_factory, remote_addr=(host, port), **kwargs)

    async def disconnect(self):
        if self.protocol is not None:
            self.protocol.disconnect()
        self.protocol = None

    def send(self, type: int, data: bytes) -> None:
        assert self.connected
        self.protocol.send(type, data)

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        raise NotImplementedError

    def on_recv_message(
            self, type: int, data: bytes,
            protocol: MessageProtocol, addr: Optional[AddrInfo]=None) -> None:
        raise NotImplementedError

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        raise NotImplementedError


class RoutingClient(Client):
    def __init__(self, scene, unpack: Callable[[int, bytes], Tuple[Any, Any]], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scene = scene
        self._routes = self._build_routes(scene)
        self._unpack = unpack

    # noinspection PyMethodMayBeStatic
    def _build_routes(self, scene) -> Dict[Type[Any], Callable[[Any], Any]]:
        routes = {}
        assert not isinstance(scene, type)  # must be an instance of the annotated class, not the class itself
        for func, message_cls, *_ in get_routing_annotations_for(scene):
            assert message_cls not in routes
            routes[message_cls] = func
        return routes

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        pass

    def on_recv_message(
            self, type: int, data: bytes,
            protocol: MessageProtocol, addr: Optional[AddrInfo]=None) -> None:
        message_cls, message = self._unpack(type, data)
        handler = self._routes.get(message_cls, None)
        if handler:
            handler(message)

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        pass


class Server(MessageHandler):
    loop: asyncio.AbstractEventLoop
    _running: bool
    _server: asyncio.AbstractServer

    def __init__(self, loop: asyncio.AbstractEventLoop, serializer: MessageSerializer) -> None:
        self._server = None
        self.protocol_factory = lambda: UDPMessageProtocol(serializer, self)
        self.loop = loop
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def start(self, *, host, port, **kwargs):
        if not self._running:
            self._server = await self.loop.create_datagram_endpoint(
                self.protocol_factory, local_addr=(host, port), **kwargs)
            self.on_start()
        self._running = True

    async def stop(self) -> None:
        if self._running:
            self.on_stop()
            self._server.close()
            await self._server.wait_closed()
        self._running = False

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        pass

    def on_recv_message(
            self, type: int, data: bytes,
            protocol: MessageProtocol, addr: Optional[AddrInfo]=None) -> None:
        pass

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass
