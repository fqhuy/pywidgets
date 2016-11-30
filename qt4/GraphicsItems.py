# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 07:32:13 2015

@author: phanquochuy
"""

from PyQt4 import QtGui
from PyQt4.QtCore import (QByteArray, QDataStream, QFile, QFileInfo,
        QIODevice, QPoint, QPointF, QRectF, Qt, SIGNAL, QRect, QSize)
from PyQt4.QtGui import (QApplication, QWidget, QDockWidget, QStackedLayout,
                         QTabWidget, QVBoxLayout, QGridLayout, QSpinBox, QLabel,
                         QGraphicsView, QGraphicsScene, QGraphicsItem, 
                         QGraphicsTextItem, QColor, QBrush, QGroupBox,
                         QListWidget, QPixmap, QPainter, QBitmap, QListWidgetItem, QIcon, QFont, QPen)

import numpy as np
from scipy.spatial.distance import euclidean as euc

DEFAULT_COLOR = Qt.white
DEFAULT_HIGH_COLOR = Qt.yellow
DEFAULT_EDGE_COLOR = Qt.black
DEFAULT_HIGH_EDGE_COLOR = Qt.blue
DEFAULT_HANDLE_COLOR = Qt.green
DEFAULT_HANDLE_SIZE = 10
DEFAULT_EDGE_WIDTH = 1


def colorPixmap(pix, color):
    newPix = QPixmap(pix.size())
    newPix.fill(Qt.transparent)
    mask = pix.createMaskFromColor(QColor(0, 0, 0, 0), Qt.MaskInColor)
    p = QPainter(newPix)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setRenderHint(QPainter.Antialiasing)

    p.setBackgroundMode(Qt.TransparentMode)
    p.setPen(color)
    p.drawPixmap(newPix.rect(), mask, pix.rect())
    p.end()
    return newPix


def _circle_to_poly(center, r, astep=10):
    i = 0
    points = []
    while i < np.pi * 2:
        points.append([np.math.cos(i) * r +  center[0], np.math.sin(i) * r + center[1]])
        i += np.math.radians(astep)

    return points


def _NC(rgb):
    return np.array([float(rgb.red()) / 255., float(rgb.green()) / 255., float(rgb.blue()) / 255.] )


def _QC(rgb):
    if np.max(rgb) <= 1:
        fact = 255
    else:
        fact = 1

    if len(rgb) == 3:
        alpha = 255
    elif len(rgb) == 4:
        alpha = int(rgb[3] * fact)

    return QColor(int(rgb[0] * fact),int(rgb[1] * fact),int(rgb[2] * fact), alpha)


def _QP(pos):
    return QPointF(pos[0], pos[1])


def _NP(point):
    return np.array([point.x(), point.y()])


class ControllableItem(QGraphicsItem):
    def __init__(self, color, parent=None, idd=0, handle_size=10,
                 handle_color=DEFAULT_HANDLE_COLOR,
                 edge_color=DEFAULT_EDGE_COLOR, edge_width=DEFAULT_EDGE_WIDTH):
        super(ControllableItem, self).__init__(parent)
        self.controls = []
        self._handle_size = handle_size
        self._handle_color = handle_color
        self._color = color
        self._edge_color = edge_color
        self._idd = idd
        self._edge_width = edge_width

    @property
    def edge_width(self):
        return self._edge_width

    @edge_width.setter
    def edge_width(self, value):
        self._edge_width = value

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

    def addHandle(self, pos):
        if len(self.childItems()) == 0:
            idd = 0
        else:
            idd = self.childItems()[-1].idd + 1
            
        control = HandleItem(_QP(pos), size=self.handle_size, idd=idd, parent=self, color=self.handle_color)
        self.controls.append(control)
        return control

    def hideHandles(self):
        for c in self.controls:
            c.setVisible(False)

    def points(self):
        pass

    def polies(self):
        pass


class InteractiveScene(QGraphicsScene):
    def __init__(self, parent):
        super(InteractiveScene, self).__init__(parent)
        self.activeItem = None
        self.activeItemId = None
        self.activeSubItem = None
        
    def mousePressEvent(self, e):
        #print e.scenePos()

        if self.activeSubItem is not None:
            self.sendEvent(self.activeSubItem, e)
        elif self.activeItem is not None:
            self.sendEvent(self.activeItem, e)

        return super(InteractiveScene, self).mousePressEvent(e)


class GroupItem(QGraphicsItem):
    def __init__(self, items, idd, parent=None):
        super(GroupItem, self).__init__(parent)
        self.idd = idd
        for item in items:
            item.setParentItem(self)

    def mousePressEvent(self, e):
        for ch in self.childItems():
            self.scene().sendEvent(ch, e)
            
    def boundingRect(self):
        x1, y1, x2, y2 = [],[],[],[]
        for item in self.childItems():
            x1.append(item.boundingRect().x())
            y1.append(item.boundingRect().y())
            x2.append(item.boundingRect().right())
            y2.append(item.boundingRect().bottom())
        if len(x1) > 0:    
            return QRectF(min(x1), min(y1), max(x2) - min(x1), max(y2) - min(y1))
        else:
            return QRectF(self.x(), self.y(), 100, 100)
            
    def paint(self, painter, option, widget):
        pass
        #painter.setPen(QPen(QBrush(Qt.black),  5, Qt.DotLine))
        #painter.drawRect(self.boundingRect())
    
    def addItem(self, item):
        item.setParentItem(self)
        if self.scene() is not None:
            self.scene().activeSubItem = item
        return item
    
    def setZValue(self, p_float):
        for child in self.childItems():
            child.setZValue(p_float)

        super(GroupItem, self).setZValue(p_float)

    def points(self):
        points = []
        for child in self.childItems():
            points.append(child.points())

        return points

    def polies(self):
        points = []
        for child in self.childItems():
            points.append(child.polies())

        return points


class RectItem(ControllableItem):
    def __init__(self, p1, p2, color, parent, idd, main):
        super(RectItem, self).__init__(color=color, parent=parent, idd=idd)
        self.w = abs(p2[0] - p1[0])
        self.h = abs(p2[1] - p1[1])
        h1 = self.addHandle(p1)
        h1.color = color
        h2 = self.addHandle(p2)
        h2.color = color
        self.rect = QRectF(0, 0, 100, 100)
        
    def updateRect(self):
        self.w = abs(self.controls[0].x() - self.controls[1].x())
        self.h = abs(self.controls[0].y() - self.controls[1].y())
        hsize = self.controls[0].size
        
        self.prepareGeometryChange()
        self.rect = QRectF(self.controls[0].x() - hsize, self.controls[0].y() - hsize, self.w + hsize * 2, self.h + hsize * 2)
        
    def paint(self, painter, option, widget):
        qp = painter
        qp.setPen(QPen(QBrush(self.color), 5))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        if hasattr(self, 'controls'):
            if len(self.controls) > 0:
                qp.drawRect(self.controls[0].x(), self.controls[0].y(), self.w, self.h)
    
    def boundingRect(self):
        return self.rect

    def points(self):
        return np.array(self.controls[0].points() + self.controls[1].points())

    def polies(self):
        p1 = self.controls[0].points()[0]
        p2 = self.controls[1].points()[0]
        return np.array([list(p1), [p2[0], p1[1]], list(p2), [p1[0], p2[1]]])


class CircleItem(ControllableItem):
    def __init__(self, center, r, parent, idd, main, color=DEFAULT_COLOR,
                 edge_color=DEFAULT_EDGE_COLOR, handle_color=DEFAULT_HANDLE_COLOR,
                 handle_size=8, edge_width=DEFAULT_EDGE_WIDTH):
        super(CircleItem, self).__init__(color=color, parent=parent, edge_color=edge_color, idd=idd,
                                         handle_color=handle_color, handle_size=handle_size, edge_width=edge_width)
        self.main = main
        self.center = center
        self.r = r
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)
        
        self.addHandle(center)
        self.addHandle([center[0], center[1] + r])
        self.rect = None
        self.updateRect()

    def hideHandles(self):
        for c in self.controls:
            c.setVisible(False)
    
    def updateRect(self):
        self.center = _NP(self.controls[0])
        self.r = euc(_NP(self.controls[1]), self.center)
        
        self.prepareGeometryChange()
        self.rect = QRectF(self.center[0] - self.r - 10, self.center[1] - self.r - 10
                           , self.r * 2 + 20, self.r * 2 + 20)

    def paint(self, painter, option, widget):
        qp = painter
        qp.setPen(QPen(QBrush(self.edge_color), self.edge_width))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        if hasattr(self, 'controls'):
            if len(self.controls) > 0:
                qp.drawEllipse(_QP(self.center), self.r, self.r)
    
    def boundingRect(self):
        return self.rect

    def points(self):
        return np.array([list(self.center), [self.r, 0]])

    def polies(self):
        return [_circle_to_poly(self.center, self.r, 10)]


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
    
    def updateRect(self):
        super(RingItem, self).updateRect()
        if len(self.controls) > 2:
            self.r1 = euc(_NP(self.controls[2]), self.center)

    def polies(self):
        return [_circle_to_poly(self.center, self.r, 10), _circle_to_poly(self.center, self.r1, 10)]

    def paint(self, qp, option, widget):
        super(RingItem, self).paint(qp, option, widget)
        qp.drawEllipse(_QP(self.center), self.r1, self.r1)


class SRectItem(RingItem):
    def __init__(self, center, r1, r2, color, parent, idd, main,
                 edge_color=DEFAULT_EDGE_COLOR,
                 edge_width=DEFAULT_EDGE_WIDTH):
        super(SRectItem, self).__init__(center=center, r1=r1, r2=r2, parent=parent, idd=idd, main=main,
                                        color=color, edge_color=edge_color, edge_width=edge_width)

    def updateRect(self):
        self.center = _NP(self.controls[0])
        self.r = euc(_NP(self.controls[1]), self.center)
        self.prepareGeometryChange()
        self.rect = QRectF(self.center[0] - self.r - 10, self.center[1] - self.r - 10
                           , self.r * 2 + 20, self.r * 2 + 20)

    def paint(self, qp, option, widget):
        x, y = self.center[0] - self.r, self.center[1] - self.r
        qp.drawRect(x, y, self.r * 2, self.r - self.r1)

    def boundingRect(self):
        return self.rect

    def polies(self):
        pass

    def points(self):
        pass

        
class PolylineItem(ControllableItem):
    def __init__(self, points, color, parent, idd, main, edge_color=DEFAULT_EDGE_COLOR,
                 handle_color=DEFAULT_HANDLE_COLOR, edge_width=DEFAULT_EDGE_WIDTH):
        super(PolylineItem, self).__init__(parent, idd=idd, color=color, parent=parent, edge_color=edge_color,
                                           handle_color=handle_color, edge_width=edge_width)
        self.main = main
        self.controls = []
        self.breaks = []
        self.handle_size = 8
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)

        for px, p in enumerate(points):
            self.addHandle(p)
        
        if len(self.controls) > 0:
            titem = QGraphicsTextItem(str(self.idd), parent=self.controls[0])
            titem.setPos(QPointF(0,0))
            titem.setFont(QFont('',40))

        self.updateRect()
        
    def paint(self, painter, option, widget):
        qp = painter
        #qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setPen(QPen(QBrush(self.color), 5))
        if hasattr(self, 'controls'):
            if len(self.controls) > 0 and len(self.breaks) == 0:
                qp.drawPolyline(*[ c.pos() for c in self.controls])
            elif len(self.controls) > 0 and len(self.breaks) > 0 :
                qp.drawPolyline(*[ c.pos() for c in self.controls[0:self.breaks[0]]])
                qp.drawPolyline(*[ c.pos() for c in self.controls[self.breaks[-1]:]])
                if len(self.breaks) > 1:
                    for brk in range(0, len(self.breaks) - 1):
                        qp.drawPolyline(*[ c.pos() for c in
                        self.controls[self.breaks[brk]:self.breaks[brk+1]]])
                
        if self.isSelected():
            qp.setPen(QPen(QBrush(self.color),  5, Qt.DotLine))
            qp.drawRect(self.boundingRect())
            
    def __len__(self):
        return len(self.controls)

    def updateRect(self):
        pos = []
        for control in self.controls:
            pos.append((control.x(), control.y()))
            
        pos = np.array(pos)
        if len(pos) > 0:
            xmax,xmin,ymax,ymin = pos[:,0].max(), pos[:,0].min(), pos[:,1].max(), pos[:,1].min()
            #return self.mapToScene( QRectF(xmin - 5, ymin - 5, xmax - xmin + 5, ymax - ymin + 5) ).boundingRect()
            self.prepareGeometryChange()
            #self.rect = self.controls[0].boundingRect().adjusted(-20, -20, 20, 20)
            self.rect = QRectF(xmin - 5, ymin - 5, xmax - xmin + 5, ymax - ymin + 5)
            #self.parentItem().update()
        
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
        if hasattr(self, 'rect'):
            return self.rect
        else:
            return QRectF(self.x(), self.y(), 0.0, 0.0)
        
    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() == Qt.ControlModifier:
            self.addHandle(e.scenePos())
        elif e.button() == 1 and e.modifiers() == Qt.ShiftModifier:
            self.breaks.append(len(self.controls))
            self.addHandle(e.scenePos())

    def addHandle(self, pos):
        if len(self.childItems()) == 0:
            idd = 0
        else:
            idd = self.childItems()[-1].idd + 1
            
        control = HandleItem(pos, size=self.handle_size, idd=idd, parent=self, color=self.color)
       
        self.controls.append(control)
        self.updateRect()
        
    def addHandles(self, poss):
        for pos in poss:
            self.addHandle(pos)
        
    def addBreak(self, pos):
        self.breaks.append(pos)

    def itemChange(self, change, value):
            
        return super(PolylineItem, self).itemChange(change, value)
        
    def points(self):
        if len(self.breaks) == 0:
            return np.array([np.array([[c.x(), c.y()] for c in self.controls])])
        else:
            data = [ [[c.x(), c.y()] for c in self.controls[:self.breaks[0]]] ]
            for brk in range(len(self.breaks)-1):
                data.append([[c.x(), c.y()] for c in 
                self.controls[self.breaks[brk]: self.breaks[brk+1]] ])
            data.append( [[c.x(), c.y()] for c in self.controls[self.breaks[-1]:]] )
            return np.array(data)
        
class HandleItem(QGraphicsItem):
    def __init__(self, position, size, idd, parent, color=Qt.green):
        super(HandleItem, self).__init__(parent)
        self.setPos(position)
        self.size = size
        self.color = color
        self.idd = idd
        #self.setZValue(10)
        self.setFlags(self.flags()                  |
#                    QGraphicsItem.ItemIsSelectable  |
                    QGraphicsItem.ItemIsMovable     |
                    QGraphicsItem.ItemSendsGeometryChanges |
                    QGraphicsItem.ItemIsFocusable   )
        self.rect = QRectF(0,0,size,size)
                    
    def boundingRect(self):
        size = self.size
        return self.rect.adjusted(-size,-size,0,0)
        
    def paint(self, painter, option, widget):
        qp = painter
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        #size = self.size
        qp.drawEllipse(self.boundingRect())
    
    def points(self):
        return [[self.x(), self.y()]]

    def mousePressEvent(self, e):
        #if e.button() == 1:
        #    self.parentItem().main.bringToFront(self.parentItem().idd)
        if e.button() == 2:
            self.parentItem().main.remove(self)
            
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.parentItem()._updateRect()
        return super(HandleItem, self).itemChange(change, value)
        
    def setSize(self, size):
        self.prepareGeometryChange()
        self.size = size
        self.rect = QRectF(0,0,size,size)
        
    def setColor(self, color):
        self.color = color
        self.update()
    
    