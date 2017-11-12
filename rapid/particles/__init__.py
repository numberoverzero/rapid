import pyglet.gl
from pyglet.graphics import Batch
from pyglet.graphics.vertexdomain import VertexList


from typing import Optional, Tuple, TypeVar
from ..scene import BatchDrawable

__all__ = [
    "LineParticleCollection"
]

Color = Tuple[int, int, int, int]  # c4B
Vec2 = Tuple[float, float]  # v2f
T = TypeVar("T")


def monotonic_counter(initial: int=0):
    value = initial
    while True:
        yield value
        value += 1


GLOBAL_ID = monotonic_counter()


# noinspection PyProtectedMember
class LineParticleCollection(BatchDrawable):
    """Collection of particles, rendered using GL_LINES"""
    active_particles: int
    max_particles: int

    _inactive_head: Optional["LineParticle"]
    _active_head: Optional["LineParticle"]

    _last_rendered_count: int
    verts: VertexList
    dirty: bool  # set to True to re-stream vert/color data

    def __init__(self, max_particles: int=1000, batch: Optional[Batch]=None) -> None:
        super().__init__(batch)
        self.verts = self.batch.add(2 * max_particles, pyglet.gl.GL_LINES, None, "v2f/stream", "c4B/stream")

        self.dirty = True

        self._last_rendered_count = 0
        self.active_particles = 0
        self.max_particles = max_particles

        self._active_head = None
        self._inactive_head = None
        for _ in range(max_particles):
            # _prev_particle isn't set, because we only need to track prev when free-ing an active particle
            particle = LineParticle(collection=self)
            particle._next_particle = self._inactive_head
            self._inactive_head = particle

    def alloc(self) -> Optional["LineParticle"]:
        """Pull an inactive particle off the inactive stack, push it onto the active stack"""
        particle = self._inactive_head
        if particle is None:
            return None

        self.dirty = True

        # Pop the to-be-returned particle from the inactive stack
        self._inactive_head = particle._next_particle

        # Push the to-be-returned particle onto the active stack
        particle._next_particle = old_head = self._active_head
        if old_head is not None:
            old_head._prev_particle = particle
        self._active_head = particle
        particle._prev_particle = None

        self.active_particles += 1

        particle._id = next(GLOBAL_ID)
        return particle

    def free(self, particle: "LineParticle") -> None:
        # TODO | is this actually a problem?  Double free should simply re-order
        # TODO | the inactive list, without actually losing a particle...
        assert particle._id is not None, "tried to double free"
        particle._id = None
        self.dirty = True

        prev = particle._prev_particle
        next = particle._next_particle

        if particle is self._active_head:
            self._active_head = next

        # Pointers to this particle now point to each other: A <--> particle <--> B becomes A <--> B
        if prev is not None:
            prev._next_particle = next
        if next is not None:
            next._prev_particle = prev

        # Clear this particle's pointers, and push in onto the head of the inactive stack.
        # _prev is always None on the inactive stack since we only need a singly linked list to allocate
        particle._prev_particle = None
        particle._next_particle = self._inactive_head
        self._inactive_head = particle

        self.active_particles -= 1

    def on_update(self, dt: float) -> None:
        if self.dirty:
            self._rebuild_verts()
            self.dirty = False

    def _rebuild_verts(self) -> None:
        n = self.active_particles
        particle = self._active_head
        for i in range(n):
            self.verts.vertices[i * 4: i * 4 + 4] = [*particle.p0, *particle.p1]
            self.verts.colors[i * 8: i * 8 + 8] = particle.color * 2
            particle = next(particle)
        assert particle is None, "excluded some active particles"

        if self._last_rendered_count > n:
            to_clear = self._last_rendered_count - n
            # multiply by 8 because there are 4 values per vertex color, two vertices per particle
            # offset by 3 to set the alpha to 0
            # replace with to_clear * 2 because there are 2 vertices to clear per particle
            self.verts.colors[n * 8 + 3: (n + to_clear) * 8 + 3: 4] = (0,) * (to_clear * 2)
        self._last_rendered_count = n


# noinspection PyProtectedMember
class ParticleProperty:
    # noinspection PyTypeChecker
    def __get__(self, instance: Optional["LineParticle"], owner):
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance: "LineParticle", value):
        instance.__dict__[self.name] = value
        instance._collection.dirty = True

    def __set_name__(self, owner, name):
        self.name = name


class LineParticle:
    _collection: LineParticleCollection
    _prev_particle: Optional["LineParticle"]
    _next_particle: Optional["LineParticle"]
    _id: Optional[int]

    p0: Vec2 = ParticleProperty()
    p1: Vec2 = ParticleProperty()
    color: Color = ParticleProperty()

    def __init__(self, collection: LineParticleCollection) -> None:
        self._collection = collection
        self._prev_particle = None
        self._next_particle = None
        self._id = None

        self.p0 = 0, 0
        self.p1 = 0, 0
        self.color = 255, 255, 255, 255

    def __repr__(self) -> str:
        if self._id is not None:
            x = f"{self._id}, {id(self)}"
        else:
            x = id(self)
        return f"<LineParticle[{x}]>"

    def __next__(self) -> Optional["LineParticle"]:
        return self._next_particle

    def free(self) -> None:
        self._collection.free(self)
