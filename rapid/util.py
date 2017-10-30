ANNOTATIONS_NAME = "_rapid_annotations"
_symbols = {}


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
