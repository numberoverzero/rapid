import random
import pyglet
from rapid.particles import LineParticleCollection
from skeleton import Game

vx0, vy0 = 160, 100
width, height = 7, 11
padding = 5
size = 50
pool = LineParticleCollection(100)
active = []
i, j = 0, 0


class MyGame(Game):

    def on_update(self, dt: float):
        global i, j
        x = i % width
        y = i // width
        x0, y0 = vx0 + x * size, vy0 + y * size
        x1, y1 = x0 + (size - padding), y0 + (size - padding)
        # print(i, x, y)
        # print(x0, y0, x1, y1)

        if i < len(active):
            available = len(active)
            for particle in random.sample(active, available - 2):
                particle.free()
                active.remove(particle)
            new_particle = pool.alloc()
            assert new_particle, (i, j, len(active))
        else:
            new_particle = pool.alloc()
            assert new_particle, (i, j, len(active))

        new_particle.p0 = self.camera.to_world_coords(x0, y0)
        new_particle.p1 = self.camera.to_world_coords(x1, y1)
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
game.run()
