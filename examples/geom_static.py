from pyglet import gl

from rapid.rendering import Circle, Rectangle, GLMode, Color
from rapid.util import Vec2
from rapid.windowing import BatchDrawable
from skeleton import Game

GAME = Game()
MODE = GLMode.Triangles
SHAPE = "circle"
MULTIPLE_RENDERERS = False

if not MULTIPLE_RENDERERS:
    renderer = BatchDrawable()
    GAME.components.append(renderer)

radius = 100
rotation = 3.14159 / 1
p = 1.6 * radius
resolution = 40
colors = [
    Color(int(255 / 1), int(255 / 8), 0, 127),
    Color(int(255 / 2), int(255 / 4), 0, 127),
    Color(int(255 / 4), int(255 / 2), 0, 127),
    Color(int(255 / 8), int(255 / 1), 0, 127),
]
centers = [
    (p, p), (-p, p), (-p, -p), (p, -p)
]


for color, center in zip(colors, centers):
    if MULTIPLE_RENDERERS:
        renderer = BatchDrawable()
        GAME.components.append(renderer)
    if SHAPE == "circle":
        circle_shape = Circle(
            center=Vec2.of(center),
            radius=radius,
            resolution=resolution,
            color=color,
            batch=renderer.batch,
            mode=MODE)
    else:
        rect_shape = Rectangle(
            center=Vec2.of(center),
            width=radius,
            height=radius/2,
            rotation=rotation,
            color=color,
            batch=renderer.batch,
            mode=MODE
        )


gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_SRC_ALPHA)
gl.glEnable(gl.GL_LINE_SMOOTH)

gl.glFrontFace(gl.GL_CCW)
gl.glEnable(gl.GL_CULL_FACE)
gl.glCullFace(gl.GL_BACK)

GAME.run()
