import pyglet
from rapid import Scene, Camera, Window, key
from rapid.networking import handle
from rapid.networking.tcp import RoutingClient
from examples.networking_routing.messages import GameUpdate, PlayerMoveAction, serializer, unpack


class MyScene(Scene):
    def __init__(self, *args, **kwargs) -> None:
        loop = kwargs.pop("loop", None)
        super().__init__(*args, **kwargs)
        self.movement = {
            key.W: 0,
            key.A: 0,
            key.S: 0,
            key.D: 0
        }
        self.id = None
        self.players = {}
        self.client = RoutingClient(self, unpack, loop=loop, serializer=serializer)

    def on_key_release(self, symbol, modifiers):
        if symbol in self.movement:
            self.movement[symbol] = 0
        else:
            super().on_key_release(symbol, modifiers)

    def on_key_press(self, symbol, modifiers):
        if symbol in self.movement:
            self.movement[symbol] = 1
        else:
            super().on_key_press(symbol, modifiers)

    def on_update(self, dt: float) -> None:
        speed = 1
        dy = speed * (self.movement[key.W] - self.movement[key.S])
        dx = speed * (self.movement[key.D] - self.movement[key.A])

        if dx or dy:
            PlayerMoveAction.send(self.client, player_id=self.id, dx=dx, dy=dy)

    def on_draw(self):
        with self.camera:
            pyglet.graphics.draw(
                4, pyglet.gl.GL_TRIANGLE_STRIP,
                ("v2i", (-50, -50, 50, -50, -50, 50, 50, 50)),
                ("c3B", (255, 0, 0) * 4)
            )

            for player_id, (x, y) in self.players.items():
                label = pyglet.text.Label(
                    f"Player {player_id}",
                    font_name="Times New Roman",
                    font_size=20,
                    x=x, y=y,
                    anchor_x="center",
                    anchor_y="center"
                )
                label.draw()

    def connect(self, host, port):
        self.client.loop.create_task(self.client.connect(host=host, port=port))

    @handle(GameUpdate)
    def _game_update(self, update: dict):
        data = update["data"]
        if update["type"] == "player.joined":
            self.on_player_joined(
                data["player.id"],
                data["player.pos"])
        elif update["type"] == "player.left":
            self.on_player_left(data["player.id"])
        elif update["type"] == "set.player.id":
            self.set_player_id(data["player.id"])

    def on_player_joined(self, player_id: int, player_pos: (int, int)):
        self.players[player_id] = player_pos

    def on_player_left(self, player_id: int):
        del self.players[player_id]

    def set_player_id(self, player_id: int):
        self.id = player_id

    @handle(PlayerMoveAction)
    def on_player_moved(self, action: dict):
        player_id = action["player_id"]
        player_x, player_y = self.players[player_id]
        player_x += action["dx"]
        player_y += action["dy"]
        self.players[player_id] = (player_x, player_y)

        if player_id == self.id:
            self.camera.world_x += action["dx"]
            self.camera.world_y += action["dy"]


def main(host: str="0.0.0.0"):
    import uvloop
    loop = uvloop.new_event_loop()

    width, height = 1024, 768
    camera = Camera()

    scene = MyScene(camera, "network-routing-scene", loop=loop)
    scene.connect(host, 8888)

    window = Window(width=width, height=height, scenes=[scene], loop=loop)
    window.run()


if __name__ == '__main__':
    main()
