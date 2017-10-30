import asyncio
import uvloop
import pyglet
from typing import List
from .scene import Scene


class Window(pyglet.window.Window):
    scenes: List[Scene]

    def __init__(self, *args, **kwargs):
        scenes = kwargs.pop("scenes", [])
        loop = kwargs.pop("loop", None)
        super().__init__(*args, **kwargs)

        self.scenes = scenes
        for scene in scenes:
            scene.window = self

        if loop is None:
            loop = uvloop.new_event_loop()
        self.loop = loop
        self.clock = pyglet.clock.Clock()

    @property
    def scene(self) -> Scene:
        return self.scenes[-1]

    def on_scene_close(self, scene: Scene):
        assert scene is self.scene  # TODO handle non-active scene closing
        self.scenes.pop(-1)
        scene.on_close()
        if not self.scenes:
            self.on_close()

    def on_update(self, dt: float) -> None:
        self.scene.on_update(dt)

    def run(self) -> None:
        async def pyglet_update(interval: float):
            self.clock.schedule_interval(self.on_update, interval)
            try:
                while not self.has_exit:
                    self.clock.tick()
                    self.on_draw()
                    self.dispatch_events()
                    await asyncio.sleep(interval, loop=self.loop)
                self.loop.stop()
            finally:
                self.clock.unschedule(self.on_update)

        self.loop.create_task(pyglet_update(1 / 120))
        self.loop.run_forever()

    # INHERITED FROM pyglet.window.Window ============================================================================
    # Forward to the current scene

    def on_close(self):
        if not self.scenes:
            super().on_close()
        while self.scenes:
            self.on_scene_close(self.scene)

    def on_draw(self):
        """The window contents must be redrawn."""
        self.switch_to()
        self.clear()
        self.scene.on_draw()
        self.flip()

    def on_expose(self):
        """A portion of the window needs to be redrawn."""
        self.on_draw()

    def on_key_press(self, symbol, modifiers):
        """A key on the keyboard was pressed (and held down)."""
        self.scene.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        """A key on the keyboard was released."""
        self.scene.on_key_release(symbol, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """The mouse was moved with one or more mouse buttons pressed."""
        self.scene.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_enter(self, x, y):
        """The mouse was moved into the window."""
        self.scene.on_mouse_enter(x, y)

    def on_mouse_leave(self, x, y):
        """The mouse was moved outside of the window."""
        self.scene.on_mouse_leave(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        """The mouse was moved with no buttons held down."""
        self.scene.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        """A mouse button was pressed (and held down)."""
        self.scene.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        """A mouse button was released."""
        self.scene.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """The mouse wheel was scrolled."""
        self.scene.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_resize(self, width, height):
        """The window was resized."""
        self.scene.on_resize(width, height)

    def on_text(self, text):
        """The user input some text."""
        self.scene.on_text(text)

    def on_text_motion(self, motion):
        """The user moved the text input cursor."""
        self.scene.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        """The user moved the text input cursor while extending the selection."""
        self.scene.on_text_motion_select(motion)
