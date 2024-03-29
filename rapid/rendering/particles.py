from typing import ClassVar, Generic, Optional, Tuple, Type, TypeVar

from pyglet import gl
from pyglet.graphics import Batch, Group
from pyglet.graphics.vertexdomain import VertexList

from ..util import Vec2
from .primitives.geometry import circle, rectangle
from .util import Color, GLMode, flatten


# When True, particles are assigned a unique id every time they are allocated
DEBUG = True


def _monotonic_counter(initial: int=0):
    value = initial
    while True:
        yield value
        value += 1


_GLOBAL_ID = _monotonic_counter()


ParticleType = TypeVar("ParticleType", bound="AbstractParticle")


# noinspection PyProtectedMember
class ParticleCollection(Generic[ParticleType]):
    max: int
    active: int
    delete_on_last_free: bool
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
            particle_count: int=1000,
            delete_on_last_free: bool=False, *, batch: Batch) -> None:
        self._verts = particle_cls.allocate_verts(particle_count, batch)
        self.delete_on_last_free = delete_on_last_free

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
        if self.delete_on_last_free and not self.active:
            del self

    def __del__(self):
        if self._verts:
            self._verts.delete()
            self._verts = None
        if DEBUG:
            print("Cleaned up ParticleCollection")

    def iterator(self):
        """Temporarily allocate all available particles for iteration.

        .. code-block:: pycon

            >>> collection = ParticleCollection(LineParticle)
            >>> with collection.iterator() as it:
            ...     for particle in it:
            ...         particle.color = 255, 0, 0, 255
        """
        return CollectionIterator(self)


class CollectionIterator(Generic[ParticleType]):
    """Temporarily allocate all available particles for iteration.

    .. code-block:: pycon

        >>> collection = ParticleCollection(LineParticle)
        >>> with collection.iterator() as it:
        ...     for particle in it:
        ...         particle.color = 255, 0, 0, 255
    """
    def __init__(self, collection: ParticleCollection) -> None:
        self.collection = collection
        self.allocated = []

    def __enter__(self):
        particle = self.collection.alloc()
        while particle:
            self.allocated.append(particle)
            particle = self.collection.alloc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for particle in self.allocated:
            particle.free()
        del self.allocated

    def __iter__(self):
        return iter(self.allocated)


# noinspection PyProtectedMember
class AbstractParticle:
    vert_count: ClassVar[int]
    gl_mode: ClassVar[GLMode]

    _collection: ParticleCollection
    _index: int
    _next: Optional["AbstractParticle"]
    _id: Optional[int]

    def __init__(self, _collection: ParticleCollection, _index: int) -> None:
        self._collection = _collection
        self._index = _index
        self._id = None

    __hash__ = object.__hash__

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
        return batch.add(count * cls.vert_count, cls.gl_mode.gl_mode, group, "v2f/stream", "c4B/stream")

    def free(self) -> None:
        self._collection.free(self)

    def _get_vert(self, i: int) -> Vec2:
        start = 2 * (self._index * self.vert_count + i)
        return self._collection._verts.vertices[start: start + 2]

    def _set_vert(self, i: int, v: Vec2) -> None:
        start = 2 * (self._index * self.vert_count + i)
        self._collection._verts.vertices[start: start + 2] = v

    def _set_verts(self, verts: Tuple[float, ...]) -> None:
        assert len(verts) == 2 * self.vert_count
        start = 2 * (self._index * self.vert_count)
        self._collection._verts.vertices[start: start + 2 * self.vert_count] = verts

    def _get_color(self, i: int) -> Color:
        start = 4 * (self._index * self.vert_count + i)
        return self._collection._verts.colors[start: start + 4]

    def _set_color(self, i: int, c: Color) -> None:
        start = 4 * (self._index * self.vert_count + i)
        self._collection._verts.colors[start: start + 4] = c

    def _set_colors(self, c: Color) -> None:
        start = 4 * (self._index * self.vert_count)
        self._collection._verts.colors[start: start + 4 * self.vert_count] = c * self.vert_count

    def _get_alpha(self) -> int:
        start = 4 * (self._index * self.vert_count) + 3
        return self._collection._verts.colors[start]

    def _set_alpha(self, a: int) -> None:
        start = 4 * (self._index * self.vert_count) + 3
        end = start + 4 * self.vert_count
        self._collection._verts.colors[start: end: 4] = (a,) * self.vert_count


class PointParticle(AbstractParticle):
    vert_count = 1
    gl_mode = GLMode.Points

    @classmethod
    def new_instance(cls, _collection: ParticleCollection, _index: int) -> AbstractParticle:
        instance = super().new_instance(_collection, _index)
        instance.color = 255, 255, 255, 255
        return instance

    @property
    def pos(self) -> Vec2:
        return self._get_vert(0)

    @pos.setter
    def pos(self, v: Vec2) -> None:
        self._set_vert(0, v)

    @property
    def color(self) -> Color:
        return self._get_color(0)

    @color.setter
    def color(self, c: Color) -> None:
        self._set_colors(c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)


class LineParticle(AbstractParticle):
    vert_count = 2
    gl_mode = GLMode.Lines

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
        self._set_colors(c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)


class TriangleParticle(AbstractParticle):
    vert_count = 3
    gl_mode = GLMode.Triangles

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
    def p2(self) -> Vec2:
        return self._get_vert(2)

    @p2.setter
    def p2(self, v: Vec2) -> None:
        self._set_vert(2, v)

    @property
    def color(self) -> Color:
        return self._get_color(0)

    @color.setter
    def color(self, c: Color) -> None:
        self._set_colors(c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)


# noinspection PyAttributeOutsideInit
class CircleParticle(AbstractParticle):
    # You should subclass CircleParticle to modify the resolution
    # Make sure this is the vert count, and not the number of triangles.
    # For example, 20 slices requires 60 verts
    vert_count = 20 * 3
    gl_mode = GLMode.Triangles

    _radius: float
    _center: Vec2

    def __init__(self, _collection: ParticleCollection, _index: int) -> None:
        super().__init__(_collection, _index)
        self._radius = 0
        self._center = Vec2.Zero

    @property
    def center(self) -> Vec2:
        return self._center

    @center.setter
    def center(self, c: Vec2) -> None:
        self._center = c
        self._recalculate_verts()

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, r: float) -> None:
        self._radius = r
        self._recalculate_verts()

    @classmethod
    def new_instance(cls, _collection: ParticleCollection, _index: int) -> AbstractParticle:
        instance = super().new_instance(_collection, _index)
        instance.color = 255, 255, 255, 255
        instance.radius = 0
        return instance

    def _recalculate_verts(self) -> None:
        self._set_verts(tuple(flatten(circle(
            center=self.center,
            r=self.radius,
            resolution=int(self.vert_count // 3),
            mode=self.gl_mode))))

    @property
    def color(self) -> Color:
        return self._get_color(0)

    @color.setter
    def color(self, c: Color) -> None:
        self._set_colors(c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)


class RectangleParticle(AbstractParticle):
    vert_count = 4
    gl_mode = GLMode.Quads

    _center: Vec2
    _width: float
    _height: float
    _rotation: float

    def __init__(self, _collection: ParticleCollection, _index: int) -> None:
        super().__init__(_collection, _index)
        self._center = Vec2.Zero
        self._width = self._height = self._rotation = 0

    @property
    def center(self) -> Vec2:
        return self._center

    @center.setter
    def center(self, c: Vec2) -> None:
        self._center = c
        self._recalculate_verts()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, r: float) -> None:
        self._rotation = r
        self._recalculate_verts()

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, w: float) -> None:
        self._width = w
        self._recalculate_verts()

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, h: float) -> None:
        self._height = h
        self._recalculate_verts()

    @classmethod
    def new_instance(cls, _collection: ParticleCollection, _index: int) -> AbstractParticle:
        instance = super().new_instance(_collection, _index)
        instance.color = 255, 255, 255, 255
        instance.width = instance.height = instance.rotation = 0
        return instance

    def _recalculate_verts(self) -> None:
        self._set_verts(tuple(flatten(rectangle(
            center=self.center,
            width=self.width,
            height=self.height,
            rotation=self.rotation,
            mode=self.gl_mode))))

    @property
    def color(self) -> Color:
        return self._get_color(0)

    @color.setter
    def color(self, c: Color) -> None:
        self._set_colors(c)

    def set_alpha(self, a: int) -> None:
        self._set_alpha(a)


def single_particle(particle_cls: Type[ParticleType], *, batch: Batch) -> ParticleType:
    """Allocate a single particle from an anonymous pool"""
    pool = ParticleCollection(
        particle_cls=particle_cls,
        particle_count=1,
        delete_on_last_free=True,
        batch=batch)
    particle = pool.alloc()
    assert particle is not None
    return particle
