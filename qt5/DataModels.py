#!/usr/bin/python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject


class Geometry(QObject):
    """A region

    """
    changed = pyqtSignal(int)

    def __init__(self):
        super(Geometry, self).__init__()

    @abstractmethod
    def toString(self):
        """convert this object to SVG tag
        :return:
        """

    @abstractmethod
    def toPolies(self):
        """
        Convert this geometry to a set of polygons
        :return:
        """

    @property
    @abstractmethod
    def control_points(self):
        """
        Return control points
        :return:
        """

    @control_points.setter
    @abstractmethod
    def control_points(self, points):
        """
        set control points, remember to call self.update
        :param points:
        :return:
        """

    def update(self, change=0):
        """
        notify all the listeners that the geometry has changed
        :param change: 0 = default change
        :return:
        """
        self.changed.emit(change)


class Group(Geometry):
    def __init__(self, geometries):
        """

        :param geometries: must be a list of Geometry
        """
        super(Group, self).__init__()
        self._geos = geometries

    @property
    def geometries(self):
        return self._geos

    @geometries.setter
    def geometries(self, value):
        if not isinstance(value, list):
            raise ValueError('value must be a list')

        if sum([issubclass(v.__class__, Geometry) for v in value]) == len(value):
            self._geos = value
        else:
            raise ValueError('objects in the list must be Geometry')

    def toString(self):
        return 'group'

    def toPolies(self):
        return [geo.toPolies() for geo in self.geometries]


class Polyline(Geometry):
    def __init__(self, points):
        self._points = np.array(points)
        if len(self._points.shape) != 2:
            raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Polyline, self).__init__()

    def toString(self):
        return 'polyline'

    def toPolies(self):
        return self._points[None, ...]

    @property
    def control_points(self):
        return self._points

    @control_points.setter
    def control_points(self, points):
        self._points = points


class Rect(Geometry):
    def __init__(self, x, y, width, height):
        self._x, self._y, self._width, self._height = x, y, width, height
        super(Rect, self).__init__()

    @property
    def x(self): return self._x

    @x.setter
    def x(self, value): self._x = value

    @property
    def y(self): return self._y

    @y.setter
    def y(self, value): self._y = value

    @property
    def width(self): return self._width

    @width.setter
    def width(self, value): self._width = value

    @property
    def height(self): return self._height

    @height.setter
    def height(self, value): self._height = value

    @property
    def control_points(self):
        return np.array([[self._x, self._y], [self._x + self._width, self._y + self._height]])

    @control_points.setter
    def control_points(self, points):
        if points.shape == (2, 2):
            self._x, self._y, self._width, self._height = \
                points[0][0], points[0][1], abs(points[1][0] - points[0][0]), abs(points[1][1] - points[0][1])

    def toString(self):
        return 'rectangle'

    def toPolies(self):
        return np.array([])


class Box(Rect):
    def __init__(self, a, x=0, y=0):
        super(Box, self).__init__(x, y, width=a, height=a)

    def toString(self):
        return 'box'


class Circle(Geometry):
    def __init__(self, x, y, r):
        self.x, self.y, self.r = x, y, r
        super(Circle, self).__init__()

    @property
    def center(self):
        return np.array([self.x, self.y])

    @center.setter
    def center(self, value):
        self.x, self.y = value[0], value[1]

    @property
    def control_points(self):
        return np.array([[self.x, self.y], [self.x + self.r, self.y]])

    @control_points.setter
    def control_points(self, points):
        if len(points) >= 2:
            self.x, self.y = points[0][0], points[0][1]
            self.r = np.linalg.norm(points[0] - points[1])
            # self.update()

    def toString(self):
        return 'circle'

    def toPolies(self):
        return np.array([])


class Point(Geometry):
    def __init__(self, x, y):
        self._x = x
        self._y = y
        super(Point, self).__init__()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    def toString(self):
        return 'point'

    def toPolies(self):
        return np.array([[[self._x, self._y]]])


class Line(Polyline):
    def __init__(self, x0, y0, x1, y1):
        super(Line, self).__init__([[x0, y0], [x1, y1]])

    def toString(self):
        return 'line'


class Spline(Geometry):
    def __init__(self, points):
        self._points = np.array(points)
        if len(self._points.shape) != 2:
            raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Spline, self).__init__()

    def toString(self):
        return 'polyline'

    def toPolies(self):
        return self._points[None, ...]


class AnnotationModel(object):
    """Model for Annotating Objects

    """
    def __init__(self):
        self._region = Geometry()

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        self._region = value


if __name__ == '__main__':
    l = Line(0, 0, 1, 1)
    pl = Polyline([[3, 3], [4, 4]])
    print(l.toString())
    print(pl.toString())