from .builders import body_factory, shape_factory
from .world import World
from .loader import WorldLoader

__all__ = [
    "World", "WorldLoader",
    "load_world",
    "body_factory", "shape_factory",
]


def load_world(string: str, **global_variables) -> World:
    return WorldLoader().load(string, global_variables)

