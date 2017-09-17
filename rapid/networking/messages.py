from typing import Tuple, Optional, Dict
import asyncio


def _build_slices(segments: Tuple[Tuple[str, int], ...]) -> Dict[str, slice]:
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


class MessageSerializer:
    def __init__(self, type_size_bytes: int=1, data_size_bytes: int=2, byteorder: str="big") -> None:
        """

        :param type_size_bytes: number of bytes used to represent the message type
        :param data_size_bytes: number of bytes used to represent the size of the data
        :param byteorder: determines the byte order used to represent the integer
        """
        self.byteorder = byteorder
        self.type_size_bytes = type_size_bytes
        self.data_size_bytes = data_size_bytes
        self.fixed_slices = _build_slices((
            ("msg_type", type_size_bytes),
            ("msg_length", data_size_bytes)
        ))

    def pack(self, type: int, data: bytes) -> bytes:
        return b"".join((
            type.to_bytes(self.type_size_bytes, self.byteorder),
            len(data).to_bytes(self.data_size_bytes, self.byteorder),
            data
        ))

    def unpack(self, data: bytes) -> Tuple[Optional[Tuple[int, bytes]], bytes]:
        if len(data) < self.fixed_slices["_total"].stop:
            return None, data

        message_length = int.from_bytes(
            data[self.fixed_slices["msg_length"]],
            byteorder=self.byteorder
        )

        data_start = self.fixed_slices["_total"].stop
        data_stop = data_start + message_length
        if len(data) < data_stop:
            return None, data

        message_type = int.from_bytes(
            data[self.fixed_slices["msg_type"]],
            byteorder=self.byteorder
        )
        message_data = data[data_start: data_stop]

        return (message_type, message_data), data[data_stop:]


class MessageProtocol(asyncio.Protocol):
    buffer: bytes
    transport: Optional[asyncio.Transport]
    serializer: MessageSerializer

    def __init__(self, serializer: MessageSerializer, handler: "MessageHandler") -> None:
        self.buffer = b""
        self.transport = None
        self.serializer = serializer
        self.handler = handler

    def disconnect(self):
        if self.transport:
            self.transport.close()
            self.transport = None

    def send(self, type: int, data: bytes) -> None:
        assert self.transport
        packed = self.serializer.pack(type, data)
        self.transport.write(packed)

    # asyncio.Protocol ===============================================================================================

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.handler.on_connection_made(self)

    def data_received(self, data: bytes) -> None:
        self.buffer += data
        message, self.buffer = self.serializer.unpack(self.buffer)
        while message is not None:
            msg_type, msg_data = message
            self.handler.on_recv_message(self, msg_type, msg_data)
            message, self.buffer = self.serializer.unpack(self.buffer)

    def connection_lost(self, exc) -> None:
        self.transport = None
        self.handler.on_connection_lost(self)


class MessageHandler:
    def on_connection_made(self, protocol: MessageProtocol) -> None:
        raise NotImplementedError

    def on_recv_message(self, protocol: MessageProtocol, type: int, data: bytes) -> None:
        raise NotImplementedError

    def on_connection_lost(self, protocol: MessageProtocol) -> None:
        raise NotImplementedError
