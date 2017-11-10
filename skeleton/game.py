from rapid import Scene, Camera, Window
from skeleton.net import Client


class Game(Scene):
    def __init__(
            self,
            host: str, port: int, mode: str="tcp",
            screen_width=1024, screen_height=768, title="<GAME TITLE HERE>"):
        camera = Camera()
        super().__init__(camera, name=title)
        window = Window(width=screen_width, height=screen_height)
        window.add_scene(self)
        self.client = Client(self, host=host, port=port, mode=mode)

    def run(self):
        self.client.connect()
        self.window.run()
