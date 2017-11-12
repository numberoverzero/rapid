from rapid.particles import LineParticle, LineParticleCollection
from skeleton import Game


pool = LineParticleCollection(1)
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
game.components.append(pool)
game.run()
