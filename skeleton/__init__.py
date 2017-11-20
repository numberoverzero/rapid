"""
High-level components for quick prototyping on top of rapid.
Single-scene games
"""
from rapid import key
from skeleton import net
from skeleton.game import Game


__all__ = [
    "Game",
    "AbstractMessage", "Client", "Server",
    "key",
    "net"
]
