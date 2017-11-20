import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import pymunk
import pymunk.pyglet_util

from ..parsing import (
    json_template_loader,
    load_json_templates,
    whitelist_common_attribute_names,
)
from .builders import (
    body_factory,
    body_types_by_name,
    extract_shape_definition,
    shape_classes_by_name,
    shape_factory,
)


__all__ = ["load_space", "fixed_timestep_clock"]


logger = logging.getLogger(__name__)


def fixed_timestep_clock(fixed_timestep: float) -> Callable[[pymunk.Space, float], None]:
    """Creates a function that can be used to advance a space using a fixed timestep.

    .. code-block:: python

        >>> from rapid.physics.world import fixed_timestep_clock
        >>> from pymunk import Space
        >>> advance_clock = fixed_timestep_clock(1/120)
        >>> space = Space()
        >>> advance_clock(space, 1/40)  # advance the space 3 times
        >>> advance_clock(space, 1/240)  # doesn't advance the space
        >>> advance_clock(space, 1/240)  # advances the space 1 time

    :param fixed_timestep: The fixed amount to step the space by
    """
    unused_dt = 0.0

    def step(space: pymunk.Space, dt: float) -> None:
        """Step the space using a fixed timestep, even when ``dt`` varies.

        :param space: The space to step forward
        :param dt: A variable amount of time to move forward
        """
        nonlocal unused_dt
        steps, unused_dt = divmod(dt + unused_dt, fixed_timestep)
        for _ in range(int(steps)):
            space.step(fixed_timestep)

    return step


def load_space(
        space: pymunk.Space, *,
        data: Dict[str, Any],
        global_variables: Optional[Dict[str, Any]]=None) -> Dict[str, pymunk.Body]:
    logger.debug(f"loading space from data: {data} using global variables: {global_variables}")
    templates = load_json_templates(data.get("templates", {}))
    new_template = json_template_loader(base_templates=templates)

    global_variables = global_variables or {}
    objects = data.get("objects", {})

    created_bodies = {}

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
        created_bodies[name] = body
        return body, shapes

    for object_name, object_data in objects.items():
        if isinstance(object_data, list):
            for i, each_data in enumerate(object_data):
                each_name = f"{object_name}#{i}"
                body, shapes = build(each_name, each_data)
                space.add(body, *shapes)
        elif isinstance(object_data, dict):
            body, shapes = build(object_name, object_data)
            space.add(body, *shapes)

    return created_bodies
