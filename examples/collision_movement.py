import json
from pyglet import gl
from rapid.physics import load_world
from rapid.primitives import Color, GLMode
from rapid import Vec2
from skeleton import Game, key

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

world = load_world(data=GEOMETRY, global_variables=GLOBAL_GEOMETRY_VARIABLES)
world.timestep = 1 / 120

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
        world.bodies["player"].velocity = vx, vy
        world.step(dt)

    def on_draw(self):
        super().on_draw()
        with self.camera:
            world.debug_draw()


game = MyGame()

gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_LINE_SMOOTH)

game.run()
