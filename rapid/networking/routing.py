import inspect
from typing import Any, Callable, Dict, Tuple, Type
from .clients import Client
from .messages import MessageProtocol
from ..util import get_annotations, has_annotations

ROUTING_ANNOTATIONS = "rapid.networking.routing"
MessageHandler = Callable[[Any], Any]


class RoutingClient(Client):
    def __init__(self, scene, unpack: Callable[[int, bytes], Tuple[Any, Any]], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.scene = scene
        self._routes = self._build_routes(scene)
        self._unpack = unpack

    # noinspection PyMethodMayBeStatic
    def _build_routes(self, scene) -> Dict[Type[Any], MessageHandler]:
        routes = {}
        assert not isinstance(scene, type)  # must be an instance of the annotated class, not the class itself
        for func, message_cls, *_ in get_routing_annotations_for(scene):
            assert message_cls not in routes
            routes[message_cls] = func
        return routes

    def on_connection_made(self, protocol: MessageProtocol) -> None:
        pass

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
        message_cls, message = self._unpack(type, data)
        handler = self._routes.get(message_cls, None)
        if handler:
            handler(message)

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        pass


def handle(message_cls: Type[Any], *args, **kwargs):
    """
    .. code-block:: pycon

        >>> from rapid import Scene
        >>> from rapid.networking.routing import RoutingClient, handle
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
        ...     return msg
        ...
        >>> scene = MyScene()
        >>> client = RoutingClient(scene, unpack)
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
