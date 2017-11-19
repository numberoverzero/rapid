from typing import Any, Callable, Dict, Generic, Optional, TypeVar

import pymunk

from ..parsing import Parser
from ..util import Vec2, missing

__all__ = [
    "body_factory", "shape_factory",
    "build_body", "build_shape",
]

ShapeClass = TypeVar("ShapeClass", pymunk.Circle, pymunk.Segment, pymunk.Poly)


shape_arguments = {
    pymunk.Circle: {
        "required": {
            "radius": float
        },
        "optional": {
            "offset": Vec2
        }
    },
    pymunk.Segment: {
        "required": {
            "a": Vec2,
            "b": Vec2,
            "radius": float
        }, "optional": {},
    },
    pymunk.Poly: {
        "required": {
            "vertices": (list, Vec2)
        }, "optional": {},
    }
}


def guard_body_type(body_type: int) -> None:
    if body_type not in {pymunk.Body.DYNAMIC, pymunk.Body.KINEMATIC, pymunk.Body.STATIC}:
        raise ValueError(f"Unrecognized body_type {body_type}")


def build_body(
        body_type: int,
        position: Optional[Vec2]=None,
        mass: Optional[float]=None,
        moment: Optional[float]=None) -> pymunk.Body:
    """Create a new pymunk.Body

    Remember that mass and moment are overwritten when you add shapes to the body.

    :param body_type:
        One of pymunk.Body.DYNAMIC, pymunk.Body.KINEMATIC, pymunk.Body.STATIC
    :param position:
        Vec2 for initial position.  Defaults to pymunk's default position.
    :param mass:
        Body mass.  Defaults to pymunk's default body mass.
    :param moment:
        Body moment.  Defaults to pymunk's default body moment.
    :return:
        A new pymunk.Body with no shapes attached.
    """
    guard_body_type(body_type)
    body = pymunk.Body(body_type=body_type)
    if position is not None:
        body.position = position
    if mass is not None:
        body.mass = mass
    if moment is not None:
        body.moment = moment
    return body


def body_factory(
        body_type: int,
        position: Optional[Any]=None,
        mass: Optional[Any]=None,
        moment: Optional[Any]=None) -> Callable[[Parser], pymunk.Body]:
    """Returns a function that can be called to create a new pymunk.Body using attribute templates

    .. code-block:: pycon

        >>> import pymunk
        >>> from rapid.physics import body_factory
        >>> from rapid.parsing import EvalContext, Parser, whitelist_common_attribute_names
        >>> parser = Parser(eval_context=EvalContext(
        ...     exposed_variables={
        ...         "x": 7,
        ...         "y": 11
        ...     }
        ... ))
        >>> whitelist_common_attribute_names(parser)
        >>> static_factory = body_factory(
        ...     pymunk.Body.STATIC,
        ...     position=[20, 70],
        ...     mass="x**2", moment="y**2"
        ... )
        >>> body = static_factory(parser, None)
        >>> body.mass, body.moment, body.position
        (49.0, 121.0, (20, 70))


    :param body_type:
        One of pymunk.Body.DYNAMIC, pymunk.Body.KINEMATIC, pymunk.Body.STATIC
    :param position:
        An optional mass value or template to apply to the body.
        If you provide a tuple, list, or Vec2, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :param mass:
        An optional mass value or template to apply to the body.
        If you provide a float, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :param moment:
        An optional moment value or template to apply to the body.
        If you provide a float, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :return:
        A function that takes a rapid.parsing.Parser and returns new pymunk.Body with no shapes attached.
    """
    guard_body_type(body_type)

    def new_body(parser: Parser) -> pymunk.Body:
        """Create a new pymunk.Body

        If this factory's mass and moment are templates, the parser will be used to eval them with its
        exposed variables.

        :param parser:
            rapid.parser.Parser that exposes variables used in any attribute templates.
        :return:
            A new pymunk.Body with no shapes attached.
        """
        return build_body(
            body_type,
            position=parser.parse(position, Vec2),
            mass=parser.parse(mass, float),
            moment=parser.parse(moment, float)
        )
    return new_body


def build_shape(
        shape_cls: Generic[ShapeClass], shape_definition: Dict[str, Any],
        body: Optional[pymunk.Body]=None,
        mass: Optional[float]=None,
        elasticity: Optional[float]=None,
        friction: Optional[float]=None) -> ShapeClass:
    """Create a new pymunk.Shape, optionally attached to the given pymunk.Body

    You can attach the shape to a body later with ``shape.body = body``.

    :param shape_cls:
        One of pymunk.Circle, pymunk.Segment, or pymunk.Poly
    :param shape_definition:
        A dict of values passed to the shape's constructor.
        Optional values that aren't provided in the shape_definition use pymunk's defaults.
    :param body:
        An optional pymunk.Body to attach this shape to.  By default doesn't attach to a body.
    :param mass:
        Shape mass.  Defaults to pymunk's default shape mass.
    :param elasticity:
        Shape elasticity.  Defaults to pymunk's default shape elasticity.
    :param friction:
        Shape friction.  Defaults to pymunk's default shape friction.
    :return:
        A new pymunk.Shape of the specified type
    """
    shape = shape_cls(body=body, **shape_definition)
    if mass is not None:
        shape.mass = mass
    if elasticity is not None:
        shape.elasticity = elasticity
    if friction is not None:
        shape.friction = friction
    return shape


def shape_factory(
        shape_cls: Generic[ShapeClass], shape_definition: Dict[str, Any],
        mass: Optional[Any]=None,
        elasticity: Optional[Any]=None,
        friction: Optional[Any]=None) -> Callable[[Parser, Optional[pymunk.Body]], ShapeClass]:
    """Returns a function that can be called to create a new pymunk.Shape using attribute templates

    .. code-block:: pycon

        >>> import pymunk
        >>> from rapid.physics import shape_factory
        >>> from rapid.parsing import EvalContext, Parser
        >>> parser = Parser(eval_context=EvalContext(
        ...     exposed_variables={
        ...         "x": 7,
        ...         "y": 11
        ...     }
        ... ))
        >>> circle_factory = shape_factory(
        ...     pymunk.Circle,
        ...     {"offset": ['x', 'y'], "radius": "x+y"},
        ...     mass="x**2", elasticity="y**2", friction="y-x"
        ... )
        >>> c = circle_factory(parser, None)
        >>> c.radius
        18.0
        >>> c.mass, c.elasticity
        (49.0, 121.0)

    :param shape_cls:
        One of pymunk.Circle, pymunk.Segment, or pymunk.Poly
    :param shape_definition:
        A dict of attribute values or templates.
        For each value, if you provide the required type, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :param mass:
        An optional mass value or template to apply to the shape.
        If you provide a float, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :param elasticity:
        An optional elasticity value or template to apply to the shape.
        If you provide a float, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :param friction:
        An optional friction value or template to apply to the shape.
        If you provide a float, it will be used directly.
        If you provide a string, it will be eval'd with the given rapid.parsing.Parser
    :return:
        A function that takes a rapid.parsing.Parser and returns new pymunk.Shape with no shapes attached.
    """
    argument_types = shape_arguments[shape_cls]
    required_args = set(argument_types["required"].keys())
    optional_args = set(argument_types["optional"].keys())
    provided_args = set(shape_definition.keys())
    extra_args = provided_args - required_args - optional_args
    missing_args = required_args - provided_args
    if missing_args:
        raise ValueError(f"shape_definition is missing required arguments {missing_args}")
    if extra_args:
        raise ValueError(f"shape_definition contains extra arguments {extra_args}")

    def parse(parser, type, value):
        if isinstance(type, tuple):
            assert type[0] is list
            value = parser.parse(value, type[0])
            value = [parser.parse(x, type[1]) for x in value]
        else:
            value = parser.parse(value, type)
        return value

    def new_shape(parser: Parser, body: Optional[pymunk.Body]=None) -> ShapeClass:
        """Create a new pymunk.Shape

        If any of this factory's shape_definitions or mass, elasticity, or friction are templates,
        the parser will be used to eval them with its exposed variables.

        :param parser:
            rapid.parser.Parser that exposes variables used in any attribute templates.
        :param body:
            An optional pymunk.Body to attach the body to.
        :return:
            A new pymunk.Shape of the specified type
        """
        computed_definition = {}
        for name, type in argument_types["required"].items():
            value = shape_definition[name]
            computed_definition[name] = parse(parser, type, value)
        for name, type in argument_types["optional"].items():
            value = shape_definition.get(name, missing)
            if value is missing:
                continue
            computed_definition[name] = parse(parser, type, value)

        return build_shape(
            shape_cls, computed_definition,
            body=body,
            mass=parser.parse(mass, float),
            elasticity=parser.parse(elasticity, float),
            friction=parser.parse(friction, float)
        )
    return new_shape
