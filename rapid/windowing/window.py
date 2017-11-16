import asyncio
import uvloop
import pyglet
from typing import List, Optional
from .scene import Scene


class Window(pyglet.window.Window):
    scenes: List[Scene]
    _closing: bool = False

    def __init__(self, *args, scenes=None, loop=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.scenes = []
        for scene in (scenes or []):
            self.add_scene(scene)

        if loop is None:
            loop = uvloop.new_event_loop()
        self.loop = loop
        self.clock = pyglet.clock.Clock()

    @property
    def scene(self) -> Optional[Scene]:
        if not self.scenes:
            return None
        return self.scenes[-1]

    def add_scene(self, scene: Scene):
        # TODO handle non-active scene additions
        assert not scene.window

        scene.window = self
        self.scenes.append(scene)

        self.on_scene_change()

    def remove_scene(self, scene: Scene):
        # TODO handle non-active scene removals
        assert scene is self.scene
        assert scene.window is self

        scene.on_close()
        scene.window = None
        self.scenes.pop(-1)

        self.on_scene_change()

    def on_scene_change(self):
        if self.scene:
            self.set_caption(self.scene.name)
            self.on_resize(self.width, self.height)
        if not self.scene:
            self.on_close()

    def on_update(self, dt: float) -> None:
        self.scene.on_update(dt)

    def run(self) -> None:
        async def pyglet_update(interval: float):
            self.clock.schedule_interval(self.on_update, interval * 2)
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

    # pyglet.window.Window ============================================================================================
    # Forward to the current scene

    def on_close(self):
        if self._closing:
            return
        self._closing = True
        while self.scene:
            self.remove_scene(self.scene)
        super().on_close()

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
        if self._closing:
            return
        self.scene.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        """A key on the keyboard was released."""
        if self._closing:
            return
        self.scene.on_key_release(symbol, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """The mouse was moved with one or more mouse buttons pressed."""
        if self._closing:
            return
        self.scene.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_enter(self, x, y):
        """The mouse was moved into the window."""
        if self._closing:
            return
        self.scene.on_mouse_enter(x, y)

    def on_mouse_leave(self, x, y):
        """The mouse was moved outside of the window."""
        if self._closing:
            return
        self.scene.on_mouse_leave(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        """The mouse was moved with no buttons held down."""
        if self._closing:
            return
        self.scene.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        """A mouse button was pressed (and held down)."""
        if self._closing:
            return
        self.scene.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        """A mouse button was released."""
        if self._closing:
            return
        self.scene.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """The mouse wheel was scrolled."""
        if self._closing:
            return
        self.scene.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_resize(self, width, height):
        """The window was resized."""
        if self._closing:
            return
        self.scene.on_resize(width, height)

    def on_text(self, text):
        """The user input some text."""
        if self._closing:
            return
        self.scene.on_text(text)

    def on_text_motion(self, motion):
        """The user moved the text input cursor."""
        if self._closing:
            return
        self.scene.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        """The user moved the text input cursor while extending the selection."""
        if self._closing:
            return
        self.scene.on_text_motion_select(motion)
