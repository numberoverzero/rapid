from rapid.primitives.utils import GLMode
from rapid.primitives.geometry import circle, flatten
from rapid.windowing.scene import BatchDrawable
from skeleton import Game


renderer = BatchDrawable()


c = (0, 0)
r = 210
n = 3
verts = flatten(circle(c[0], c[1], r, n, GLMode.TriangleFan))
assert len(verts) == 2 * (n + 1)
renderer.batch.add(
    n + 1, GLMode.TriangleFan.gl_mode, None,
    ("v2f", verts),
    ("c4B", (255, 255, 255, 255) * (n + 1)),
)

game = Game()
game.components.append(renderer)
game.run()
