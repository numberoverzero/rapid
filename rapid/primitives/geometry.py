"""
No rendering, simply calculates 2D verts for various geometry
"""
from typing import Generator, List, Tuple
from math import cos, sin, pi

from .utils import GLMode, Vec2
v2 = Vec2


def flatten(verts: List[Vec2]) -> Tuple[float, ...]:
    flattened = [0] * (2 * len(verts))
    for i, vert in enumerate(verts):
        flattened[0 + i * 2] = vert.x
        flattened[1 + i * 2] = vert.y
    return tuple(flattened)


def circle(cx: float, cy: float, r: float, n_points: int, mode: GLMode) -> List[Vec2]:
    assert n_points > 2
    assert mode in {GLMode.Triangles, GLMode.TriangleFan, GLMode.TriangleStrip}
    center = v2(cx, cy)
    verts = []

    if mode is GLMode.TriangleFan:
        verts.append(center)
        verts.extend(_circle_vertices(cx, cy, r, n_points))
        return verts
    else:
        raise ValueError("Unhandled")


def _circle_vertices(cx: float, cy: float, r: float, n_points: int) -> Generator[Vec2, None, None]:
    theta = 2 * pi
    c = cos(theta)
    s = sin(theta)

    x = r
    y = 0

    for i in range(n_points):
        yield v2(cx + x, cy + y)

        t = x
        x = c * x - s * y
        y = s * t + c * y
