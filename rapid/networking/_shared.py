import asyncio
import inspect
from typing import Any, Dict, Optional, Generic, Tuple, Type, TypeVar, Union
from ..util import get_annotations, has_annotations
_Transport_co = TypeVar("Transport_co", bound=Union[asyncio.Transport, asyncio.DatagramTransport])
ROUTING_ANNOTATIONS = "rapid.networking.routing"

__all__ = [
    "AddrInfo", "MessageHandler", "MessageProtocol",
    "build_slices", "get_routing_annotations_for", "handle",
]


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


AddrInfo = Tuple[str, int]  # ("127.0.0.1", 8888)


class MessageHandler(Generic[_Transport_co]):
    def on_connection_made(self, protocol: "MessageProtocol[_Transport_co]") -> None:
        raise NotImplementedError

    def on_recv_message(
            self, type: int, data: bytes,
            protocol: "MessageProtocol[_Transport_co]",
            addr: Optional[AddrInfo]=None) -> None:
        raise NotImplementedError

    def on_connection_lost(self, protocol: "MessageProtocol[_Transport_co]") -> None:
        raise NotImplementedError


class MessageProtocol(Generic[_Transport_co]):
    transport: Optional[_Transport_co]
    serializer: Any
    handler: MessageHandler[_Transport_co]

    def __init__(self, handler: MessageHandler[_Transport_co]):
        self.transport = None
        self.handler = handler

    def disconnect(self):
        if self.transport:
            self.transport.close()
            self.transport = None

    def send(self, type: int, data: bytes, addr: Optional[AddrInfo] = None) -> None:
        raise NotImplementedError
