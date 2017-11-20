from typing import Any, Dict, List, Optional, Tuple
import pymunk
import pymunk.pyglet_util

from .builders import (
    body_factory, shape_factory,
    body_types_by_name, shape_classes_by_name,
    extract_shape_definition
)
from ..parsing import (
    load_json_templates,
    json_template_loader,
    whitelist_common_attribute_names,
)

import logging
logger = logging.getLogger(__name__)


class World:
    space: pymunk.Space
    bodies: Dict[str, pymunk.Body]
    timestep: float
    _dt_remainder: float

    def __init__(self, *, space: pymunk.Space, timestep: float) -> None:
        self.bodies = {}
        self.space = space
        self.timestep = timestep
        self._dt_remainder = 0

    def step(self, dt: float) -> None:
        fixed_timestep = self.timestep
        steps, self._dt_remainder = divmod(dt + self._dt_remainder, fixed_timestep)
        for _ in range(int(steps)):
            self.space.step(fixed_timestep)

    def add(self, name: str, body: pymunk.Body, *shapes: pymunk.Shape) -> None:
        assert name not in self.bodies
        self.space.add(body, *shapes)
        self.bodies[name] = body

    def debug_draw(self, options: Optional[pymunk.pyglet_util.DrawOptions]=None) -> None:
        if options is None:
            options = pymunk.pyglet_util.DrawOptions()
        self.space.debug_draw(options)


def load_world(*, data: Dict[str, Any], global_variables: Optional[Dict[str, Any]]=None) -> World:
    logger.debug(f"loading world from data: {data} using global variables: {global_variables}")
    world = World(space=pymunk.Space(), timestep=1/60)
    templates = load_json_templates(data.get("templates", {}))
    new_template = json_template_loader(base_templates=templates)

    global_variables = global_variables or {}
    objects = data.get("objects", {})

    def build(name: str, data: Dict[str, Any]) -> Tuple[pymunk.Body, List[pymunk.Shape]]:
        logger.info(f"building {name!r}")
        if "__base__" in data:
            # Rendering from a base template
            object_template = new_template(f"anonymous:{name}", data)
        else:
            # Inline definition, wrap data in dict for json loader
            object_template = new_template(f"inline:{name}", {"template": data})

        parser = object_template.build_parser(variables={})
        parser.eval_context.exposed_variables.update(global_variables)
        whitelist_common_attribute_names(parser)

        body_data = object_template.template_data["physics"]["body"]
        factory = body_factory(
            body_type=body_types_by_name[body_data["type"]],
            position=body_data.get("position", None),
            mass=body_data.get("mass", None),
            moment=body_data.get("moment", None))
        body = factory(parser)

        shapes = []
        for shape_data in object_template.template_data["physics"]["shapes"]:
            shape_cls = shape_classes_by_name[shape_data["type"]]
            factory = shape_factory(
                shape_cls=shape_cls,
                shape_definition=extract_shape_definition(shape_cls, shape_data),
                mass=shape_data.get("mass", None),
                elasticity=shape_data.get("elasticity", None),
                friction=shape_data.get("friction", None))
            shapes.append(factory(parser, body))

        return body, shapes

    for object_name, object_data in objects.items():
        if isinstance(object_data, list):
            for i, each_data in enumerate(object_data):
                each_name = f"{object_name}#{i}"
                body, shapes = build(each_name, each_data)
                world.add(each_name, body, *shapes)
        elif isinstance(object_data, dict):
            body, shapes = build(object_name, object_data)
            world.add(object_name, body, *shapes)

    return world
