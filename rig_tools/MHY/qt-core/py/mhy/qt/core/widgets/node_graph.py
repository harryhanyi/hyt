from mhy.qt.core import QtWidgets, QtCore, QtGui


class NodeGraphView(QtWidgets.QGraphicsView):
    """
    A generic node graph view.
    """

    _BG_COLOR = QtGui.QColor(30, 30, 33)
    _GRID_PEN_S = QtGui.QPen(QtGui.QColor(50, 50, 50, 255), 0.5)
    _GRID_PEN_L = QtGui.QPen(QtGui.QColor(40, 40, 40, 255), 1.0)
    # _TEXT_PEN = QtGui.QPen(QtGui.QColor(100, 100, 100, 255), 1.0)
    _GRID_SIZE_FINE = 30
    _GRID_SIZE_COURSE = 300

    _width = 8000000
    _height = 4000000

    minimum_pixel = None

    # The maximum scale when user zoom in with mouse wheel
    maximum_scale = 3

    view_zoom_changed = QtCore.Signal(float)

    def __init__(self, scene, parent=None):
        """TODO doc"""
        super(NodeGraphView, self).__init__(parent)
        self.setScene(scene)

        # default settings
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # internal variables
        self.__drag = False
        self.__mouse_wheel_zoom_rate = 0.0005
        # self.__text_scale = 1
        self.__init_center = False
        self.__center = QtCore.QPoint(0, 0)

        # Set scene rectangle
        self.scene().setSceneRect(
            QtCore.QRectF(-self._width / 2, -self._height / 2,
                          self._width, self._height))

    # --- qt method re-implementation

    def wheelEvent(self, event):
        """Override wheel event to zoom in/out of the view."""
        zoom_factor = 1.0 + event.delta() * self.__mouse_wheel_zoom_rate
        scale_value = self.__get_scale_value()
        if scale_value*zoom_factor > self.maximum_scale:
            zoom_factor = self.maximum_scale/scale_value
        self.scale(zoom_factor, zoom_factor)
        scale_value = self.__get_scale_value()
        self.view_zoom_changed.emit(scale_value)
        self.update_center()

    def __get_scale_value(self):
        transform = self.transform()
        scale_value = transform.m11()
        return scale_value

    def mousePressEvent(self, event):
        """TODO doc"""
        if event.button() == QtCore.Qt.MiddleButton and \
           event.modifiers() == QtCore.Qt.AltModifier:
            # self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.__drag = True
            self.prev_pos = event.pos()
            # self.setCursor(QtCore.Qt.SizeAllCursor)
        elif event.button() == QtCore.Qt.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        super(NodeGraphView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """TODO doc"""
        if self.__drag:
            delta = (self.mapToScene(event.pos()) - self.mapToScene(self.prev_pos)) * - 1.0
            self.__center = self.__center + delta
            self.centerOn(self.__center)
            self.prev_pos = event.pos()
        super(NodeGraphView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """TODO doc"""
        super(NodeGraphView, self).mouseReleaseEvent(event)
        if self.__drag:
            self.__drag = False
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def keyPressEvent(self, event):
        """TODO doc"""
        super(NodeGraphView, self).keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_F:
            self.frame_items()

    def resizeEvent(self, event):
        """TODO doc"""
        super(NodeGraphView, self).resizeEvent(event)
        self.update_center()

    def drawBackground(self, painter, rect):
        """TODO doc"""
        if not self.__init_center:
            center = QtCore.QPoint(
                self.viewport().width() / 2, self.viewport().height() / 2)
            self.__center = self.mapToScene(center)
            self.__init_center = True

        painter.fillRect(rect, self._BG_COLOR)

        left = int(rect.left()) - (int(rect.left()) % self._GRID_SIZE_FINE)
        top = int(rect.top()) - (int(rect.top()) % self._GRID_SIZE_FINE)

        # Draw horizontal fine lines
        grid_lines = []
        painter.setPen(self._GRID_PEN_S)
        y = float(top)
        while y < float(rect.bottom()):
            grid_lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
            y += self._GRID_SIZE_FINE
        painter.drawLines(grid_lines)

        # Draw vertical fine lines
        grid_lines = []
        painter.setPen(self._GRID_PEN_S)
        x = float(left)
        while x < float(rect.right()):
            grid_lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
            x += self._GRID_SIZE_FINE
        painter.drawLines(grid_lines)

        # Draw thick grid
        left = int(rect.left()) - (int(rect.left()) % self._GRID_SIZE_COURSE)
        top = int(rect.top()) - (int(rect.top()) % self._GRID_SIZE_COURSE)

        # Draw vertical thick lines
        grid_lines = []
        painter.setPen(self._GRID_PEN_L)
        x = left
        while x < rect.right():
            grid_lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
            x += self._GRID_SIZE_COURSE
        painter.drawLines(grid_lines)

        # Draw horizontal thick lines
        grid_lines = []
        painter.setPen(self._GRID_PEN_L)
        y = top
        while y < rect.bottom():
            grid_lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
            y += self._GRID_SIZE_COURSE
        painter.drawLines(grid_lines)

        return QtWidgets.QGraphicsView.drawBackground(self, painter, rect)

    # --- other methods

    def frame_items(self, selection=True, items=None):
        """Frames view to selected or all items.

        Args:
            selection (bool): If True, frame to selected items.
                Otherwise frame to all items.
            items(list): A list of items for frame the view with

        Returns:
            None
        """
        scene = self.scene()
        bounding_box = None
        if items is None:
            if selection:
                sel_items = scene.selectedItems()
                if sel_items:
                    items = sel_items

            if not items:
                items = scene.node_items()
        if items:
            bounding_box = NodeGraphScene.get_bounding_rect(items)
        if bounding_box and self.minimum_pixel is not None:
            width = bounding_box.width()
            height = bounding_box.height()
            minimum = min(width, height)
            if minimum < self.minimum_pixel:
                margin = self.minimum_pixel - minimum
                bounding_box = bounding_box.marginsAdded(
                    QtCore.QMargins(margin, margin, margin, margin)
                )

        if not bounding_box:
            self.update_center()
            return

        self.fitInView(bounding_box, QtCore.Qt.KeepAspectRatio)

        scene_rect = self.sceneRect()
        center = scene_rect.center()

        self.update_center(center)


    def update_center(self, center=None):
        """TODO doc"""
        if not center:
            center = QtCore.QPoint(
                self.viewport().width() / 2, self.viewport().height() / 2)

        self.__center = self.mapToScene(center)
        self.__drag = False
        self.update()


class NodeGraphScene(QtWidgets.QGraphicsScene):
    """
    TODO doc
    """

    selection_changed = QtCore.Signal(list)

    class AlignmentMethod(object):
        kLeft = 3
        kCenter = 4
        kRight = 5
        kTop = 6
        kMiddle = 7
        kBottom = 8

    def __init__(self):
        super(NodeGraphScene, self).__init__()
        self.active = True

    def mouseReleaseEvent(self, event):
        """TODO doc"""
        result = super(NodeGraphScene, self).mouseReleaseEvent(event)
        if self.active:
            sel = self.selectedItems()
            self.selection_changed.emit(sel)
        return result

    def clear(self):
        """TODO doc"""
        QtWidgets.QGraphicsScene.clear(self)

    @staticmethod
    def get_bounding_rect(items):
        """TODO doc"""
        if not items:
            return QtCore.QRectF()
        item_rect = items[0].boundingRect()
        item_rect.moveTo(items[0].pos())
        for node in items[1:]:
            rect = node.boundingRect()
            rect.moveTo(node.pos())
            item_rect = item_rect.united(rect)
        return item_rect

    def align_selected_items(self, method):
        """Align the selected items.

        Args:
            method(int): One of NodeGraphScene.AlignMethod option.

        Returns:
            None
        """
        items = [i for i in self.selectedItems()
                 if not hasattr(i, 'zero_area_object')]
        if not items:
            return

        if method == NodeGraphScene.AlignmentMethod.kLeft:
            val = sum(item.pos().x() + item.rect.x()
                      for item in items) / len(items)
            for item in items:
                pos = item.pos()
                item.setPos(val - item.rect.x(), pos.y())

        elif method == NodeGraphScene.AlignmentMethod.kCenter:
            val = sum(item.pos().x() + item.rect.x() + item.rect.width()/2
                      for item in items) / len(items)
            for item in items:
                pos = item.pos()
                offset = item.rect.x() + item.rect.width()/2
                item.setPos(val-offset, pos.y())

        elif method == NodeGraphScene.AlignmentMethod.kRight:
            val = sum(item.pos().x() + item.rect.width() + item.rect.x() for item in items)
            val /= len(items)
            for item in items:
                pos = item.pos()
                offset = item.rect.width() + item.rect.x()
                item.setPos(val - offset, pos.y())

        elif method == NodeGraphScene.AlignmentMethod.kMiddle:
            val = sum(item.pos().y() + item.rect.y() + item.rect.height()/2 for item in items) / len(items)
            for item in items:
                pos = item.pos()
                offset = item.rect.y() + item.rect.height()/2
                item.setPos(pos.x(), val-offset)

        elif method == NodeGraphScene.AlignmentMethod.kTop:
            val = sum(item.pos().y() - item.rect.y() for item in items)
            val /= len(items)
            for item in items:
                pos = item.pos()
                offset = item.rect.y()
                item.setPos(pos.x(), val + offset)

        elif method == NodeGraphScene.AlignmentMethod.kBottom:
            val = sum(item.pos().y() + item.rect.y() + item.rect.height() for item in items)
            val /= len(items)
            for item in items:
                pos = item.pos()
                offset = item.rect.height() + item.rect.y()
                item.setPos(pos.x(), val - offset)

    def node_items(self):
        """
        This method should return the top level items that determines the bounding
        box of the existing items in the graph view
        Returns:

        """
        return self.items()
