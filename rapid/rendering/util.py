import enum
from typing import Generator, Iterable, NamedTuple, Tuple, overload

from pyglet.gl import (
    GL_LINES,
    GL_LINE_LOOP,
    GL_LINE_STRIP,
    GL_POINTS,
    GL_POLYGON,
    GL_QUADS,
    GL_QUAD_STRIP,
    GL_TRIANGLES,
    GL_TRIANGLE_FAN,
    GL_TRIANGLE_STRIP,
)

from ..util import Vec2


class GLMode(enum.Enum):
    Points = ("GL_POINTS", GL_POINTS)
    Lines = ("GL_LINES", GL_LINES)
    LineLoop = ("GL_LINE_LOOP", GL_LINE_LOOP)
    LineStrip = ("GL_LINE_STRIP", GL_LINE_STRIP)
    Triangles = ("GL_TRIANGLES", GL_TRIANGLES)
    TriangleStrip = ("GL_TRIANGLE_STRIP", GL_TRIANGLE_STRIP)
    TriangleFan = ("GL_TRIANGLE_FAN", GL_TRIANGLE_FAN)
    Quads = ("GL_QUADS", GL_QUADS)
    QuadStrip = ("GL_QUAD_STRIP", GL_QUAD_STRIP)
    Polygon = ("GL_POLYGON", GL_POLYGON)

    def __init__(self, gl_name: str, gl_mode: int) -> None:
        self.gl_name = gl_name
        self.gl_mode = gl_mode

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}[{self.gl_name}]>"


class Color(NamedTuple):
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}{list(self)}>"

    def copy(self) -> "Color":
        return Color(*self)

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return self.r, self.g, self.b

    @staticmethod
    def of(color: Tuple[int, int, int, int]) -> "Color":
        return Color(*color)


@overload
def flatten(it: Iterable[Vec2]) -> Generator[float, None, None]: ...


@overload
def flatten(it: Iterable[Color]) -> Generator[int, None, None]: ...


def flatten(it):
    """
    Flatten an iterable of Vec2 or Color into a single Iterable for use in a Batch add.

    .. code-block:: python

        def greyscale():
            for i in range(256):
                yield Color(i, i, i, 255)

        colors = tuple(flatten(greyscale()))
        assert len(colors) == 1024
        assert colors[3::4] == (255,) * 256
    """
    for each in it:
        yield from each
