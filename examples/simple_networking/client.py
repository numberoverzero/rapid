import json
import pyglet
from rapid import Camera, Scene, Window, key
from rapid.networking import Client, MessageProtocol
from examples.simple_networking.messages import GameUpdate, PlayerMoveAction, serializer, unpack


class GameClient(Client):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scene = None

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        print("connection established.")

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
        message = unpack(type, data)
        if isinstance(message, GameUpdate):
            print(f"{message.type}\n{json.dumps(message.data, sort_keys=True, indent=2)}\n")
            if message.type == "player.joined":
                self.scene.on_player_joined(
                    message.data["player.id"],
                    message.data["player.pos"])
            elif message.type == "player.left":
                self.scene.on_player_left(message.data["player.id"])
            elif message.type == "set.player.id":
                self.scene.set_player_id(message.data["player.id"])
            else:
                print(f"Unknown game update type {message.type}")
        elif isinstance(message, PlayerMoveAction):
            self.scene.on_player_moved(message.player_id, message.dx, message.dy)
        else:
            print(f"Unknown message type {type(message)}")

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        print("connection closed.")
        self.scene.on_close and self.scene.on_close()


class BubbleScene(Scene):
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
        self.client = GameClient(loop=loop, serializer=serializer)
        self.client.scene = self

    def connect(self, host, port):
        self.client.loop.create_task(self.client.connect(host=host, port=port))

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
            message = PlayerMoveAction(self.id, dx, dy)
            message.send(self.client)

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

    # network updates ================================================================================================

    def set_player_id(self, player_id: int):
        self.id = player_id

    def on_player_joined(self, player_id: int, player_pos: (int, int)):
        self.players[player_id] = player_pos

    def on_player_left(self, player_id: int):
        del self.players[player_id]

    def on_player_moved(self, player_id: int, dx: int, dy: int):
        player_x, player_y = self.players[player_id]
        player_x += dx
        player_y += dy
        self.players[player_id] = (player_x, player_y)

        if player_id == self.id:
            self.camera.world_x += dx
            self.camera.world_y += dy


def main(host: str="0.0.0.0"):
    import uvloop
    loop = uvloop.new_event_loop()

    width, height = 1024, 768
    camera = Camera()

    scene = BubbleScene(camera, "network-bubble-scene", loop=loop)
    scene.connect(host, 8888)

    window = Window(width=width, height=height, scenes=[scene], loop=loop)
    window.run()
