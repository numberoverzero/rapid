import inspect
from typing import ClassVar, Dict, Generic, Optional, TypeVar

import pyglet

from ...util import Vec2
from ..util import Color, GLMode, flatten
from .geometry import circle, rectangle


T = TypeVar("T")


class Shape:
    batch: pyglet.graphics.Batch
    mode: GLMode
    _cached_verts: Optional[pyglet.graphics.vertexdomain.VertexList] = None
    _shape_properties: ClassVar[Dict[str, "ShapeProperty"]]

    def __init__(self, *, batch: pyglet.graphics.Batch, mode: GLMode, **properties) -> None:
        self.batch = batch
        self.mode = mode
        for key, prop in self._shape_properties.items():
            if key not in properties:
                value = prop.default()
                if value is None:
                    raise TypeError(f"__init__() missing a required keyword-only argument: {key}")
                properties[key] = value
        self.update(**properties)

    def __init_subclass__(cls, **kwargs):
        cls._shape_properties = dict(inspect.getmembers(
            cls, lambda prop: isinstance(prop, ShapeProperty)
        ))

    def _invalidate_cached_verts(self, recalculate: bool=True) -> None:
        if self._cached_verts is not None:
            self._cached_verts.delete()
            if recalculate:
                self._recalculate_verts()
            else:
                self._cached_verts = None

    def _recalculate_verts(self) -> None:
        raise NotImplementedError

    def update(self, **properties) -> None:
        recalculate_verts = False
        for key, value in properties.items():
            prop = self._shape_properties[key]
            if value is not None:
                prop.__set__(self, value, recalculate_verts=False)
                recalculate_verts = True
        if recalculate_verts:
            self._recalculate_verts()

    def delete(self) -> None:
        self._invalidate_cached_verts(recalculate=False)


class ShapeProperty(Generic[T]):
    def __init__(self, default=None) -> None:
        if not callable(default):
            self.default = lambda: default
        else:
            self.default = default

    def __set_name__(self, owner, name):
        self.name = name

    # noinspection PyTypeChecker
    def __get__(self, instance: Shape, owner) -> T:
        if instance is None:
            return self
        try:
            return instance.__dict__[self.name]
        except KeyError:
            raise AttributeError(self.name)

    # noinspection PyProtectedMember
    def __set__(self, instance: Shape, value: T, recalculate_verts: bool=True) -> None:
        instance.__dict__[self.name] = value
        instance._invalidate_cached_verts(recalculate=recalculate_verts)


class Circle(Shape):
    center = ShapeProperty[Vec2]()
    radius = ShapeProperty[float]()
    resolution = ShapeProperty[int]()
    color = ShapeProperty[Color](default=Color(255, 255, 255, 255))

    def _recalculate_verts(self) -> None:
        verts = tuple(flatten(circle(self.center, self.radius, self.resolution, self.mode)))
        vcount = int(len(verts) // 2)
        self._cached_verts = self.batch.add(
            vcount, self.mode.gl_mode, None,
            ("v2f", verts),
            ("c4B", self.color * vcount),
        )


class Rectangle(Shape):
    center = ShapeProperty[Vec2]()
    width = ShapeProperty[float]()
    height = ShapeProperty[float]()
    rotation = ShapeProperty[float](default=0)
    color = ShapeProperty[Color]()

    def _recalculate_verts(self) -> None:
        verts = tuple(flatten(rectangle(self.center, self.width, self.height, self.rotation, self.mode)))
        vcount = int(len(verts) // 2)
        self._cached_verts = self.batch.add(
            vcount, self.mode.gl_mode, None,
            ("v2f", verts),
            ("c4B", self.color * vcount)
        )
