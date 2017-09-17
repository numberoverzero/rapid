from typing import Callable, List, Optional, Tuple
import pyglet

Viewport = Tuple[int, int]


class Drawable:
    def on_draw(self, scene: "Scene") -> None:
        raise NotImplementedError()

    def on_update(self, dt: float) -> None:
        pass

    @classmethod
    def of(cls, batch: pyglet.graphics.Batch) -> "Drawable":
        return BatchDrawable(batch)


class BatchDrawable(Drawable):
    def __init__(self, batch: pyglet.graphics.Batch) -> None:
        self.batch = batch

    def on_draw(self, scene: "Scene") -> None:
        with scene.camera:
            self.batch.draw()


class Camera:
    _world_bounds: Tuple[int, int, int, int]
    _world_x: float
    _world_y: float
    _viewport: Viewport
    clipping: Tuple[int, int]
    _zoom: float

    def __init__(
            self,
            world_x: float=0, world_y: float=0, zoom: float=1.0,
            viewport: Viewport=(1920, 1080),
            clipping: Tuple[int, int]=(0, 1)):
        self._world_x, self._world_y = world_x, world_y
        self._zoom = zoom
        self._viewport = viewport
        self.clipping = clipping
        self._recalculate_ortho()

    @property
    def world_bounds(self) -> Tuple[int, int, int, int]:
        return self._world_bounds

    @property
    def world_x(self) -> float:
        return self._world_x

    @world_x.setter
    def world_x(self, value: float) -> None:
        original = self._world_x
        self._world_x = value
        if original != value:
            self._recalculate_ortho()

    @property
    def world_y(self) -> float:
        return self._world_y

    @world_y.setter
    def world_y(self, value: float) -> None:
        original = self._world_y
        self._world_y = value
        if original != value:
            self._recalculate_ortho()

    @property
    def world_pos(self) -> Tuple[float, float]:
        return self.world_x, self.world_y

    @world_pos.setter
    def world_pos(self, value: Tuple[float, float]) -> None:
        self._world_x, self._world_y = value
        self._recalculate_ortho()

    @property
    def viewport(self) -> Viewport:
        return self._viewport

    @viewport.setter
    def viewport(self, value: Viewport) -> None:
        original = self._viewport
        self._viewport = value
        if original != value:
            self._recalculate_ortho()

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        original = self._zoom
        self._zoom = value
        if original != value:
            self._recalculate_ortho()

    def _recalculate_ortho(self) -> None:
        width, height = self.viewport
        x, y = self.world_x, self.world_y
        zoom = self.zoom

        width /= zoom
        height /= zoom

        left = x - width / 2
        right = left + width
        bottom = y - height / 2
        top = bottom + height

        self._world_bounds = int(left), int(right), int(bottom), int(top)

    def __enter__(self):
        pyglet.gl.glViewport(0, 0, *self.viewport)

        pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
        pyglet.gl.glPushMatrix()
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glOrtho(*self.world_bounds, *self.clipping)

        pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
        pyglet.gl.glPushMatrix()
        pyglet.gl.glLoadIdentity()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
        pyglet.gl.glPopMatrix()
        pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
        pyglet.gl.glPopMatrix()

    def to_world_coords(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        left, _, bottom, _ = self.world_bounds
        x = left + (screen_x / self.zoom)
        y = bottom + (screen_y / self.zoom)
        return int(x), int(y)

    def on_update(self, dt: float) -> None:
        pass


SceneCloseHandler = Callable[["Scene"], None]


class Scene:
    camera: Camera
    components: List[Drawable]
    name: str
    on_close: Optional[SceneCloseHandler]

    def __init__(self,
                 camera: Camera, name: str="unnamed-scene",
                 on_close: Optional[SceneCloseHandler]=None) -> None:
        self.components = []  # type: List[Drawable]
        self.camera = camera
        self.name = name
        self.on_close = on_close

    def on_update(self, dt: float) -> None:
        self.camera.on_update(dt)
        for component in self.components:
            component.on_update(dt)

    def on_draw(self):
        for component in self.components:
            component.on_draw(self)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close and self.on_close(self)

    def on_key_release(self, symbol, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_enter(self, x, y):
        pass

    def on_mouse_leave(self, x, y):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass

    def on_resize(self, width, height):
        self.camera.viewport = (width, height)

    def on_text(self, text):
        pass

    def on_text_motion(self, motion):
        pass

    def on_text_motion_select(self, motion):
        pass


def debug_scene(scene: Scene) -> None:
    with scene.camera:
        pyglet.gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        label = pyglet.text.Label(
            f"<scene:{scene.name}>",
            font_name="Times New Roman", font_size=36,
            color=(255, 255, 255, 255),
            x=0, y=-150,
            anchor_x="center", anchor_y="center")
        label.draw()
        markers = [
            pyglet.text.Label(
                f"{t}",
                font_name="Droid Sans Mono", font_size=36,
                color=(255, 255, 255, 255),
                x=x, y=y, anchor_x="center", anchor_y="center")
            for (t, x, y) in [(1, 50, 50), (2, -50, 50), (3, -50, -50), (4, 50, -50)]
        ] + [
            pyglet.text.Label(
                f"+",
                font_name="Droid Sans Mono", font_size=36,
                color=(255, 255, 255, 255),
                x=0, y=0, anchor_x="center", anchor_y="center")
        ]
        for marker in markers:
            marker.draw()
        w, h = scene.camera.viewport
        pyglet.graphics.draw(
            4, pyglet.gl.GL_LINES,
            ("v2f", (-w / 2, 0, w / 2, 0, 0, -h / 2, 0, h / 2))
        )
        pyglet.graphics.draw(
            4, pyglet.gl.GL_LINES,
            ("v2f", (
                -w / 2, scene.camera.world_y,
                w / 2, scene.camera.world_y,
                scene.camera.world_x, -h / 2,
                scene.camera.world_x, h / 2)),
            ("c3B", [255, 0, 0] * 2 + [0, 0, 255] * 2)
        )
