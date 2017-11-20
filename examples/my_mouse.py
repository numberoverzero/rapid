import random
from typing import Set

from pyglet.gl import *

from rapid.rendering import ParticleCollection, TriangleParticle
from rapid.windowing import BatchDrawable
from skeleton import Game, key


DEBUG = False
MAX_PARTICLES = 500
active = set()  # type: Set[MyParticle]

renderer = BatchDrawable()
particles = ParticleCollection(TriangleParticle, particle_count=MAX_PARTICLES, batch=renderer.batch)

spawn_chance = .9
die_chance = .1

reduce = lambda x: int(x * 0.8)


class MyParticle:
    def __init__(self, particle: TriangleParticle) -> None:
        self.x = self.lx = random.randint(v0x, v1x)
        self.y = self.ly = random.randint(v0y, v1y)
        self.dx = random.randint(-70, 70)
        self.dy = random.randint(-70, 70)
        self.damping = random.random() * .15 + .8
        self.power = random.random() * .1 + .05
        self._particle = particle
        self._particle.set_alpha(255)

    def update(self, dt) -> None:
        global minx, maxx
        # calculate my acceleration based on the distance to the mouse
        # pointer and my acceleration power
        mx, my = game.target
        x, y = self.x, self.y
        lx, ly = x, y

        dx2 = (x - mx) / self.power
        dy2 = (y - my) / self.power

        # now figure my new velocity
        self.dx -= dx2 * dt
        self.dy -= dy2 * dt
        self.dx *= self.damping
        self.dy *= self.damping

        # calculate new line endpoints
        x += self.dx * dt
        y += self.dy * dt

        self.x, self.y = x, y
        self.lx, self.ly = lx, ly

        self._particle.p0 = x, y  # front of triangle

        m = -(x - lx) / (y - ly)  # negative reciprocal
        b = ly - m * lx
        d2 = (x - lx) ** 2 + (y - ly) ** 2
        xo = (d2 / (m**2 + 1)) ** 0.5
        if xo > 3:
            xo = 3

        p1x = lx - xo
        p1y = m * p1x + b

        p2x = lx + xo
        p2y = m * p2x + b

        self._particle.p1 = p1x, p1y
        self._particle.p2 = p2x, p2y

    def kill(self):
        particle = self._particle
        r, g, b, _ = particle.color
        particle.color = (r, reduce(g), reduce(b), 0)
        particle.free()


class ParticleGame(Game):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = 0, 0
        self.window.clear = lambda: None
        self._enabled = True

    def on_mouse_motion(self, x, y, dx, dy):
        self.target = self.camera.to_world_coords(x, y)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self._enabled = not self._enabled
        elif symbol == key.ENTER:
            while len(active) < MAX_PARTICLES:
                spawn_particle()
        else:
            super().on_key_press(symbol, modifiers)

    def on_update(self, dt: float) -> None:
        if self._enabled:
            if random.random() < spawn_chance:
                spawn_particle()
            if random.random() < die_chance:
                kill_random()

            for p in active:
                p.update(dt)
        super().on_update(dt)

    def on_draw(self):
        glColor4f(0, 0, 0, .1)
        x0, y0 = self.camera.to_world_coords(0, 0)
        x1, y1 = self.camera.to_world_coords(self.window.width, self.window.height)
        glRectf(x0, y0, x1, y1)
        super().on_draw()
        with self.camera:
            fps_display.draw()


game = ParticleGame()
game.components.append(renderer)
fps_display = pyglet.clock.ClockDisplay(clock=game.window.clock)
v0x, v0y = game.camera.to_world_coords(0, 0)
v1x, v1y = game.camera.to_world_coords(game.window.width, game.window.height)


def spawn_particle():
    particle = particles.alloc()
    if particle is None:
        return
    my_particle = MyParticle(particle)
    if DEBUG:
        print(f"spawned {my_particle._particle}")
    active.add(my_particle)


def kill_random():
    if not active:
        return
    my_particle = pick_random()
    active.remove(my_particle)
    my_particle.kill()
    if DEBUG:
        print(f"killed {my_particle._particle} {my_particle._particle.color[1]}")


def pick_random():
    it = iter(active)
    n = random.randint(0, len(active) - 1)
    el = next(it)
    for _ in range(n - 1):
        el = next(it)
    return el


if __name__ == '__main__':
    ParticleCollection.enable_blending()
    if spawn_chance >= 1 and die_chance >= 1:
        while len(active) < MAX_PARTICLES:
            spawn_particle()
    game.run()
