"""
No rendering, simply calculates 2D verts for various geometry given a GLMode
"""
from typing import Generator
from math import cos, sin, pi

from .util import GLMode
from ..util import Vec2


def rectangle(
        center: Vec2,
        width: float, height: float,
        rotation: float,
        mode: GLMode) -> Generator[Vec2, None, None]:
    """Generate the necessary Vec2 points to render a rectangle with the given mode.

    :param center: position of the rectangle's center
    :param width: width of the rectangle
    :param height: height of the rectangle
    :param rotation: Rotation in radians counterclockwise from x axis.
    :param mode: One of GLMode.Triangles, GLMode.Quads
    :return: Iterable of Vec2 coordinates for the given mode.
    """
    verts = _rect_vertices(center=center, width=width, height=height, theta=rotation)
    if mode is GLMode.Triangles:
        v1, v2, v3, v4 = verts
        yield from (v1, v2, v3)
        yield from (v3, v4, v1)
    elif mode is GLMode.Quads:
        yield from verts
    else:
        raise ValueError(f"Invalid mode {mode!r}")


def circle(center: Vec2, r: float, resolution: int, mode: GLMode) -> Generator[Vec2, None, None]:
    """Generate the necessary Vec2 points to render a circle with the given mode.

    Note that the number of yielded Vec2s will exceed ``resolution``, which is the number of points on
    the outside of the circle.  For example, GLMode.TriangleFan will return resolution + 2 points:
    (resolution + 1 for the center, 1 to close the circle with the first vertex)

    :param center: position of the circle's center
    :param r: radius of the circle
    :param resolution: number of points on the outer edge of the circle.
    :param mode: One of GLMode.Triangles, GLMode.TriangleFan, GLMode.TriangleStrip, GLMode.Polygon
    :return: Iterable of Vec2 coordinates for the given mode.
    """
    return ellipse(center=center, a=r, b=r, resolution=resolution, mode=mode)


def ellipse(center: Vec2, a: float, b: float, resolution: int, mode: GLMode) -> Generator[Vec2, None, None]:
    """Generate the necessary Vec2 points to render an ellipse with the given mode.

    To generate vertices for a circle, pass a = b = radius.

    Note that the number of yielded Vec2s will exceed ``resolution``, which is the number of points on
    the outside of the ellipse.  For example, GLMode.TriangleFan will return resolution + 2 points:
    (resolution + 1 for the center, 1 to close the ellipse with the first vertex)

    :param center: position of the ellipse's center
    :param a: horizontal radius of the ellipse
    :param b: vertical radius of the ellipse
    :param resolution: number of points on the outer edge of the ellipse.
    :param mode: One of GLMode.Triangles, GLMode.TriangleFan, GLMode.TriangleStrip, GLMode.Polygon
    :return: Iterable of Vec2 coordinates for the given mode.
    """
    assert resolution > 2
    outer_verts = _ellipse_vertices(center=center, a=a, b=b, n=resolution)

    if mode is GLMode.Triangles:
        first = prev = next(outer_verts)
        for vert in outer_verts:
            yield from (center, prev, vert)
            prev = vert
        yield from (center, prev, first)
    elif mode is GLMode.TriangleFan:
        first = next(outer_verts)
        yield center
        yield first
        yield from outer_verts
        yield first
    elif mode is GLMode.TriangleStrip:
        first = next(outer_verts)
        yield first
        for vert in outer_verts:
            yield vert
            yield center
        yield first
    elif mode is GLMode.Polygon:
        yield from outer_verts
    else:
        raise ValueError(f"Invalid mode {mode!r}")


def _ellipse_vertices(center: Vec2, a: float, b: float, n: int) -> Generator[Vec2, None, None]:
    # triangles are wound CCW
    theta = 2 * pi / float(n)
    c, s = cos(theta), sin(theta)
    x, y = 1, 0
    cx, cy = center
    for i in range(n):
        yield Vec2(
            cx + a * x,
            cy + b * y,
        )
        x, y = c * x - s * y, s * x + c * y


def _rect_vertices(center: Vec2, width: float, height: float, theta: float) -> Generator[Vec2, None, None]:
    # triangles are wound CCW.  Triangles: (123, 341) Quads: (1234)
    # 4----3
    # |   /|
    # |  / |
    # | /  |
    # |/   |
    # 1----2
    w2, h2 = width/2, height/2
    cx, cy = center
    c, s = cos(theta), sin(theta)
    for x, y in [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]:
        yield Vec2(
            cx + (x * c - y * s),
            cy + (x * s + y * c),
        )
