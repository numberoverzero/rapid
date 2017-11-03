from rapid import Scene, Camera, Window
from skeleton.networking import attach_routing_client


class Game(Scene):
    def __init__(self, title="<GAME TITLE HERE>", screen_width=1024, screen_height=768):
        camera = Camera()
        super().__init__(camera, name=title)
        window = Window(width=screen_width, height=screen_height)
        window.add_scene(self)
        self.client = attach_routing_client(self)

    def run(self, host=None, port=None):
        if host and port:
            self.client.loop.create_task(self.client.connect(host=host, port=port))
        self.window.run()
