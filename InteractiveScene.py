from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem)
from PyQt5.QtGui import (QBrush, QPen, QTransform)
from PyQt5.QtCore import (Qt)
from .GraphicsItems import ControllableItem, DEFAULT_IDMAN


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


class LayerStack(object):
    MAX_N_ITEMS_PER_LAYER = 1000

    def __init__(self):
        self.clear()

    def __contains__(self, item):
        try:
            re = self.itemById(item.idd)
        except ValueError:
            return False

        return True

    @property
    def current_item_id(self):
        return self._current_item_id

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
        if item.parentItem() is not None:
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

    def clear(self):
        """
        empty current stack
        :return:
        """
        self._layers = [LayerItem(self, 'default', None)]
        self._current_layer_id = self._layers[0].idd
        self._current_item_id = -1


class InteractiveScene(QGraphicsScene):
    def __init__(self, parent=None):
        # self._active_item = None
        self._layer_stack = LayerStack()
        super(InteractiveScene, self).__init__(parent)
        self.reset()

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

    def reset(self):
        self._layer_stack.clear()
        self.clear()
        self.setBackgroundBrush(QBrush(Qt.white, Qt.SolidPattern))
        self.addLine(0, 0, 1000, 0, QPen(Qt.DashLine))
        self.addLine(0, 0, 0, 1000, QPen(Qt.DashLine))