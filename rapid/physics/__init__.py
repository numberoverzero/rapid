from typing import Callable, List

import pymunk

from ..parsing import Parser
from ..util import Vec2

shapes = {
    "circle": {
        "cls": pymunk.Circle,
        "fields": {
            "radius": float
        }
    },
    "segment": {
        "cls": pymunk.Segment,
        "fields": {
            "a": Vec2,
            "b": Vec2,
            "radius": float
        },
    },
    "poly": {
        "cls": pymunk.Poly,
        "fields": {
            "vertices": List[Vec2]
        }
    }
}


def build_body(body_type, mass=None, moment=None) -> pymunk.Body:
    body = pymunk.Body(body_type=body_type)
    if mass is not None:
        body.mass = mass
    if moment is not None:
        body.moment = moment
    return body


def build_shape(
        shape_type: str, shape_definition: dict,
        body: pymunk.Body=None,
        mass: float=None, elasticity: float=None, friction: float=None) -> pymunk.Shape:
    shape_cls = shapes[shape_type]["cls"]
    shape = shape_cls(body=body, **shape_definition)
    if mass is not None:
        shape.mass = mass
    if elasticity is not None:
        shape.elasticity = elasticity
    if friction is not None:
        shape.friction = friction
    return shape


def body_factory(body_type, mass=None, moment=None) -> Callable[[Parser], pymunk.Body]:
    def new_body(parser: Parser) -> pymunk.Body:
        return build_body(
            body_type,
            mass=parser.parse(mass, float),
            moment=parser.parse(moment, float)
        )
    return new_body


def shape_factory(
        shape_type, shape_definition,
        mass=None, elasticity=None, friction=None) -> Callable[[Parser], pymunk.Shape]:
    def new_shape(parser: Parser) -> pymunk.Shape:
        computed_definition = {}
        return None
    return new_shape
