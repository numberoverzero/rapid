import asyncio
import datetime
import uvloop
from rapid.networking import Client, Server, MessageProtocol, MessageSerializer

import json
import sys


def now():
    return datetime.datetime.now().timestamp()


class AbstractGameMessage:
    message_type: int

    def pack(self) -> bytes:
        raise NotImplementedError

    def send(self, client: MessageProtocol) -> None:
        client.send(self.message_type, self.pack())


class PositionMessage(AbstractGameMessage):
    message_type = 2

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def pack(self) -> bytes:
        return b"".join((
            self.x.to_bytes(2, "big"),
            self.y.to_bytes(2, "big")
        ))

    @classmethod
    def unpack(cls, data: bytes) -> "PositionMessage":
        return cls(
            int.from_bytes(data[0:2], "big"),
            int.from_bytes(data[2:4], "big")
        )

    def __repr__(self):
        return json.dumps({"x": self.x, "y": self.y}, sort_keys=True)


class GameStatusMessage(AbstractGameMessage):
    message_type = 4

    def __init__(self, type: str, data: dict) -> None:
        self.type = type
        self.data = data

    def pack(self) -> bytes:
        return json.dumps({
            "type": self.type,
            "data": self.data
        }).encode("utf-8")

    @classmethod
    def unpack(cls, data: bytes) -> "GameStatusMessage":
        obj = json.loads(data.decode("utf-8"))
        return cls(**obj)

    def __repr__(self):
        return json.dumps({"type": self.type, "data": self.data}, sort_keys=True)


message_classes = {
    cls.message_type: cls for cls in AbstractGameMessage.__subclasses__()
}
serializer = MessageSerializer()


def run_server():
    loop = uvloop.new_event_loop()

    class GameServer(Server):
        def __init__(self, loop: asyncio.AbstractEventLoop, serializer: MessageSerializer) -> None:
            super().__init__(loop, serializer)
            self.clients = set()

        def on_connection_made(self, protocol: MessageProtocol) -> None:
            for client in self.clients:
                player_connected = GameStatusMessage("player.connected", {"time": now()})
                player_connected.send(client)
            self.clients.add(protocol)

        def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
            msg_cls = message_classes[type]
            msg = msg_cls.unpack(data)
            for client in self.clients:
                if client is protocol:
                    continue
                msg.send(client)

        def on_connection_lost(self, protocol: MessageProtocol) -> None:
            self.clients.remove(protocol)
            for client in self.clients:
                player_disconnected = GameStatusMessage("player.disconnected", {"time": now()})
                player_disconnected.send(client)

        def on_start(self) -> None:
            print(f"Serving on {self._server.sockets[0].getsockname()}")

    server = GameServer(loop=loop, serializer=serializer)
    loop.create_task(server.start(host="127.0.0.1", port=8888))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("shutting down")
        loop.run_until_complete(server.stop())


def run_client():
    loop = uvloop.new_event_loop()

    class GameClient(Client):

        def on_connection_made(self, protocol: MessageProtocol) -> None:
            print(f"connected")

        def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
            msg_cls = message_classes[type]
            msg = msg_cls.unpack(data)
            print(f"{msg.__class__.__name__}: {msg}")

        def on_connection_lost(self, protocol: MessageProtocol) -> None:
            print(f"disconnected")

    client = GameClient(loop=loop, serializer=serializer)
    loop.create_task(client.connect(host="127.0.0.1", port=8888))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("disconnecting")
        loop.run_until_complete(client.disconnect())


if __name__ == '__main__':
    mode = sys.argv[-1]
    if mode == "server":
        run_server()
    elif mode == "client":
        run_client()
    else:
        raise ValueError(f"Unknown mode {mode}")
