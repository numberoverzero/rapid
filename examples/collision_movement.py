import pymunk
from pymunk import Space, Body, Circle, Segment
from pyglet import gl
from rapid.windowing.scene import BatchDrawable
from rapid.primitives import shapes, Color, GLMode

from skeleton import Game, key

FIXED_TIMESTEP = 1 / 120
WALL_COLOR = Color(128, 128, 128, 128)
PLAYER_COLOR = Color(0, 255, 0, 255)
BALL_COLOR = Color(0, 0, 255, 255)
GL_MODE = GLMode.Triangles
PLAYER_VELOCITY = 150.0
WALL_THICKNESS = 10

PLAYER_RADIUS = 50
BALL_RADIUS = 20
CIRCLE_RESOLUTION = 50

renderer = BatchDrawable()

# Collision setup
space = Space()
space.gravity = 0, 0


segment = lambda a, b: Segment(space.static_body, a, b, 1)


walls = [
    # bottom
    segment(
        (-(200 + WALL_THICKNESS), -(200 + WALL_THICKNESS)),
        ((200 + WALL_THICKNESS), -200)
    ),
    # top
    segment(
        (-(200 + WALL_THICKNESS), 200),
        ((200 + WALL_THICKNESS), (200 + WALL_THICKNESS))
    ),
    # left
    segment(
        (-(200 + WALL_THICKNESS), -(200 + WALL_THICKNESS)),
        (-200, (200 + WALL_THICKNESS))
    ),
    # right
    segment(
        (200, -(200 + WALL_THICKNESS)),
        ((200 + WALL_THICKNESS), (200 + WALL_THICKNESS))
    ),
]
for wall in walls:
    wall.elasticity = 1.0
    wall.friction = 0
space.add(walls)

player_body = Body(mass=1, moment=pymunk.moment_for_circle(1, 0, PLAYER_RADIUS), body_type=pymunk.Body.KINEMATIC)
player_body.position = 0, 0
player_collider = Circle(player_body, PLAYER_RADIUS)
player_collider.elasticity = 1
space.add(player_body, player_collider)

ball_body = Body(mass=1, moment=pymunk.moment_for_circle(1, 0, BALL_RADIUS), body_type=pymunk.Body.DYNAMIC)
ball_body.position = (
    1.5 * (PLAYER_RADIUS + BALL_RADIUS),
    1.5 * (PLAYER_RADIUS + BALL_RADIUS),
)
ball_collider = Circle(ball_body, BALL_RADIUS)
ball_collider.elasticity = 1
ball_collider.friction = 0
space.add(ball_body, ball_collider)

movement = {
    key.W: 0,
    key.S: 0,
    key.A: 0,
    key.D: 0,
}

# Rendering setup
batch = renderer.batch
for wall in walls:
    (left, bottom), (right, top) = wall.a, wall.b
    cx = left + (right - left) / 2.0
    cy = bottom + (top - bottom) / 2.0
    shapes.Rectangle(
        center=Vec2(cx, cy),
        width=right - left,
        height=top - bottom,
        rotation=0, color=WALL_COLOR,
        batch=batch, mode=GL_MODE)
player_renderer = shapes.Circle(
    center=Vec2.of(player_body.position), radius=PLAYER_RADIUS,
    color=PLAYER_COLOR, resolution=CIRCLE_RESOLUTION,
    batch=batch, mode=GL_MODE
)
ball_renderer = shapes.Circle(
    center=Vec2.of(ball_body.position), radius=BALL_RADIUS,
    color=BALL_COLOR, resolution=CIRCLE_RESOLUTION,
    batch=batch, mode=GL_MODE
)


overlay = shapes.Rectangle(
    center=Vec2(0, 0),
    width=400, height=400,
    rotation=0, color=Color(255, 0, 255, 64),
    batch=batch, mode=GL_MODE
)


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
        player_body.velocity = vx, vy
        steps, self.dt_slop = divmod(dt + self.dt_slop, FIXED_TIMESTEP)
        steps = int(steps)
        print(steps, self.dt_slop)
        for _ in range(steps):
            space.step(FIXED_TIMESTEP)

        ball_renderer.center = Vec2.of(ball_body.position)
        player_renderer.center = Vec2.of(player_body.position)

        bvx, bvy = ball_body.velocity
        # print((bvx**2 + bvy**2) ** 0.5)


game = MyGame()
game.components.append(renderer)

gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_LINE_SMOOTH)

gl.glFrontFace(gl.GL_CCW)
gl.glEnable(gl.GL_CULL_FACE)
gl.glCullFace(gl.GL_BACK)

game.run()
