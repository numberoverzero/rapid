from skeleton import AbstractMessage
HOST, PORT = "localhost", 8080


class MyMessage(AbstractMessage):
    message_type = 0

    @classmethod
    def unpack(cls, message_data: bytes) -> dict:
        return {"now": message_data.decode()}

    @classmethod
    def pack(cls, message: dict) -> bytes:
        return message["now"].encode()


def run_server():
    import json
    from skeleton import Server

    class EchoServer(Server):
        def on_connection_made(self, protocol): print(f"+++ {protocol}")

        def on_connection_lost(self, protocol): print(f"--- {protocol}")

        def on_recv_message(self, protocol, type, data):
            assert type == MyMessage.message_type
            received = MyMessage.unpack(data)
            print(json.dumps(received, sort_keys=True))
            MyMessage.send(protocol, received)

    print(f"Serving on {PORT}")
    server = EchoServer()
    server.run(HOST, PORT)


def run_client():
    import datetime
    from skeleton import Game, handle, key

    class MyGame(Game):
        @handle(MyMessage)
        def on_my_message(self, message: dict):
            print(message["now"])

        def on_key_press(self, symbol, modifiers):
            if symbol == key.ENTER:
                now = datetime.datetime.now().isoformat()
                MyMessage.send(self.client, {"now": now})
            else:
                return super().on_key_press(symbol, modifiers)

    print("Starting up client")
    g = MyGame()
    g.run(HOST, PORT)


if __name__ == '__main__':
    import sys
    {
        (): run_server,
        ("client",): run_client,
        ("server",): run_server
    }[tuple(sys.argv[1:])]()
