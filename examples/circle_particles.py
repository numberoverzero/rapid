import random
from typing import Set

import pyglet

from rapid.util import Vec2
from rapid.rendering import CircleParticle, Color, ParticleCollection, RectangleParticle, single_particle
from rapid.windowing import BatchDrawable
from skeleton import Game, key


MAX_PARTICLES = 100

particle_renderer = BatchDrawable()
particles = ParticleCollection(CircleParticle, particle_count=MAX_PARTICLES, batch=particle_renderer.batch)
gray_box = single_particle(RectangleParticle, batch=particle_renderer.batch)

active = set()  # type: Set[CircleParticle]

speed = 0.1
spawn_chance = .9
die_chance = .1


class ParticleGame(Game):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = Vec2.Zero
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

            for particle in active:
                heading = self.target - particle.center
                particle.center += (heading * speed) / particle.radius

        super().on_update(dt)

    def on_draw(self):
        super().on_draw()
        with self.camera:
            fps_display.draw()


def spawn_particle():
    particle = particles.alloc()
    if particle is None:
        return
    particle.color = _random_color()
    particle.radius = _random_radius()
    particle.center = _random_center()
    active.add(particle)


def kill_random():
    if not active:
        return
    particle = pick_random()
    active.remove(particle)
    particle.color = 255, 255, 255, 0
    particle.free()


def pick_random():
    it = iter(active)
    n = random.randint(0, len(active) - 1)
    el = next(it)
    for _ in range(n - 1):
        el = next(it)
    return el


game = ParticleGame()
game.components.append(particle_renderer)
fps_display = pyglet.clock.ClockDisplay(clock=game.window.clock)


v0x, v0y = game.camera.to_world_coords(0, 0)
v1x, v1y = game.camera.to_world_coords(game.window.width, game.window.height)

vw = v1x - v0x
vh = v1y - v0y

gray_box.center = Vec2(v0x + vw / 2, v0y + vh / 2)
gray_box.width = vw
gray_box.height = vh
gray_box.color = 0, 0, 0, 25


def _random_center() -> Vec2:
    return Vec2(_rlerp(v0x, v1x), _rlerp(v0y, v1y))


def _random_radius() -> float:
    return _rlerp(10, 50)


def _random_color() -> Color:
    c0, c1 = 0, 255
    r = lambda: int(_rlerp(c0, c1))
    return Color(r(), r(), r(), 128)


def _rlerp(v0, v1) -> float:
    t = random.random()
    return v0 + t * (v1 - v0)


if __name__ == '__main__':
    ParticleCollection.enable_blending()
    if spawn_chance >= 1 and die_chance >= 1:
        while len(active) < MAX_PARTICLES:
            spawn_particle()
    game.run()
