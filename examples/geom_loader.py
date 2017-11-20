from skeleton import Game
from rapid.windowing.scene import BatchDrawable
from rapid.physics import load_world

import json
import logging
logging.basicConfig(level=logging.DEBUG)

GEOMETRY = """{
  "templates": {
    "box[center, width, height]": {
      "variables": {
        "center": "vec2",
        "width": "float",
        "height": "float"
      },
      "template": {
        "physics": {
          "body": {
            "type": "static"
          },
          "shapes": [
            {
              "type": "segment",
              "a": ["center.x - width / 2", "center.y - height / 2"],
              "b": ["center.x - width / 2", "center.y + height / 2"],
              "radius": 1,
              "elasticity": 1,
              "friction": 0
            },
            {
              "type": "segment",
              "a": ["center.x + width / 2", "center.y - height / 2"],
              "b": ["center.x + width / 2", "center.y + height / 2"],
              "radius": 1,
              "elasticity": 1,
              "friction": 0
            },
            {
              "type": "segment",
              "a": ["center.x - width / 2", "center.y - height / 2"],
              "b": ["center.x + width / 2", "center.y - height / 2"],
              "radius": 1,
              "elasticity": 1,
              "friction": 0
            },
            {
              "type": "segment",
              "a": ["center.x - width / 2", "center.y + height / 2"],
              "b": ["center.x + width / 2", "center.y + height / 2"],
              "radius": 1,
              "elasticity": 1,
              "friction": 0
            }
          ]
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
  },
  "objects": {
    "boxes": [
      {
        "__base__": "medium_box[center]",
        "defaults": {
          "center": [-210, 0]
        }
      },
      {
        "__base__": "medium_box[center]",
        "defaults": {
          "center": [0, 0]
        }
      },
      {
        "__base__": "medium_box[center]",
        "defaults": {
          "center": [210, 0]
        }
      }
    ],
    "player": {
      "physics": {
        "body": {
          "type": "dynamic",
          "position": [0, 300]
        },
        "shapes": [{
          "type": "circle",
          "radius": 50,
          "elasticity": 1,
          "friction": 0
        }]
      }
    },
    "ball": {
      "physics": {
        "body": {
          "type": "dynamic",
          "position": [0, -300]
        },
        "shapes": [{
          "type": "circle",
          "radius": 25,
          "elasticity": 1,
          "friction": 0
        }]
      }
    }
  }
}"""
world = load_world(data=json.loads(GEOMETRY))
game = Game()


def debug_draw(scene) -> None:
    with scene.camera:
        world.debug_draw()


renderer = BatchDrawable()
game.components.append(renderer)
renderer.on_draw = debug_draw
game.run()
