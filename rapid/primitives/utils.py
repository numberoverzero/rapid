from pyglet.gl import (
    GL_POINTS,
    GL_LINES,
    GL_LINE_LOOP,
    GL_LINE_STRIP,
    GL_TRIANGLES,
    GL_TRIANGLE_STRIP,
    GL_TRIANGLE_FAN,
    GL_QUADS,
    GL_QUAD_STRIP,
    GL_POLYGON,
)
from typing import Tuple, Union
import enum


class GLMode(enum.Enum):
    Points = ("points", GL_POINTS)
    Lines = ("lines", GL_LINES)
    LineLoop = ("line_loop", GL_LINE_LOOP)
    LineStrip = ("line_strip", GL_LINE_STRIP)
    Triangles = ("triangles", GL_TRIANGLES)
    TriangleStrip = ("triangle_strip", GL_TRIANGLE_STRIP)
    TriangleFan = ("triangle_fan", GL_TRIANGLE_FAN)
    Quads = ("quads", GL_QUADS)
    QuadStrip = ("quadstrip", GL_QUAD_STRIP)
    Polygon = ("polygon", GL_POLYGON)

    def __init__(self, friendly_name: str, gl_mode: int) -> None:
        self.friendly_name = friendly_name
        self.gl_mode = gl_mode


class Vec2:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def zero() -> "Vec2":
        return Vec2(0, 0)

    def __iter__(self):
        return iter((self.x, self.y))

    @property
    def xy(self) -> Tuple[float, float]:
        return self.x, self.y

    @xy.setter
    def xy(self, xy: Tuple[float, float]) -> None:
        self.x, self.y = xy

    @property
    def yx(self) -> Tuple[float, float]:
        return self.y , self.x

    @yx.setter
    def yx(self, yx: Tuple[float, float]) -> None:
        self.y, self.x = yx

    def __getitem__(self, item: Union[int, slice]) -> Union[float, Tuple[float, float]]:
        return self.xy[item]

    def __setitem__(self, key: Union[int, slice], value: Union[float, Tuple[float, float]]) -> None:
        if isinstance(key, int):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
            else:
                raise ValueError(f"Unknown key {key}")
        else:
            t = [self.x, self.y]
            t[key] = value
            self.xy = t

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)
