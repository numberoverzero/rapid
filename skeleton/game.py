from typing import Optional

from rapid.windowing import Camera, Scene, Window
from skeleton.net import Client


class Game(Scene):
    def __init__(
            self,
            host: Optional[str]=None, port: Optional[int]=None, mode: str="tcp",
            screen_width=1024, screen_height=768, title="<GAME TITLE HERE>"):
        camera = Camera()
        super().__init__(camera, name=title)
        window = Window(width=screen_width, height=screen_height)
        window.add_scene(self)
        if host is not None and port is not None:
            self.client = Client(self, host=host, port=port, mode=mode)
        else:
            self.client = None

    def run(self):
        if self.client:
            self.client.connect()
        self.window.run()
