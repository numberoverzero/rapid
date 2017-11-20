import random

import pyglet

from rapid.rendering import PointParticle, LineParticle, ParticleCollection
from rapid.windowing import BatchDrawable
from skeleton import Game

USE_POINTS = False
# Free'd particles are turned red and transparent
#   when USE_ALPHA is False, disabled particles appear red, unallocated appear blue
#   when USE_ALPHA is True, disabled particles are invisible
USE_ALPHA = False
# when SHUFFLE is True, particles are free'd in random order for re-use
SHUFFLE = True


vx0, vy0 = 160, 100
width, height = 7, 11
padding = 5
size = 50
cls = PointParticle if USE_POINTS else LineParticle
pool_renderer = BatchDrawable()
pool = ParticleCollection(cls, width * height, batch=pool_renderer.batch)
active = []
i, j = 0, 0


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
        if USE_POINTS:
            new_particle.pos = self.camera.to_world_coords(x0, y0)
        else:
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
game.components.append(pool_renderer)
fps = pyglet.clock.ClockDisplay(clock=game.window.clock)


with pool.iterator() as it:
    for particle in it:
        particle.color = 0, 0, 255, 0
        if not USE_POINTS:
            particle.p0 = 0, 0
            particle.p1 = (size - padding, ) * 2

if USE_ALPHA:
    ParticleCollection.enable_blending()

pyglet.gl.glPointSize(12.0)
pyglet.gl.glEnable(pyglet.gl.GL_POINT_SMOOTH)

game.run()
