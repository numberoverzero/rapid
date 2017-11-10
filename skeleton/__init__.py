"""
High-level components for quick prototyping on top of rapid.
Single-scene games
"""
from rapid import key
from rapid.networking import handle
from skeleton.game import Game
from skeleton.net import AbstractMessage, Client, Server

__all__ = [
    "Game",
    "AbstractMessage", "Client", "Server",
    "handle", "key",
]
