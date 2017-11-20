from rapid.rendering import LineParticle, ParticleCollection
from rapid.windowing import BatchDrawable
from skeleton import Game

pool_renderer = BatchDrawable()
pool = ParticleCollection(LineParticle, 1, batch=pool_renderer.batch)
particle = pool.alloc()  # type: LineParticle
assert particle


class MyGame(Game):
    def on_update(self, dt: float) -> None:
        x0, y0 = particle.p0
        x1, y1 = particle.p1
        particle.p0 = x0 + 1, y0 + 1
        particle.p1 = x1 + 3, y1 + 3
        super().on_update(dt)


game = MyGame()
game.components.append(pool_renderer)
game.run()
