import asyncio
from typing import Optional, Callable, Any, Tuple, Dict, Type

from ..shared import get_routing_annotations_for
from .messages import MessageHandler, MessageProtocol, MessageSerializer


class Client(MessageHandler):
    loop: asyncio.AbstractEventLoop
    protocol: Optional[MessageProtocol]

    def __init__(self, loop: asyncio.AbstractEventLoop, serializer: MessageSerializer) -> None:
        self.protocol_factory = lambda: MessageProtocol(serializer, self)
        self.protocol = None
        self.loop = loop

    @property
    def connected(self) -> bool:
        return self.protocol is not None and self.protocol.transport is not None

    async def connect(self, *, host, port, **kwargs):
        _, self.protocol = await self.loop.create_connection(self.protocol_factory, host=host, port=port, **kwargs)

    async def disconnect(self):
        if self.protocol is not None:
            self.protocol.disconnect()
        self.protocol = None

    def send(self, type: int, data: bytes) -> None:
        assert self.connected
        self.protocol.send(type, data)

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        raise NotImplementedError

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
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

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
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
        super().__init__()
        self._server = None
        self.protocol_factory = lambda: MessageProtocol(serializer, self)
        self.loop = loop
        self._running = False

    async def start(self, *, host, port, **kwargs):
        if not self._running:
            self._server = await self.loop.create_server(self.protocol_factory, host=host, port=port, **kwargs)
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

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
        pass

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass
