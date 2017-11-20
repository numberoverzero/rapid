from typing import Any, Callable, Dict, Optional, Type

from ._eval import EvalContext, safe_eval
from .template import Parser, Template

from ..util import Vec2

__all__ = [
    "EvalContext", "safe_eval",
    "Parser", "Template",
    "whitelist_common_attribute_names", "json_template_loader", "load_json_templates",
]

DEFAULT_TYPE_NAMES = {
    "float": float,
    "vec2": Vec2
}


def whitelist_common_attribute_names(parser: Parser) -> None:
    """Utility to whitelist 'x', 'y', 'z', 'r', 'g', 'b', 'a'"""
    parser.eval_context.whitelisted_attribute_names |= {"x", "y", "z", "r", "g", "b", "a"}


def json_template_loader(
        type_names: Optional[Dict[str, Type]]=None,
        base_templates: Optional[Dict[str, Template]]=None) -> Callable[[str, Dict[str, Any]], Template]:
    """Returns a function that loads templates from json blobs.

    :param type_names:
        Dict that maps (lowercase) type names to classes eg. {"vec2": Vec2}
    :param base_templates:
        Dict of existing templates, which this one may derive from.
    :return:
        A function that uses the given type_names mapping and base_templates dict to build new templates.
    """
    if type_names is None:
        type_names = DEFAULT_TYPE_NAMES
    type_names = {key.lower(): value for (key, value) in type_names.items()}
    if base_templates is None:
        base_templates = {}

    def load_template(name: str, data: Dict[str, Any]) -> Template:
        """Construct a template from a loaded json blob.

        An example of a loaded json blob to create a template from:

            {
                "__base__": "_global_base_template",
                "variables": {
                    "center": "vec2",
                    "width": "float",
                    "height": "float"
                },
                "defaults": {
                    "width": "125/6"
                }
            }

        :param name:
            This template's name, so others can derive from it
        :param data:
            A loaded json blob representing the template
        :return:
            A new rapid.parsing.Template
        """
        if name in base_templates:
            raise ValueError(f"base_templates already has a template for name {name!r}")

        if "__base__" in data:
            base_template = base_templates[data["__base__"]]
        else:
            base_template = None

        variables = {
            key.lower(): value
            for (key, value) in data.get("variables", {}).items()
        }
        defaults = data.get("defaults", {})
        template_data = data.get("template", {})

        required_type_names = set(variables.values())
        provided_type_names = set(type_names.keys())
        missing_type_names = required_type_names - provided_type_names
        if missing_type_names:
            raise ValueError(f"type_names is missing required keys {missing_type_names}")

        template = Template(
            name=name,
            local_variables={key: type_names[value] for (key, value) in variables.items()},
            local_defaults=defaults,
            local_data=template_data
        )
        if base_template:
            template.derive_from(base_template)

        base_templates[name] = template
        return template

    return load_template


def load_json_templates(data: Dict[str, Any]) -> Dict[str, Template]:
    """Returns a collection of templates from a loaded json blob.

    An example of a collection of templates:

        {
          "box[center, width, height]": {
            "variables": {
              "center": "vec2",
              "width": "float",
              "height": "float"
            },
            "template": {
              "physics": {
                "body": {
                  "type": "static",
                  "elasticity": 1,
                  "friction": 0
                },
                "shapes": [...]
              }
            }
          },
          "medium_box[center]": {
            "__base__": "box[center, width, height]",
            "defaults": {
              "width": 200,
              "height": 400
            }
          }
        }

    :param data: Loaded json blob
    :return: dict of templates from the blob
    """
    templates = {}
    bases = []
    for name, blob in data.items():
        base = blob.get("__base__", None)
        bases.append((name, base))

    load = json_template_loader(base_templates=templates)
    while bases:
        name, base = bases.pop(0)
        if base is not None and base not in templates:
            bases.append((name, base))
            continue
        load(name, data[name])
    return templates
