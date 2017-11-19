from math import cos, sin
from numbers import Real
from typing import NamedTuple, Tuple, Union

ANNOTATIONS_NAME = "_rapid_annotations"
_symbols = {}

__all__ = [
    "Vec2", "Sentinel",
    "get_annotations", "has_annotations",
    "missing"
]


class Vec2(NamedTuple):
    x: Real = 0
    y: Real = 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}{list(self)}>"

    def copy(self) -> "Vec2":
        return Vec2(*self)

    @staticmethod
    def of(vec2: Tuple[Real, Real]) -> "Vec2":
        vec2 = tuple(vec2)
        assert len(vec2) == 2
        return Vec2(*vec2)

    def __add__(self, other: Union["Vec2", Real]) -> "Vec2":
        if isinstance(other, Real):
            return Vec2(self.x + other, self.y + other)
        else:
            return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Union["Vec2", Real]) -> "Vec2":
        if isinstance(other, Real):
            return Vec2(self.x - other, self.y - other)
        else:
            return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Union["Vec2", Real]) -> "Vec2":
        if isinstance(other, Real):
            return Vec2(self.x * other, self.y * other)
        else:
            return Vec2(self.x * other.x, self.y * other.y)

    def __div__(self, other: Union["Vec2", Real]) -> "Vec2":
        if isinstance(other, Real):
            return Vec2(self.x / other, self.y / other)
        else:
            return Vec2(self.x / other.x, self.y / other.y)

    def rotate_about(self, theta: Real) -> "Vec2":
        c, s = cos(theta), sin(theta)
        return Vec2(
            self.x * c - self.y * s,
            self.x * s + self.y * c
        )


Vec2.Zero = Vec2(0, 0)


class Sentinel:
    """Simple string-based placeholders for missing or special values.

    Names are unique, and instances are re-used for the same name:

    .. code-block:: pycon

        >>> from rapid.util import Sentinel
        >>> empty = Sentinel("empty")
        >>> empty
        <Sentinel[empty]>
        >>> same_token = Sentinel("empty")
        >>> empty is same_token
        True

    This removes the need to import the same signal or placeholder value everywhere; two modules can create
    ``Sentinel("some-value")`` and refer to the same object.  This is especially helpful where ``None`` is a possible
    value, and so can't be used to indicate omission of an optional parameter.

    Implements \_\_repr\_\_ to render nicely in function signatures.  Standard object-based sentinels:

    .. code-block:: pycon

        >>> missing = object()
        >>> def some_func(optional=missing):
        ...     pass
        ...
        >>> help(some_func)
        Help on function some_func in module __main__:

        some_func(optional=<object object at 0x7f0f3f29e5d0>)

    With the Sentinel class:

    .. code-block:: pycon

        >>> from rapid.util import Sentinel
        >>> missing = Sentinel("Missing")
        >>> def some_func(optional=missing):
        ...     pass
        ...
        >>> help(some_func)
        Help on function some_func in module __main__:

        some_func(optional=<Sentinel[Missing]>)

    :param str name: The name for this sentinel.
    """
    def __new__(cls, name, *args, **kwargs):
        name = name.lower()
        sentinel = _symbols.get(name, None)
        if sentinel is None:
            sentinel = _symbols[name] = super().__new__(cls)
        return sentinel

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Sentinel[{}]>".format(self.name)


def has_annotations(obj) -> bool:
    return hasattr(obj, ANNOTATIONS_NAME)


def get_annotations(obj) -> dict:
    """
    .. code-block:: pycon

        >>> import random
        >>> def singleton(func):
        ...     get_annotations(func)["singleton"] = True
        ...     return func
        ...
        >>> @singleton
        >>> def rng():
        ...     return random.Random()
        ...
        >>> assert get_annotations(rng)["singleton"]
    """
    if not has_annotations(obj):
        setattr(obj, ANNOTATIONS_NAME, {})
    return getattr(obj, ANNOTATIONS_NAME)

missing = Sentinel("Missing")
