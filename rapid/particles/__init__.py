from pyglet import gl
from pyglet.graphics import Batch, Group
from pyglet.graphics.vertexdomain import VertexList


from typing import ClassVar, Generic, Optional, Tuple, Type, TypeVar
from ..scene import BatchDrawable

__all__ = [
    "ParticleCollection", "AbstractParticle",
    "Vec2", "Color",
    "LineParticle"
]

DEBUG = True
Color = Tuple[int, int, int, int]  # c4B
Vec2 = Tuple[float, float]  # v2f


def _monotonic_counter(initial: int=0):
    value = initial
    while True:
        yield value
        value += 1


_GLOBAL_ID = _monotonic_counter()


ParticleType = TypeVar("ParticleType", bound="AbstractParticle")


# noinspection PyProtectedMember
class ParticleCollection(BatchDrawable, Generic[ParticleType]):
    max: int
    active: int
    _verts: VertexList
    _inactive: Optional["ParticleType"] = None

    @staticmethod
    def enable_blending() -> None:
        # TODO this should be part of window setup, right?
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_SRC_ALPHA)
        gl.glEnable(gl.GL_LINE_SMOOTH)

    def __init__(
            self, particle_cls: Type["ParticleType"],
            particle_count: int=1000, batch: Optional[Batch]=None) -> None:
        super().__init__(batch=batch)
        self._verts = particle_cls.allocate_verts(particle_count, self.batch)

        self.active = self.max = particle_count
        for index in range(particle_count):
            self.free(particle_cls.new_instance(_collection=self, _index=index))
        assert self.active == 0

    def alloc(self) -> Optional["ParticleType"]:
        particle = self._inactive
        if particle is None:
            return None
        self._inactive = particle._next
        if DEBUG:
            particle._id = next(_GLOBAL_ID)
        self.active += 1
        return particle

    def free(self, particle: "ParticleType") -> None:
        if DEBUG:
            particle._id = None
        particle._next = self._inactive
        self._inactive = particle
        self.active -= 1


# noinspection PyProtectedMember
class AbstractParticle:
    vert_count: ClassVar[int]
    gl_mode: ClassVar[int]  # pyglet.gl.GL_LINES, pyglet.gl.GL_POINTS, etc.

    _collection: ParticleCollection
    _index: int
    _next: Optional["AbstractParticle"]
    _id: Optional[int]

    def __init__(self, _collection: ParticleCollection, _index: int) -> None:
        self._collection = _collection
        self._index = _index
        self._id = None

    def __eq__(self, other: "AbstractParticle") -> bool:
        try:
            return self._id == other._id
        except AttributeError:
            return False

    @classmethod
    def new_instance(cls, _collection: ParticleCollection, _index: int) -> "AbstractParticle":
        return cls(_collection=_collection, _index=_index)

    @classmethod
    def allocate_verts(cls, count: int, batch: Batch, group: Optional[Group]=None) -> VertexList:
        return batch.add(count * cls.vert_count, cls.gl_mode, group, "v2f/stream", "c4B/stream")

    def free(self) -> None:
        self._collection.free(self)

    def _get_vert(self, i: int) -> Vec2:
        start = 2 * (self._index * self.vert_count + i)
        return self._collection._verts.vertices[start: start + 2]

    def _set_vert(self, i: int, v: Vec2) -> None:
        start = 2 * (self._index * self.vert_count + i)
        self._collection._verts.vertices[start: start + 2] = v

    def _get_color(self, i: int) -> Color:
        start = 4 * (self._index * self.vert_count + i)
        return self._collection._verts.colors[start: start + 4]

    def _set_color(self, i: int, c: Color) -> None:
        start = 4 * (self._index * self.vert_count + i)
        self._collection._verts.colors[start: start + 4] = c

    def _get_alpha(self) -> int:
        start = 4 * (self._index * self.vert_count) + 3
        return self._collection._verts.colors[start]

    def _set_alpha(self, a: int) -> None:
        start = 4 * (self._index * self.vert_count) + 3
        end = start + 4 * self.vert_count
        self._collection._verts.colors[start: end: 4] = (a,) * self.vert_count


class LineParticle(AbstractParticle):
    vert_count = 2
    gl_mode = gl.GL_LINES

    @classmethod
    def new_instance(cls, _collection: ParticleCollection, _index: int) -> AbstractParticle:
        instance = super().new_instance(_collection, _index)
        instance.color = 255, 255, 255, 255
        return instance

    @property
    def p0(self) -> Vec2:
        return self._get_vert(0)

    @p0.setter
    def p0(self, v: Vec2) -> None:
        self._set_vert(0, v)

    @property
    def p1(self) -> Vec2:
        return self._get_vert(1)

    @p1.setter
    def p1(self, v: Vec2) -> None:
        self._set_vert(1, v)

    @property
    def color(self) -> Color:
        return self._get_color(0)

    @color.setter
    def color(self, c: Color) -> None:
        self._set_color(0, c)
        self._set_color(1, c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)
