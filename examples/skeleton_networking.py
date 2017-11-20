import skeleton


HOST, PORT = "localhost", 8080


class ClockMessage(skeleton.net.AbstractMessage):
    message_type = 0

    def __init__(self, now: str):
        self.now = now

    @classmethod
    def unpack(cls, message_data: bytes) -> "ClockMessage":
        return cls(message_data.decode())

    def pack(self) -> bytes:
        return self.now.encode()


def run_server(net_mode):
    class EchoServer(skeleton.net.Server):
        def on_connection_made(self, protocol):
            print(f"+++ {protocol}")

        def on_connection_lost(self, protocol):
            print(f"--- {protocol}")

        def on_recv_message(self, message, protocol, addr=None):
            print("SERVER", message.now, protocol, addr)
            self.send(message, protocol, addr)

    print(f"Serving on {PORT} over {net_mode.upper()}")
    server = EchoServer(HOST, PORT, mode=net_mode)
    server.start()


def run_client(net_mode):
    import datetime

    class Game(skeleton.Game):
        @skeleton.net.handle(ClockMessage)
        def on_clock_message(self, message: ClockMessage):
            print("CLIENT", message.now)

        def on_key_press(self, symbol, modifiers):
            if symbol == skeleton.key.ENTER:
                message = ClockMessage(now=datetime.datetime.now().isoformat())
                self.client.send(message)
            else:
                return super().on_key_press(symbol, modifiers)

    print(f"Client talking to {PORT} over {net_mode.upper()}")
    g = Game(host=HOST, port=PORT, mode=net_mode, title="Press <Enter> to send a message")
    g.run()


def run_both(net_mode):
    import multiprocessing

    print("Starting server in new process")
    server = multiprocessing.Process(target=run_server, args=(net_mode,))
    server.start()
    run_client(net_mode)
    server.terminate()


if __name__ == '__main__':
    import sys; args = sys.argv[1:]
    mode = args[0] if args else "server"
    net_mode = args[1] if args else "tcp"
    locals()["run_" + mode](net_mode)
