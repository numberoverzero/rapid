import inspect
from typing import Any, Dict, Tuple, Type
from ..util import get_annotations, has_annotations
ROUTING_ANNOTATIONS = "rapid.networking.routing"


def build_slices(segments: Tuple[Tuple[str, int], ...]) -> Dict[str, slice]:
    end = 0
    slices = {}
    for i, (label, length) in enumerate(segments):
        if i == 0:
            start = 0
            end = length
        else:
            start = end  # previous segment's end point
            end += length
        slices[label] = slice(start, end)
    assert "_total" not in slices
    slices["_total"] = slice(0, end)
    return slices


def handle(message_cls: Type[Any], *args, **kwargs):
    """
    .. code-block:: pycon

        >>> from rapid.networking import tcp, handle
        >>> from rapid import Scene
        >>> class CustomMessageType:
        ...     def pack(self):
        ...         return b""
        ...     def unpack(self, data):
        ...         return
        ...
        >>> class MyScene(Scene):
        ...     @handle(CustomMessageType)
        ...     def on_my_message(self, message):
        ...         assert isinstance(message, CustomMessageType)
        ...
        >>> def unpack(type: int, data: bytes):
        ...     # TODO handle different types
        ...     msg = CustomMessageType()
        ...     msg.unpack(data)
        ...     return CustomMessageType, msg
        ...
        >>> scene = MyScene()
        >>> client = tcp.RoutingClient(scene, unpack)
        >>> scene.client = client

    """
    def annotate(func):
        _supported_messages(func).append((message_cls, args, kwargs))
        return func
    return annotate


def _supported_messages(func):
    annotations = get_annotations(func).setdefault(ROUTING_ANNOTATIONS, {})
    return annotations.setdefault("messages", [])


def get_routing_annotations_for(scene):
    functions = inspect.getmembers(scene, inspect.ismethod)
    for name, func in functions:
        if not has_annotations(func):
            continue
        for message_cls, args, kwargs in _supported_messages(func):
            yield func, message_cls, args, kwargs
