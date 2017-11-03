"""
High-level components for quick prototyping on top of rapid.
Single-scene games
"""
import pyglet.gl
from pyglet.graphics import Batch
from rapid import Drawable, key
from rapid.networking.routing import handle
from skeleton.game import Game
from skeleton.networking import AbstractMessage, Server, attach_routing_client

__all__ = [
    "AbstractMessage", "Game", "Server",
    "rectangle",

    # re-imports
    "handle", "key",
]


# TODO sprite class to simplify vert updates
def rectangle(left, right, bottom, top, batch=None):
    if batch is None:
        batch = Batch()
    batch.add(
        4, pyglet.gl.GL_TRIANGLE_STRIP, None,
        # ("v2i", (-50, -50, 50, -50, -50, 50, 50, 50)),
        ("v2i", (left, bottom, right, bottom, left, top, right, top)),
        ("c3B", (255, 0, 0) * 4)
    )
    return Drawable.of(batch)
