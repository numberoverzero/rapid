"""
High-level components for quick prototyping on top of rapid.
Single-scene games
"""
from rapid import key
from skeleton.game import Game
from skeleton import net

__all__ = [
    "Game",
    "AbstractMessage", "Client", "Server",
    "key",
    "net"
]
