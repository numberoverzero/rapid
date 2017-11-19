from typing import TypeVar, Any, Type, Dict, Union, Tuple, Optional

from ..util import Vec2
from ._eval import EvalContext

T = TypeVar("T")


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
        self.handlers = {}
        if default_handlers:
            add_default_handlers(self)

    def parse(self, value: Any, type: Type[T], force: bool=False) -> T:
        assert type in self.handlers, f"Unknown type {type!r}"
        if value is None:
            # noinspection PyTypeChecker
            return None
        if isinstance(value, type) and not force:
            return value
        value = self.eval_context.evaluate(str(value))
        return self.handlers[type](value)


def add_default_handlers(parser: Parser):
    for type in [float, int, str, list]:
        parser.handlers[type] = type
    parser.handlers[Vec2] = lambda x: Vec2(
        parser.parse(x[0], float),
        parser.parse(x[1], float)
    )


class Template:
    """Specifies a set of variables and their types, optionally providing default values.

    Templates are used to build a Parser which exposes those variables.

    .. code-block:: python

        >>> from rapid.parsing import Template
        >>> from rapid import Vec2
        >>> variable_types = {"center": Vec2, "width": float, "height": float}
        >>> defaults = {"width": "125/6"}
        >>> template = Template(
        ...     name="rectangle",
        ...     local_variable_types=variable_types,
        ...     local_defaults=defaults
        ... )
        >>> parser = template.build_parser(
        ...     variables={
        ...         "height": "125 ** 0.5",
        ...         "center": [-72, 72],
        ...     },
        ... )
        >>> parser.eval_context.whitelisted_attribute_names.update({"x", "y"})
        >>> parser.parse("center.x - width * 6 / 2", float)
        -134.5

    """
    name: str
    variable_types: Dict[str, Type]
    variable_defaults: Dict[str, Any]

    def __init__(
            self, *, name: str,
            local_variable_types: Dict[str, Union[Type, Tuple[T]]],
            local_defaults: Dict[str, Any]) -> None:
        self.name = name
        self._local_types = self.variable_types = local_variable_types
        self._local_defaults = self.variable_defaults = local_defaults

    def derive_from(self, base: "Template") -> None:
        self.variable_types = {
            **base.variable_types,
            **self._local_types
        }
        self.variable_defaults = {
            **base.variable_defaults,
            **self._local_defaults
        }

    def build_parser(
            self, *,
            variables: Dict[str, Any],
            bootstrap_parser: Optional[Parser]=None) -> Parser:
        """Create a new rapid.parsing.EvalContext with the template's variables bound.

        Because the template's variables may need to be parsed, another parser is necessary to bootstrap
        the process.  If you do not provide one, a default rapid.parsing.Parser is used with no exposed variables.
        You can use the bootstrap_parser to eg. inject config or provide custom type mappings.

        :param variables:
            Dict of values or templates to construct the new Parser from.
            If you do not provide a variable, the Template's default will be used instead.
            If the template does not define a default for a missing variable, build_parser will fail.
        :param bootstrap_parser:
            An optional rapid.parsing.Parser used to evaluate the template variables.
        :return:
            A new rapid.parsing.EvalContext with the Template's variables exposed.
        """
        raw_parser_variables = {
            **self.variable_defaults,
            **variables
        }
        required_variables = set(self.variable_types.keys())
        provided_variables = set(raw_parser_variables.keys())

        extra_variables = provided_variables - required_variables
        missing_variables = required_variables - provided_variables
        if missing_variables:
            raise ValueError(f"variables is missing required keys {missing_variables}")
        if extra_variables:
            raise ValueError(f"variables contains extra keys {extra_variables}")

        bootstrap_parser = bootstrap_parser or _BOOTSTRAP_PARSER
        required_handlers = set(self.variable_types.values())
        provided_handlers = set(bootstrap_parser.handlers.keys())
        missing_handlers = required_handlers - provided_handlers
        if missing_handlers:
            raise ValueError(f"bootstrap_parser can't parse required types {missing_handlers}")

        # run each of the parser variables through the bootstrap parser
        exposed_variables = {
            name: bootstrap_parser.parse(value, self.variable_types[name])
            for name, value in raw_parser_variables.items()
        }

        return Parser(eval_context=EvalContext(exposed_variables=exposed_variables))


_BOOTSTRAP_PARSER = Parser(
    eval_context=EvalContext(),
    default_handlers=True
)
