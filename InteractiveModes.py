from PyQt5 import QtGui
from PyQt5.QtCore import (QByteArray, QDataStream, QFile, QFileInfo, QObject,
        QIODevice, QPoint, QPointF, QRectF, Qt, QRect, QSize, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QColor, QBrush, QPixmap, QPainter, QBitmap, QIcon, QFont, QPen, QTransform, QPainterPath)
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QGraphicsTextItem, QGraphicsView)


class ModeRegistry(QObject):
    pass


class InteractiveMode(QObject):
    __metaclass__ = ModeRegistry
    ACTION_NAME = None
    model = None

    @classmethod
    def getName(cls):
        return cls.__name__

    def stackableOn(self, mode):
        return False

    def enter(self, model, **kwargs):
        pass

    def leave(self, **kwargs):
        pass

    def currentModifiers(self):
        pass

    def currentPosition(self):
        pass


class DragMode(InteractiveMode):
    pass


class SingleClickMode(InteractiveMode):
    def __init__(self, **kwargs):
        super(SingleClickMode, self).__init__(**kwargs)
        self._button_pressed = None

    def enter(self, model, **kwargs):
        super(SingleClickMode, self).enter(model, **kwargs)

    def leave(self, **kwargs):
        if self.model is not None:
            pass

        super(SingleClickMode, self).leave(**kwargs)

    @pyqtSlot()
    def onPress(self):
        pass

    @pyqtSlot()
    def onRelease(self):
        pass

    @pyqtSlot()
    def onClick(self):
        pass


class InstantDragMode(DragMode):
    pass


class ModeStack(QObject):
    """
    keep track of active modes
    """
    pass
