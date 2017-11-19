from typing import Any, Callable, Type, TypeVar
from ._eval import EvalContext, PythonEvalContext, safe_eval
from ..util import Vec2
T = TypeVar("T")

__all__ = [
    "EvalContext", "PythonEvalContext", "safe_eval",
    "Parser"
]


class Parser:
    """
    Wraps an EvalContext with a set of post-eval type coercion, so that
    the EvalContext can be constrained to a small set of types.  For example,
    either of the inputs:
        ["3", "4"] or "[3, 4]"
    will be correctly parsed as a Vec2 wit the default handlers,
    which takes an input list and returns a Vec2 instance.
    """
    def __init__(self, eval_context: EvalContext, default_handlers=True) -> None:
        self.eval_context = eval_context
        self._handlers = {}
        if default_handlers:
            add_default_handlers(self)

    def add_handler(self, type: Type[T], handler: Callable[[Any], T]) -> None:
        self._handlers[type] = handler

    def parse(self, value: Any, type: Type[T], force: bool=False) -> T:
        assert type in self._handlers, f"Unknown type {type!r}"
        if value is None:
            # noinspection PyTypeChecker
            return None
        if isinstance(value, type) and not force:
            return value
        value = self.eval_context.evaluate(str(value))
        return self._handlers[type](value)


def add_default_handlers(parser: Parser):
    for type in [float, int, str, list]:
        parser.add_handler(type, type)
    parser.add_handler(Vec2, Vec2.of)
