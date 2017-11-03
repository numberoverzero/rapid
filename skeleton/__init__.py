"""
High-level components for quick prototyping on top of rapid.
Single-scene games
"""
from rapid import key
from rapid.networking.routing import handle
from skeleton.game import Game
from skeleton.networking import AbstractMessage, Server

__all__ = [
    "AbstractMessage", "Game", "Server",

    # re-imports
    "handle", "key",
]
