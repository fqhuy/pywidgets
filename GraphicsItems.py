# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 07:32:13 2015

@author: phanquochuy
"""

from PyQt5 import QtGui
from PyQt5.QtCore import (QPointF, QRectF, Qt)
from PyQt5.QtGui import (QColor, QBrush, QFont, QPen, QTransform, QPainterPath)
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QGraphicsTextItem)

from .DataModels import *
from .Common import *
from .Utils import _NP, _QP

DEFAULT_COLOR = QColor(255, 255, 150, 50)
DEFAULT_HIGH_COLOR = Qt.yellow
DEFAULT_EDGE_COLOR = Qt.black
DEFAULT_HIGH_EDGE_COLOR = Qt.blue
DEFAULT_HANDLE_COLOR = Qt.green
DEFAULT_HANDLE_SIZE = 10
DEFAULT_EDGE_WIDTH = 2
DEFAULT_ANN_EDGE_STYLE = Qt.DashLine
DEFAULT_ANN_EDGE_WIDTH = 1.5
DEFAULT_IDMAN = IDManager()


def dataModel2GraphicsItem(model):
    if isinstance(model, str):
        return globals()[model + 'Item']


class ControllableItem(QGraphicsItem):
    """ A controllable graphics item has handles

    """
    # deleted = pyqtSignal(int, name='itemDeleted')
    HandlePositionHasChanged = 100

    def __init__(self, model, color=DEFAULT_COLOR, parent=None, label="item", handle_size=DEFAULT_HANDLE_SIZE,
                 handle_color=DEFAULT_HANDLE_COLOR,
                 edge_color=DEFAULT_EDGE_COLOR, edge_width=DEFAULT_EDGE_WIDTH):
        """
        :param model: must be a subclass of DataModels.Geometry
        :param color: fill color
        :param parent: parent object
        :param label: a label for this item
        :param handle_size: size of the handls
        :param handle_color: color of the handles
        :param edge_color:
        :param edge_width:
        """
        super(ControllableItem, self).__init__(parent)
        # if not issubclass(model.__class__, Geometry):
        #     raise ValueError('Invalid model, need to be a subclass of Geometry')

        self._model = model
        self._model.changed.connect(self.modelChanged)

        self._controls = []
        self._handle_size = handle_size
        self._handle_color = handle_color
        self._color = color
        self._edge_color = edge_color

        # the bounding rectangle
        self._rect = QRectF(0, 0, 100, 100)
        self._idd = DEFAULT_IDMAN.next()
        self._edge_width = edge_width

        # self.setFlags(self.flags() |
        #               QGraphicsItem.ItemIsSelectable |
        #               QGraphicsItem.ItemSendsGeometryChanges |
        #               QGraphicsItem.ItemIsFocusable)

        # create handles from control points
        self.control_points = self.model.control_points

        self._label = QGraphicsTextItem(label, self)
        self._label.setPos(QPointF(self.rect.x(), self.rect.y()))
        self._label.setFont(QFont('', 40))

        self._updateRect()

    def itemChange(self, change, value):
        """
        tell the inner model to update itself with new control points, also notifies other Items sharing this model
        :param change:
        :param value:
        :return:
        """
        if change == self.HandlePositionHasChanged:
            self.model.control_points = self.control_points
            self.update()

        return super(ControllableItem, self).itemChange(change, value)

    def modelChanged(self, change=0):
        self.control_points = self.model.control_points
        # print('model changed')

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value):
        self._rect = value

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if issubclass(value.__class__, Geometry):
            self._model = value
        else:
            raise(ValueError('Must be a subclass of Geometry'))

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        if isinstance(value, str):
            self._label = QGraphicsTextItem(value)
        else:
            raise ValueError('label must be a string')

    @property
    def edge_width(self):
        return self._edge_width

    @edge_width.setter
    def edge_width(self, value):
        self._edge_width = value

    @property
    def half_edge_width(self):
        return self.edge_width / 2.

    @property
    def idd(self):
        return self._idd

    @idd.setter
    def idd(self, value):
        self._idd = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.update()

    @property
    def handle_color(self):
        return self._handle_color

    @handle_color.setter
    def handle_color(self, value):
        self._handle_color = value
        self.update()

    @property
    def handle_size(self):
        return self._handle_size

    @handle_size.setter
    def handle_size(self, value):
        self._handle_size = value
        self.update()

    @property
    def edge_color(self):
        return self._edge_color

    @edge_color.setter
    def edge_color(self, value):
        self._edge_color = value
        self.update()

    @property
    def controls(self):
        return self._controls

    @property
    def control_points(self):
        """
        :return: control points from self._controls
        """
        return np.array([[cp.x(), cp.y()] for cp in self._controls])

    @control_points.setter
    def control_points(self, points):
        for ctr in self._controls:
            self.scene().removeItem(ctr)
            del ctr

        self._controls = []
        for cp in points:
            self.addHandle(cp)

        self._updateRect()

    @abstractmethod
    def _paintMe(self, qp, option, widget):
        """
        Paint the main part of this widget, subclass should impl this
        :param qp:
        :param option:
        :param widget:
        :return:
        """

    @abstractmethod
    def _updateRect(self):
        """
        update the bounding box
        :return:
        """

    def _adjustEdge(self, rect):
        """
        adjust bounding rect to
        :param rect:
        :return:
        """
        return rect.adjusted(-self.half_edge_width, -self.half_edge_width, self.half_edge_width, self.half_edge_width)

    def addHandle(self, pos):
        control = HandleItem(_QP(pos), parent=self, color=self.handle_color)
        self._controls.append(control)
        return control

    def hideHandles(self):
        for c in self._controls:
            c.setVisible(False)

    def paint(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.edge_color), self.edge_width))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        self._paintMe(qp, option, widget)
        for c in self._controls:
            c.paint(qp, option, widget)

        self.label.paint(qp, option, widget)
        if self.isSelected():
            qp.setPen(QPen(QBrush(self.color), self.edge_width, Qt.DotLine))
            qp.drawRect(self.boundingRect())

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def moveBy(self, dx, dy):
        for control in self.controls:
            control.setPos(control.x() + dx, control.y() + dy)

    def scaleBy(self, sx, sy):
        for control in self.controls:
            control.setPos(control.x() * sx, control.y() * sy)


class GroupItem(ControllableItem):
    def __init__(self, items, **kwargs):
        model = Group([item.model for item in items])
        super(GroupItem, self).__init__(model, **kwargs)
        for item in items:
            item.setParentItem(self)

    def mousePressEvent(self, e):
        for ch in self.childItems():
            self.scene().sendEvent(ch, e)
            
    def _updateRect(self):
        x1, y1, x2, y2 = [], [], [], []
        for item in self.childItems():
            x1.append(item.boundingRect().x())
            y1.append(item.boundingRect().y())
            x2.append(item.boundingRect().right())
            y2.append(item.boundingRect().bottom())
        if len(x1) > 0:    
            self.rect = QRectF(min(x1), min(y1), max(x2) - min(x1), max(y2) - min(y1))
        else:
            self.rect = QRectF(self.x(), self.y(), 100, 100)
            
    def _paintMe(self, painter, option, widget=None):
        for child in self.childItems():
            child._paintMe(painter, option, widget)
    
    def addItem(self, item):
        item.setParentItem(self)
        if self.scene() is not None:
            self.scene().activeSubItem = item
        return item
    
    # def setZValue(self, p_float):
    #     for child in self.childItems():
    #         child.setZValue(p_float)
    #
    #     super(GroupItem, self).setZValue(p_float)

    # @property
    # def control_points(self):
    #     points = []
    #     for child in self.childItems():
    #         points.append(child.control_points)
    #
    #     return points

    # def toPolies(self):
    #     points = []
    #     for child in self.childItems():
    #         points.append(child.toPolies())
    #
    #     return points


class PolylineItem(ControllableItem):
    def _paintMe(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.edge_color), 5))
        qp.drawPolyline(*[c.pos() for c in self.controls])

    def _updateRect(self):
        pos = self.model.control_points
        if len(pos) > 0:
            xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
            self.rect = self._adjustEdge(QRectF(xmin, ymin, xmax - xmin, ymax - ymin))

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() == Qt.ControlModifier:
            self.model.addControlPoints(_NP(e.scenePos())[None, ...])
            # self.addHandle(_NP(e.scenePos()))


class RectItem(ControllableItem):
    def _updateRect(self):
        self.rect = self._adjustEdge(QRectF(self.model.x, self.model.y, self.model.width, self.model.height))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawRect(self.model.x, self.model.y, self.model.width, self.model.height)


class CircleItem(ControllableItem):
    def _updateRect(self):
        center = self.model.center
        r = self.model.r
        self.rect = self._adjustEdge(QRectF(center[0] - r, center[1] - r, r * 2, r * 2))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawEllipse(_QP(self.model.center), self.model.r, self.model.r)


class RingItem(ControllableItem):
    def _updateRect(self):
        center = self.model.center
        r = self.model.outer_r
        self.rect = self._adjustEdge(QRectF(center[0] - r, center[1] - r, r * 2, r * 2))

    def _paintMe(self, qp, option, widget=None):
        qp.drawEllipse(_QP(self.model.center), self.model.outer_r, self.model.outer_r)
        qp.drawEllipse(_QP(self.model.center), self.model.inner_r, self.model.inner_r)


class SRectItem(ControllableItem):
    def _updateRect(self):
        center = self.model.center
        r1 = self.model.outer_r
        self.rect = self._adjustEdge(QRectF(center[0] - r1, center[1] - r1, r1 * 2, r1 * 2))

    def _paintMe(self, qp, option, widget=None):
        x, y = self.model.center[0] - self.model.inner_r, self.model.center[1] - self.model.inner_r
        qp.drawRect(x, y, self.model.inner_r * 2, self.model.inner_r * 2)

        x, y = self.model.center[0] - self.model.outer_r, self.model.center[1] - self.model.outer_r
        qp.drawRect(x, y, self.model.outer_r * 2, self.model.outer_r * 2)


class SplineItem(ControllableItem):
    def _paintMe(self, qp, option, widget=None):
        path = QPainterPath(_QP(self.model.control_points[0]))
        ann_path = QPainterPath()
        cur_point = 0
        while cur_point < len(self.model.control_points) - 1:
            path.cubicTo(_QP(self.model.control_points[cur_point + 1]),
                         _QP(self.model.control_points[cur_point + 2]),
                         _QP(self.model.control_points[cur_point + 3]))

            ann_path.moveTo(_QP(self.model.control_points[cur_point + 0]))
            ann_path.lineTo(_QP(self.model.control_points[cur_point + 1]))
            ann_path.moveTo(_QP(self.model.control_points[cur_point + 3]))
            ann_path.lineTo(_QP(self.model.control_points[cur_point + 2]))

            cur_point += 3

        qp.drawPath(path)
        qp.setPen(QPen(DEFAULT_ANN_EDGE_STYLE))
        qp.drawPath(ann_path)

    def __len__(self):
        return len(self.controls)

    def _updateRect(self):
        pos = self.model.toPolies()[0]
        xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
        self.rect = self._adjustEdge(QRectF(xmin, ymin, xmax - xmin, ymax - ymin))

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() == Qt.ControlModifier:
            self.model.addControlPoints(_NP(e.scenePos())[None, :])

        
class HandleItem(QGraphicsItem):
    def __init__(self, position, size=DEFAULT_HANDLE_SIZE, parent=None, color=Qt.green):
        super(HandleItem, self).__init__(parent)
        self.setPos(position)
        self.size = size
        self.color = color
        self.idd = DEFAULT_IDMAN.next()
        # self.setZValue(10)
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)
        self.rect = QRectF(0, 0, size, size)
                    
    def boundingRect(self):
        size = self.size
        return self.rect.adjusted(-size,-size,0,0)
        
    def paint(self, painter, option, widget=None):
        qp = painter
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        # size = self.size
        qp.drawEllipse(self.boundingRect())
    
    def points(self):
        return [[self.x(), self.y()]]

    def mousePressEvent(self, e):
        pass
        # if e.button() == 1:
        #     self.parentItem().main.bringToFront(self.parentItem().idd)
        # if e.button() == 2:
        #     self.parentItem().main.remove(self)
            
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.parentItem().itemChange(ControllableItem.HandlePositionHasChanged, value)
        return super(HandleItem, self).itemChange(change, value)
        
    def setSize(self, size):
        self.prepareGeometryChange()
        self.size = size
        self.rect = QRectF(0,0,size,size)
        
    def setColor(self, color):
        self.color = color
        self.update()


if __name__ == '__main__':
    geo1 = ControllableItem(Polyline([[0, 1]]))
    geo2 = ControllableItem(Polyline([[0, 1]]))
    geo3 = ControllableItem(Polyline([[0, 1]]))

    print(DEFAULT_IDMAN.ids)