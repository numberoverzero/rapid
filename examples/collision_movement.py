import json

import pymunk.pyglet_util
from pyglet import gl

from rapid.physics import fixed_timestep_clock, load_space
from rapid.rendering import Color, GLMode
from rapid.util import Vec2
from skeleton import Game, key


options = pymunk.pyglet_util.DrawOptions()


FIXED_TIMESTEP = 1 / 120
WALL_COLOR = Color(128, 128, 128, 128)
PLAYER_COLOR = Color(0, 255, 0, 255)
BALL_COLOR = Color(0, 0, 255, 255)
GL_MODE = GLMode.Triangles
PLAYER_VELOCITY = 150.0
GLOBAL_GEOMETRY_VARIABLES = {
    "center": Vec2(0, 0),
    "width": 600,
    "height": 600,
    "player_radius": 50,
    "ball_radius": 50
}
GEOMETRY = json.loads("""{
  "objects": {
    "player": {
      "physics": {
        "body": {
          "type": "kinematic"
        },
        "shapes": [{
          "type": "circle",
          "radius": "player_radius",
          "elasticity": 1,
          "friction": 0,
          "mass": 1
        }]
      }
    },
    "ball": {
      "physics": {
        "body": {
          "type": "dynamic",
          "position": [
              "1.5 * (player_radius + ball_radius)",
              "1.5 * (player_radius + ball_radius)"
          ]
        },
        "shapes": [{
          "type": "circle",
          "radius": "ball_radius",
          "elasticity": 1,
          "friction": 0,
          "mass": 1
        }]
      }
    },
    "walls": {
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
  }
}""")
space = pymunk.Space()
advance_time = fixed_timestep_clock(1 / 120)
bodies = load_space(space, data=GEOMETRY, global_variables=GLOBAL_GEOMETRY_VARIABLES)


movement = {
    key.W: 0,
    key.S: 0,
    key.A: 0,
    key.D: 0,
}


class MyGame(Game):
    dt_slop = 0

    def on_key_press(self, symbol, modifiers):
        if symbol in movement:
            movement[symbol] = 1
        else:
            super().on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        if symbol in movement:
            movement[symbol] = 0
        else:
            super().on_key_release(symbol, modifiers)

    def on_update(self, dt: float):
        super().on_update(dt)

        # Update player velocity
        vx = PLAYER_VELOCITY * (movement[key.D] - movement[key.A])
        vy = PLAYER_VELOCITY * (movement[key.W] - movement[key.S])
        bodies["player"].velocity = vx, vy
        advance_time(space, dt)

    def on_draw(self):
        super().on_draw()
        with self.camera:
            space.debug_draw(options)


game = MyGame()

gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_LINE_SMOOTH)

game.run()
