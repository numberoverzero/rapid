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
    _verts: VertexList
    active_particles: int
    _next_inactive: Optional["LineParticle"]

    def __init__(self, max_particles: int=1000, batch: Optional[Batch]=None) -> None:
        super().__init__(batch)
        self._verts = self.batch.add(2 * max_particles, pyglet.gl.GL_LINES, None, "v2f/stream", "c4B/stream")

        self.active_particles = max_particles
        self._next_inactive = None
        for i in range(max_particles):
            particle = LineParticle(_collection=self, _id=next(GLOBAL_ID), _i=i)
            self.free(particle)
        assert self.active_particles == 0

    def alloc(self) -> Optional["LineParticle"]:
        """Pull an inactive particle off the inactive stack, push it onto the active stack"""
        particle = self._next_inactive
        if particle is None:
            return None
        self._next_inactive = particle._next_inactive
        particle._id = next(GLOBAL_ID)
        self.active_particles += 1
        return particle

    def free(self, particle: "LineParticle") -> None:
        particle._id = None
        particle._next_inactive = self._next_inactive
        self._next_inactive = particle
        self.active_particles -= 1


# noinspection PyProtectedMember
class LineParticle:
    _collection: LineParticleCollection
    _i: int
    _next_inactive: Optional["LineParticle"]
    _id: Optional[int]

    def __init__(self, _collection: LineParticleCollection, _id: int, _i: int) -> None:
        self._collection = _collection
        self._i = _i

        self._next_inactive = None
        self._id = _id

        self.p0 = 0, 0
        self.p1 = 0, 0
        self.color = 255, 255, 255, 255

    def __repr__(self) -> str:
        if self._id is not None:
            x = f"{self._id}, {id(self)}"
        else:
            x = id(self)
        return f"<LineParticle[{x}]>"

    @property
    def p0(self) -> Vec2:
        return self._collection._verts.vertices[self._i * 4 + 0: self._i * 4 + 2]

    @p0.setter
    def p0(self, v: Vec2):
        self._collection._verts.vertices[self._i * 4 + 0: self._i * 4 + 2] = v

    @property
    def p1(self) -> Vec2:
        return self._collection._verts.vertices[self._i * 4 + 2: self._i * 4 + 4]

    @p1.setter
    def p1(self, v: Vec2):
        self._collection._verts.vertices[self._i * 4 + 2: self._i * 4 + 4] = v

    @property
    def color(self) -> Color:
        return self._collection._verts.colors[self._i * 8: self._i * 8 + 4]

    @color.setter
    def color(self, c: Color):
        self._collection._verts.colors[self._i * 8: self._i * 8 + 8] = c * 2

    def free(self) -> None:
        self._collection.free(self)

    def set_alpha(self, x: int) -> None:
        self._collection._verts.colors[self._i * 8 + 3: self._i * 8 + 8 + 3: 4] = (x, x)
