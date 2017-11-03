from rapid.networking import Server, MessageProtocol
from examples.simple_networking.messages import GameUpdate, PlayerMoveAction, serializer, unpack


next_player_id = 0


class GameServer(Server):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.clients = {}
        self.players = {}

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        global next_player_id

        new_player_id = next_player_id
        new_player_pos = (0, 0)

        next_player_id += 1

        self.clients[protocol] = new_player_id
        self.players[new_player_id] = new_player_pos

        print(f"player joined {new_player_id}")

        GameUpdate("set.player.id", {"player.id": new_player_id}).send(protocol)

        message = GameUpdate("player.joined", {"player.id": new_player_id, "player.pos": new_player_pos})
        for client in self.clients.keys():
            message.send(client)

        for player_id, pos in self.players.items():
            if player_id == new_player_id:
                continue
            GameUpdate("player.joined", {"player.id": player_id, "player.pos": pos}).send(protocol)

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
        message = unpack(type, data)
        if isinstance(message, PlayerMoveAction):
            player_id = self.clients[protocol]
            self._move(player_id, message.dx, message.dy)
            for client in self.clients:
                message.send(client)

    def _move(self, player_id: int, dx: int, dy: int):
        player_x, player_y = self.players[player_id]
        player_x += dx
        player_y += dy
        self.players[player_id] = player_x, player_y

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        old_player_id = self.clients.pop(protocol)
        self.players.pop(old_player_id)

        print(f"player left {old_player_id}")

        message = GameUpdate("player.left", {"player.id": old_player_id})
        for client in self.clients:
            message.send(client)

    def on_start(self) -> None:
        print(f"Serving on {self._server.sockets[0].getsockname()}")


def main(host: str="0.0.0.0"):
    import uvloop
    loop = uvloop.new_event_loop()

    server = GameServer(loop=loop, serializer=serializer)
    loop.create_task(server.start(host=host, port=8888))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("shutting down")
        loop.run_until_complete(server.stop())
