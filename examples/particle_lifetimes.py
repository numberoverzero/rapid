import random
import pyglet
from rapid.particles import LineParticle, ParticleCollection
from skeleton import Game

vx0, vy0 = 160, 100
width, height = 7, 11
padding = 5
size = 50
pool = ParticleCollection(LineParticle, 100)
active = []
i, j = 0, 0


# Free'd particles are turned red and transparent
#   when USE_ALPHA is False, disabled particles appear red
#   when USE_ALPHA is True, disabled particles are invisible
USE_ALPHA = True
# when SHUFFLE is True, particles are free'd in random order for re-use
SHUFFLE = True


class MyGame(Game):

    def on_update(self, dt: float):
        global i, j
        x = i % width
        y = i // width
        x0, y0 = vx0 + x * size, vy0 + y * size
        x1, y1 = x0 + (size - padding), y0 + (size - padding)

        if i == 0 and j > 0:
            if SHUFFLE:
                random.shuffle(active)
            while active:
                particle = active.pop()
                particle.color = 255, 0, 0, 0
                particle.free()
        new_particle = pool.alloc()
        assert new_particle, (i, j, len(active))
        new_particle.p0 = self.camera.to_world_coords(x0, y0)
        new_particle.p1 = self.camera.to_world_coords(x1, y1)
        new_particle.color = 255, 255, 255, 255
        active.append(new_particle)
        i = (i + 1) % (width * height)
        j += 1
        super().on_update(dt)

    def on_draw(self):
        super().on_draw()
        with self.camera:
            fps.draw()


game = MyGame()
game.components.append(pool)
fps = pyglet.clock.ClockDisplay(clock=game.window.clock)

if USE_ALPHA:
    ParticleCollection.enable_blending()
game.run()
