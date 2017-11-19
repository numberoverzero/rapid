"""
Support evaluation of a very limited subset of operations and literals.

EvalContext supports a subset of operations common across many languages,
while PythonEvalContext adds on Sets, Tuples, and the literals
True, False, and None.

.. code-block:: pycon

    >>> from rapid.parsing import EvalContext
    >>> Container = type("Container", (object,), {})
    >>> root = Container()
    >>> intermediate = Container()
    >>> root.first = intermediate
    >>> intermediate.second = "hello"
    >>> suffix = "world"
    >>>
    >>> ctx = EvalContext(
    ...     exposed_variables={"a": root, "suffix": suffix},
    ...     whitelisted_attribute_names={"first", "second"}
    ... )
    >>> with ctx as local_eval:
    ...     local_eval("a.first.second + ', ' + suffix")
    ...     local_eval("suffix[0]") + local_eval("suffix[-1]")
    'hello, world'
    'wd'

For one-off evaluation (or where your exposed variables change frequently),
use ``safe_eval``:

.. code-block:: pycon

    >>> from rapid.parsing import safe_eval
    >>> safe_eval(source="a * b", exposed_variables={"a": "!", "b": 3})
    '!!!'

As always, be very careful using eval (in any form) on unconstrained user
input.  This module has not been rigorously tested or reviewed.
"""
from typing import Any, Dict, Optional, Set
import ast
import operator

__all__ = ["EvalContext", "PythonEvalContext", "safe_eval"]

_un_ops = {
    ast.UAdd: operator.abs,
    ast.USub: operator.neg,
}
_bin_ops = {
    ast.Add: operator.add,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Mult: operator.mul,
    ast.Pow: operator.pow,
    ast.Sub: operator.sub,
}


def safe_eval(
        *, source: str,
        exposed_variables: Optional[Dict[str, Any]]=None,
        whitelisted_attribute_names: Optional[Set[str]]=None) -> Any:
    ctx = EvalContext(
        exposed_variables=exposed_variables,
        whitelisted_attribute_names=whitelisted_attribute_names)
    return ctx.evaluate(source)


class EvalContext:
    """Exposes a collection of variables and a subset of their attributes.

    The following operations are supported:
        unary operators:
            + (abs), - (negate)
        binary operators:
            +, -, *, /, //, %, **
        variable lookup (within the scope of provided variables)
        attribute lookup (whitelisted attribute names only)
        subscripts (without slices)
    The following literals are supported:
        numbers
        strings
        lists
        dicts
    """
    def __init__(
            self, *,
            exposed_variables: Optional[Dict[str, Any]]=None,
            whitelisted_attribute_names: Optional[Set[str]]=None) -> None:
        self.exposed_variables = exposed_variables or {}
        self.whitelisted_attribute_names = whitelisted_attribute_names or set()

    def __enter__(self):
        return self.evaluate

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def evaluate(self, source: str) -> Any:
        root = ast.parse(source=source, mode="eval").body
        return self._eval(root)

    def _eval(self, node: ast.AST) -> Any:
        # Literals
        if isinstance(node, ast.Num):  # "3"
            return node.n
        elif isinstance(node, ast.Str):  # "'3'"
            return node.s
        elif isinstance(node, ast.List):  # "[1, '2']"
            return [self._eval(x) for x in node.elts]
        elif isinstance(node, ast.Dict):  # "{'foo': "bar", 1: 2}"
            return {
                self._eval(key): self._eval(value)
                for key, value in zip(node.keys, node.values)
            }

        # Operators
        elif isinstance(node, ast.BinOp):  # "3 / 4"
            return _bin_ops[type(node.op)](self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # "-3" or "+4"
            return _un_ops[type(node.op)](self._eval(node.operand))

        # Whitelisted lookups
        elif isinstance(node, ast.Name):  # "center"
            obj_name = node.id
            try:
                return self.exposed_variables[obj_name]
            except KeyError:
                raise RuntimeError(f"Tried to access unknown variable {obj_name}")
        elif isinstance(node, ast.Attribute):  # "center.x"
            attr_name = node.attr
            if attr_name not in self.whitelisted_attribute_names:
                raise RuntimeError(f"Tried to access non-whitelisted attr {attr_name!r}")
            # can't just use node.value.id since this may not be an ast.Name,
            # but a chained value eg. "root.first.second"
            obj = self._eval(node.value)
            return getattr(obj, attr_name)

        # Subscripts
        elif isinstance(node, ast.Subscript):  # "x[2]"
            obj = self._eval(node.value)
            index = self._eval(node.slice)
            return obj[index]
        elif isinstance(node, ast.Index):  # second part of "x[2]"
            return self._eval(node.value)

        # Not supported
        else:  # "some_func()"
            raise TypeError(node)


class PythonEvalContext(EvalContext):
    """Exposes additional Python-specific nodes.

    Additional literals:
        sets
        tuples
        True, False, None
    Additional syntax:
        subscript slices (x[::-1])
    """
    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.NameConstant):  # "True"
            # This guard is a bit silly, but maybe some versions of Python add
            # an unexpected NameConstant that provides an escape mechanism?
            assert node.value in {True, False, None}
            return node.value
        elif isinstance(node, ast.Set):  # "{1, '2'}"
            return {self._eval(x) for x in node.elts}
        elif isinstance(node, ast.Tuple):  # "(1, None, '3')
            return tuple(self._eval(x) for x in node.elts)
        elif isinstance(node, ast.Slice):
            return slice(
                self._eval(node.lower),
                self._eval(node.upper),
                self._eval(node.step)
            )
        else:
            return super()._eval(node)
