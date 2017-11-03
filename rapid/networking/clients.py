from typing import Optional
import asyncio
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

    async def connect(self, **kwargs):
        _, self.protocol = await self.loop.create_connection(self.protocol_factory, **kwargs)

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

    async def start(self, **kwargs):
        if not self._running:
            self._server = await self.loop.create_server(self.protocol_factory, **kwargs)
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
