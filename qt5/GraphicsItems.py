# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 07:32:13 2015

@author: phanquochuy
"""

from PyQt5 import QtGui
from PyQt5.QtCore import (QByteArray, QDataStream, QFile, QFileInfo,
        QIODevice, QPoint, QPointF, QRectF, Qt, QRect, QSize, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QColor, QBrush, QPixmap, QPainter, QBitmap, QIcon, QFont, QPen, QTransform)
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QGraphicsTextItem)

import numpy as np
from scipy.spatial.distance import euclidean as euc
from pywidgets.qt5.DataModels import *
from pywidgets.qt5.Common import *
from pywidgets.qt5.Utils import _NC, _NP, colorPixmap, _QC, _QP, _circle_to_poly

DEFAULT_COLOR = Qt.white
DEFAULT_HIGH_COLOR = Qt.yellow
DEFAULT_EDGE_COLOR = Qt.black
DEFAULT_HIGH_EDGE_COLOR = Qt.blue
DEFAULT_HANDLE_COLOR = Qt.green
DEFAULT_HANDLE_SIZE = 10
DEFAULT_EDGE_WIDTH = 2
DEFAULT_IDMAN = IDManager()


class InteractiveScene(QGraphicsScene):
    def __init__(self, parent=None):
        # self._active_item = None
        self._layer_stack = LayerStack()
        super(InteractiveScene, self).__init__(parent)

    def addItem(self, item):
        self._layer_stack.addItemToCurrentLayer(item)
        super(InteractiveScene, self).addItem(item)

    def mousePressEvent(self, e):
        """
        if the user click on an item, set it to the current_item in the LayerStack.
        :param e:
        :return:
        """
        pos = e.scenePos()
        items = [item for item in self.items(pos) if issubclass(item.__class__, ControllableItem)]

        if len(items) == 0 and self._layer_stack.hasCurrentItem():
            self.sendEvent(self._layer_stack.current_item, e)
            return super(InteractiveScene, self).mousePressEvent(e)

        for item in items:
            if item.idd == self._layer_stack.current_item_id:
                self.sendEvent(item, e)
                return super(InteractiveScene, self).mousePressEvent(e)

        item = self.itemAt(pos.x(), pos.y(), QTransform())
        if item in self._layer_stack:
            self._layer_stack.current_item = item

        return super(InteractiveScene, self).mousePressEvent(e)


class ControllableItem(QGraphicsItem):
    """ A controllable graphics item has handles

    """
    # deleted = pyqtSignal(int, name='itemDeleted')

    def __init__(self, model, color=DEFAULT_COLOR, parent=None, label="item", handle_size=10,
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
        if not issubclass(model.__class__, Geometry):
            raise ValueError('Invalid model, need to be a subclass of Geometry')

        self._model = model
        self._model.changed.connect(self.modelChanged)

        self._controls = []
        self._handle_size = handle_size
        self._handle_color = handle_color
        self._color = color
        self._edge_color = edge_color

        # create handles from control points
        cpoints = model.control_points
        for cp in cpoints:
            self.addHandle(cp)

        # the bounding rectangle
        self._rect = QRectF(0, 0, 100, 100)
        self._idd = DEFAULT_IDMAN.next()
        self._edge_width = edge_width

        # self.setFlags(self.flags() |
        #               QGraphicsItem.ItemIsSelectable |
        #               QGraphicsItem.ItemSendsGeometryChanges |
        #               QGraphicsItem.ItemIsFocusable)

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
        # print('item changed')
        self.model.control_points = self.control_points
        self.update()
        return super(ControllableItem, self).itemChange(change, value)

    def modelChanged(self, change=0):
        pass
        # self.control_points
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


class LayerStack(object):
    MAX_N_ITEMS_PER_LAYER = 1000

    def __init__(self):
        self._layers = [LayerItem(self, 'default', None)]
        self._current_layer_id = self._layers[0].idd
        self._current_item_id = -1

    def __contains__(self, item):
        try:
            re = self.itemById(item.idd)
        except ValueError:
            return False

        return True

    @property
    def current_item_id(self):
        # if self.current_item_id in self.current_layer.items:
        return self._current_item_id
        # else:
        #     return -1

    @current_item_id.setter
    def current_item_id(self, idd):
        if self.itemById(idd) in self:
            self._current_layer_id = self.layerByItemId(idd)
            self._current_item_id = idd
        else:
            raise ValueError('item is not managed by this stack')

    @property
    def current_item(self):
        return self.itemById(self.current_item_id)

    @current_item.setter
    def current_item(self, item):
        self.current_item_id = item.idd
        self.current_layer_id = self.layerByItemId(item.idd).idd

    @property
    def current_layer_id(self):
        return self._current_layer_id

    @current_layer_id.setter
    def current_layer_id(self, layer_id):
        if self.layerById(layer_id) in self._layers:
            self._current_layer_id = layer_id
            self._current_item_id = self.layerById(layer_id)[1].items[-1].idd

    @property
    def current_layer(self):
        return self.layerById(self.current_layer_id)[1]

    def itemById(self, item_id):
        for lx, l in enumerate(self._layers):
            for item in l.items:
                if item.idd == item_id:
                    return item

        raise ValueError('item not found!')

    def layerByItemId(self, item_id):
        item = self.itemById(item_id)
        return item.parentItem().idd

    def layerById(self, layer_id):
        for lx, l in enumerate(self._layers):
            if l.idd == layer_id:
                return lx, l

        raise ValueError('layer not found!')

    def layerIndexById(self, layer_id):
        lx, l = self.layerById(layer_id)
        return lx

    def hasCurrentItem(self):
        return self.current_item_id > 0

    def push(self, layer):
        next_key = len(self._layers) + 1
        self._layers[next_key] = layer

    def pop(self):
        if len(self._layers) > 0:
            return self._layers[ len(self._layers) - 1]
        else:
            raise IndexError('queue is empty')

    def addItem(self, item, layer_id):
        """
        add an item to a layer, adjust the item's order accordingly
        :param item:
        :param layer_id:
        :return:
        """
        lx, l = self.layerById(layer_id)
        l.addItem(item)

    def addItemToCurrentLayer(self, item):
        """
        add an item to the current layer
        :param item:
        :return:
        """
        self.current_layer.addItem(item)
        self.current_item_id = item.idd

    def swap(self, item_id1, item_id2):
        lx1, l1 = self.layerById(item_id1)
        lx2, l2 = self.layerById(item_id2)
        if l1 is not None and l2 is not None:
            self._layers[lx1] = l2
            self._layers[lx2] = l1

    def moveUp(self, item_id):
        lx, l = self.layerById(item_id)
        if lx + 1 < len(self._layers):
            self.swap(item_id, self._layers[lx + 1])

    def moveDown(self, item_id):
        lx, l = self.layerById(item_id)
        if lx - 1 > 0:
            self.swap(item_id, self._layers[lx - 1].idd)

    def moveToTop(self, item_id):
        self.swap(item_id, self._layers[len(self._layers) - 1].idd)

    def moveToBottom(self, item_id):
        self.swap(item_id, self._layers[0].idd)

    def updateZValue(self):
        """
        update Z values of each item according to item order in each layer
        :return:
        """
        for lx, layer in enumerate(self._layers):
            layer.setZValue(lx * self.MAX_N_ITEMS_PER_LAYER)
            for ix, item in enumerate(layer.items):
                zval = lx * self.MAX_N_ITEMS_PER_LAYER + ix + 1
                item.setZValue(zval)


class LayerItem(QGraphicsItem):
    def __init__(self, layer_stack, label, parent=None):
        super(LayerItem, self).__init__(parent=parent)
        self._label = label
        self._idd = DEFAULT_IDMAN.next()
        self._layer_stack = layer_stack
        # self._order = layer_stack.push(self)
        self._items = []

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        assert(isinstance(value, str))
        self._label = value

    @property
    def idd(self):
        return self._idd

    @property
    def items(self):
        return self._items

    def addItem(self, item):
        assert(len(self.items) < self._layer_stack.MAX_N_ITEMS_PER_LAYER)
        self._items.append(item)
        item.setParentItem(self)
        self.update()
        self._layer_stack.updateZValue()


class GroupItem(ControllableItem):
    def __init__(self, items, **kwargs):
        model = Group([item.model for item in items])
        super(GroupItem, self).__init__(model, kwargs)
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
            
    def paint(self, painter, option, widget=None):
        for child in self.childItems():
            child.paint(painter, option, widget)
    
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
    def __init__(self, points, **kwargs):
        model = Polyline(points)
        super(PolylineItem, self).__init__(model, **kwargs)

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
            self.addHandle(_NP(e.scenePos()))


class RectItem(ControllableItem):
    def __init__(self, x, y, width, height, **kwargs):
        """
        :param x: top-left corner
        :param y: bottom-right corner
        :param width:
        :param height:
        :param kwargs: see @ControllableItem
        """
        model = Rect(x, y, width, height)
        super(RectItem, self).__init__(model=model, **kwargs)

    def _updateRect(self):
        self.rect = self._adjustEdge(QRectF(self.model.x, self.model.y, self.model.width, self.model.height))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawRect(self.model.x, self.model.y, self.model.width, self.model.height)


class CircleItem(ControllableItem):
    def __init__(self, x, y, r, **kwargs):
        model = Circle(x, y, r)
        super(CircleItem, self).__init__(model=model, **kwargs)
        self._updateRect()

    def _updateRect(self):
        center = self.model.center
        r = self.model.r
        self.rect = self._adjustEdge(QRectF(center[0] - r, center[1] - r, r * 2, r * 2))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawEllipse(_QP(self.model.center), self.model.r, self.model.r)


class RingItem(CircleItem):
    def __init__(self, center, r1, r2, color, parent, idd, main,
                 edge_color=DEFAULT_EDGE_COLOR,
                 edge_width=DEFAULT_EDGE_WIDTH):
        super(RingItem, self).__init__(center=center, r=r2, parent=parent, idd=idd, main=main,
                                       color=color, edge_color=edge_color, edge_width=edge_width)
        self.addHandle([r1 + center[0], center[1]])
        self.r1 = r1
        
    def points(self):
        return np.array([list(self.center), [self.r1, 0], [self.r, 0]])
    
    def _updateRect(self):
        super(RingItem, self)._updateRect()
        if len(self.controls) > 2:
            self.r1 = euc(_NP(self.controls[2]), self.center)

    def polies(self):
        return [_circle_to_poly(self.center, self.r, 10), _circle_to_poly(self.center, self.r1, 10)]

    def paint(self, qp, option, widget=None):
        super(RingItem, self).paint(qp, option, widget)
        qp.drawEllipse(_QP(self.center), self.r1, self.r1)


class SRectItem(RingItem):
    def __init__(self, center, r1, r2, color, parent, idd, main,
                 edge_color=DEFAULT_EDGE_COLOR,
                 edge_width=DEFAULT_EDGE_WIDTH):
        super(SRectItem, self).__init__(center=center, r1=r1, r2=r2, parent=parent, idd=idd, main=main,
                                        color=color, edge_color=edge_color, edge_width=edge_width)

    def _updateRect(self):
        self.center = _NP(self.controls[0])
        self.r = euc(_NP(self.controls[1]), self.center)
        self.prepareGeometryChange()
        self.rect = QRectF(self.center[0] - self.r - 10, self.center[1] - self.r - 10
                           , self.r * 2 + 20, self.r * 2 + 20)

    def paint(self, qp, option, widget=None):
        x, y = self.center[0] - self.r, self.center[1] - self.r
        qp.drawRect(x, y, self.r * 2, self.r - self.r1)

    def boundingRect(self):
        return self.rect

    def polies(self):
        pass

    def points(self):
        pass


class SplineItem(ControllableItem):
    def __init__(self, points, **kwargs):
        model = Polyline(points)
        super(SplineItem, self).__init__(model, kwargs)
        for px, p in enumerate(points):
            self.addHandle(p)

        self._updateRect()

    def paint(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.color), 5))
        qp.drawPolyline(*[c.pos() for c in self.controls])
        if self.isSelected():
            qp.setPen(QPen(QBrush(self.color), 5, Qt.DotLine))
            qp.drawRect(self.boundingRect())

        super(SplineItem, self).paint(qp, option, widget)

    def __len__(self):
        return len(self.controls)

    def _updateRect(self):
        pos = self.toPolies()[0]
        if len(pos) > 0:
            xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
            self.prepareGeometryChange()
            self._rect = QRectF(xmin - 5, ymin - 5, xmax - xmin + 5, ymax - ymin + 5)

    def remove(self, control):
        control.setParentItem(None)
        if control.idd == self.controls[-1].idd:
            if len(self.controls) >= 2:
                self.controls[-2].setSize(self.handle_size)
                self.controls[-2].setColor(Qt.black)

        if control.idd == self.controls[0].idd:
            if len(self.controls) >= 2:
                self.controls[1].setSize(self.handle_size)
                self.controls[1].setColor(Qt.white)

        for cx, c in enumerate(self.controls):
            if c.idd == control.idd:
                del self.controls[cx]
                break

        self.update()

    def moveBy(self, dx, dy):
        for control in self.controls:
            control.setPos(control.x() + dx, control.y() + dy)

    def scaleBy(self, sx, sy):
        for control in self.controls:
            control.setPos(control.x() * sx, control.y() * sy)

    def boundingRect(self):
        self._updateRect()
        return self._rect

    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() == Qt.ControlModifier:
            self.addHandle(e.scenePos())

    def itemChange(self, change, value):
        return super(SplineItem, self).itemChange(change, value)

    def toPolies(self):
        return np.array([np.array([[c.x(), c.y()] for c in self.controls])])

        
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
            self.parentItem().itemChange(change, value)
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