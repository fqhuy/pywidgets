#!/usr/bin/python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from skimage import draw
import json


class Geometry(QObject):
    """A region

    """
    changed = pyqtSignal(int)
    ControlPointPositionHasChanged = 0

    def __init__(self):
        super(Geometry, self).__init__()

    def _jsonTemplate(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "",
                "coordinates": []
            },
            "properties": {
                "label": ""
            }
        }

    # @abstractmethod
    def toString(self):
        """convert this object to a string for serialization
        :return:
        """
        d = self._jsonTemplate()
        d['geometry']['coordinates'] = self.control_points.tolist()
        d['properties']['label'] = type(self).__name__
        return json.dumps(d)

    # @abstractmethod
    def fromString(self, string):
        """
        parse a string and return a Geometry object
        :return:
        """
        d = json.loads(string)
        self.control_points = np.array(d['geometry']['coordinates'])

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
        string = ""
        for geo in self.geometries:
            string += super(Group, self).toString(geo)

        return string

    def fromString(self, text):
        # TODO: Under construction
        features = json.loads(text)
        geos = []
        for feature in features:
            tmp = json.dumps(feature)
            # geos.append(super())

    def toPolies(self):
        return [geo.toPolies() for geo in self.geometries]

    @property
    def control_points(self):
        return np.array([])


class Polyline(Geometry):
    def __init__(self, points):
        self._points = np.array(points)
        if len(self._points.shape) != 2:
            raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Polyline, self).__init__()

    def toPolies(self):
        return self._points[None, ...]

    @property
    def control_points(self):
        return self._points

    @control_points.setter
    def control_points(self, points):
        self._points = points

    def addControlPoints(self, points):
        self.control_points = np.concatenate([self.control_points, points])
        self.update()


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

    def toPolies(self):
        return np.array([])


class Box(Rect):
    def __init__(self, a, x=0, y=0):
        super(Box, self).__init__(x, y, width=a, height=a)


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

    def toPolies(self):
        return np.array([])


class Ring(Geometry):
    def __init__(self, x, y, inner_r, outer_r):
        self.x, self.y, self.inner_r, self.outer_r = x, y, inner_r, outer_r
        super(Ring, self).__init__()

    @property
    def center(self):
        return np.array([self.x, self.y])

    @center.setter
    def center(self, value):
        self.x, self.y = value[0], value[1]

    @property
    def control_points(self):
        return np.array([[self.x, self.y], [self.x + self.inner_r, self.y], [self.x + self.outer_r, self.y]])

    @control_points.setter
    def control_points(self, points):
        if len(points) == 3:
            self.x, self.y = points[0][0], points[0][1]
            self.inner_r = np.linalg.norm(points[0] - points[1])
            self.outer_r = np.linalg.norm(points[0] - points[2])

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

    def toPolies(self):
        return np.array([[[self._x, self._y]]])


class Line(Polyline):
    def __init__(self, x0, y0, x1, y1):
        super(Line, self).__init__([[x0, y0], [x1, y1]])


class Spline(Geometry):
    def __init__(self, points):
        self._points = np.array(points)
        if len(self._points.shape) != 2:
            raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Spline, self).__init__()

    def toPolies(self):
        # TODO: implement this
        return self._points[None, ...]

    @property
    def control_points(self):
        return self._points

    @control_points.setter
    def control_points(self, points):
        if len(points) >= 4:
            self._points = np.array(points)

    def addControlPoints(self, points):
        if len(points) == 1:
            cur_point = self.control_points[-1]
            end_point = points[0]
            diff = end_point - cur_point
            mid_point = diff / 2 + cur_point
            c_point1 = diff * np.array([1, -1]) + mid_point
            c_point2 = diff * np.array([-1, 1]) + mid_point
            self.control_points = np.concatenate([self.control_points, [c_point1, c_point2, end_point]])
        # elif len(points) == 3:
        self.update()


class MultiSpline(Group):
    def __init__(self, points):
        splines = []
        for ps in points:
            splines.append(Spline(ps))
        super(MultiSpline, self).__init__(splines)


class MultiPolygon(Group):
    def __init__(self, points):
        polygons = []
        for ps in points:
            polygons.append(Spline(ps))
        super(MultiPolygon, self).__init__(polygons)


class AnnotationModel(Group):
    """Model for Annotating Objects

    """
    def __init__(self, regions, label):
        """
        :param regions: list of Geometries
        :param label:
        """
        self._label = label
        super(AnnotationModel, self).__init__(regions)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, text):
        self._label = text

    # def toString(self):
    #     pass
    #
    # def fromString(self):
    #     pass

    def toMask(self, mode='auto', shape=None):
        """
        convert to a binary mask
        :param mode
        :type str
        :param shape
        :return:
        """
        if mode == 'auto':
            polies = self.toPolies()
            points = np.vstack(polies)
            xmax, ymax = tuple(points.max(axis=0))
            xmin, ymin = tuple(points.min(axis=0))
            w, h = xmax - xmin, ymax - ymin

            mask = np.zeros((ymax - ymin, xmax - xmin), dtype=np.uint8)
            for poly in polies:
                poly1 = poly - np.array([xmin, ymin])
                rr, cc = draw.polygon(poly1[:, 1], poly[:, 0], shape=(h, w))
                mask[rr, cc] = 1
        elif isinstance(shape, tuple):
            mask = np.zeros(shape, dtype=np.uint8)
            polies = self.toPolies()
            for poly in polies:
                rr, cc = draw.polygon(poly[:, 1], poly[:, 0], shape=shape)
                mask[rr, cc] = 1
        else:
            mask = None

        return mask

if __name__ == '__main__':
    l = Line(0, 0, 1, 1)
    pl = Polyline([[3, 3], [4, 4]])
    print(l.toString())
    print(pl.toString())