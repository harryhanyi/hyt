"""
This module is a widget used for editing a anim curve object
"""
from PySide2 import QtWidgets, QtCore, QtGui


class AnimCurveWidget(QtWidgets.QWidget):
    def __init__(self, draggable=False, magnetic=True, parent=None):
        super(AnimCurveWidget, self).__init__(parent=parent)
        main_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(main_layout)
        self.slider = AnimCurveSlider(draggable, magnetic, self)
        self.weight_box = QtWidgets.QDoubleSpinBox(self)
        self.weight_box.setRange(-999, 999)
        self.weight_box.setFixedWidth(100)
        self.weight_box.setSingleStep(0.1)
        main_layout.addWidget(self.slider)
        main_layout.addWidget(self.weight_box)
        self.slider.slider_value_changed_sg.connect(self.update_weight_box_cb)
        self.slider.selection_changed_sg.connect(self.selection_changed_cb)
        self.weight_box.valueChanged.connect(self.update_slider_current_val_cb)

    @property
    def value(self):
        return self.slider.current

    @value.setter
    def value(self, v):
        self.slider.current = v
        self.update_weight_box_cb(v)

    def selection_changed_cb(self, data):
        if data[0]:
            self.update_weight_box_cb(data[1])

    def update_weight_box_cb(self, value):
        self.weight_box.blockSignals(True)
        self.weight_box.setValue(value)
        self.weight_box.blockSignals(False)

    def update_slider_current_val_cb(self, val):
        self.slider.current = val
        self.slider.repaint()

    def set_range(self, range_value):
        """
        Set range of this slider by querying the minimum and maximum values
        Args:
            range_value(list): A list of numeric values

        Returns:
            list: A range represented by a list or two items

        """
        min_val = min(range_value)
        max_val = max(range_value)

        self.slider.driven_range = [min_val, max_val]

    def set_internal_anim_curve(self, anim_curve=None):
        self.slider.set_internal_anim_curve(anim_curve)

    def selected_key(self):
        return self.slider.selected_key


class AnimCurveSlider(QtWidgets.QWidget):

    slider_offset = 0
    margin = 20
    slider_width = 10
    tickle_radius = 15
    key_radius = 15
    key_text_offset = 8

    # ------------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------------
    selection_changed_sg = QtCore.Signal(tuple)
    slider_value_changed_sg = QtCore.Signal(float)

    def __init__(self, draggable=False, magnetic=True, parent=None):
        super(AnimCurveSlider, self).__init__(parent=parent)
        self.__range = [0, 1]
        self.__current = 0
        self.setMinimumHeight(60)
        self.setMinimumWidth(450)

        self.is_dragging = False
        self.key_frames = list()
        self.draggable = draggable

        self.__key_sense_area_centers = list()
        self.__high_light_keys = list()

        # ------------------------------------------------------------------------
        # Painting colors
        # ------------------------------------------------------------------------

        self.transparent_pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        self.background_color = QtGui.QColor(152, 207, 237)
        self.key_color = QtGui.QColor(84, 180, 232)
        self.high_light_key_color = QtGui.QColor(84, 180, 232)
        self.selected_color = QtGui.QColor(191, 59, 44)
        self.tickle_color = QtGui.QColor(222, 105, 22)

        self.init_colors()

        self.magnetic = magnetic
        self.selected_key = None
        self.font = QtGui.QFont()
        self.font.setPixelSize(18)
        self.setMouseTracking(True)

    @property
    def current(self):
        """
        Current value property
        Returns:
            float: The current value
        """
        return self.__current

    @current.setter
    def current(self, val):
        """
        Current value setter
        Args:
            val(float): Value for current setter

        """
        self.__current = val
        self.update_high_light_keys()

    @property
    def driven_range(self):
        return self.__range

    @driven_range.setter
    def driven_range(self, value):
        self.__range = value

    def set_internal_anim_curve(self, anim_curve=None):
        keys = []
        if anim_curve:
            for idx in range(anim_curve.num_keys):
                keys.append(round(anim_curve.get_input(idx), 2))

        keys.sort()
        if anim_curve:
            if len(keys) == 1:
                self.driven_range = [keys[0], keys[0]+10]
            else:
                self.driven_range = [min(keys), max(keys)]
            self.current = self.driven_range[0]
        else:
            self.driven_range = [0, 10]
            self.current = 0
        self.set_key_frames(keys)
        self.repaint()

    def init_colors(self):
        """
        Query painting colors from palette
        Returns:

        """
        self.background_color = QtGui.QColor(self.palette().color(QtGui.QPalette.Base).name())
        self.key_color = QtGui.QColor(self.palette().color(QtGui.QPalette.WindowText).name())

    def get_keys_nearby(self, pos):
        if not isinstance(pos, QtCore.QPoint):
            pos = self.get_pos_from_value(pos)
        keys_near_pos = []
        for key, key_center in zip(self.key_frames, self.__key_sense_area_centers):
            dist = abs(pos.x() - key_center.x())
            if dist < self.key_radius:
                keys_near_pos.append(key)
        return keys_near_pos

    def update_high_light_keys(self):
        pos = self.get_pos_from_value(self.current)
        high_light_keys = self.get_keys_nearby(pos)
        if high_light_keys != self.__high_light_keys:
            self.__high_light_keys = high_light_keys

    def get_pos_from_value(self, val):
        """
        Map a value to the absolute position on the slider
        Returns:
            QPoint: The position point on the slider
        """
        real_width = self.width() - self.margin
        if self.driven_range[1] == self.driven_range[0]:
            slider_length = 1
        else:
            slider_length = self.driven_range[1] - self.driven_range[0]
        pos = QtCore.QPoint(self.margin / 2 + real_width * (val - self.driven_range[0]) / slider_length,
                            self.height() / 2 - self.slider_offset)
        return pos

    def set_key_frames(self, keys):
        self.key_frames = keys
        self.update_key_centers()
        self.update_high_light_keys()

    def update_key_centers(self):
        self.__key_sense_area_centers = []
        real_width = self.width() - self.margin
        if self.driven_range[1] == self.driven_range[0]:
            slider_length = 1
        else:
            slider_length = self.driven_range[1] - self.driven_range[0]
        for k in self.key_frames:
            key_center = QtCore.QPoint(self.margin/2 + real_width*(k - self.driven_range[0])/slider_length,
                                       self.height()/2 - self.slider_offset)
            self.__key_sense_area_centers.append(key_center)

    def resizeEvent(self, event):
        super(AnimCurveSlider, self).resizeEvent(event)
        self.update_key_centers()

    def paintEvent(self, *args, **kwargs):
        painter = QtGui.QPainter(self)
        painter.setPen(self.transparent_pen)
        brush = QtGui.QBrush()
        brush.setColor(self.background_color)
        brush.setStyle(QtCore.Qt.SolidPattern)
        real_width = self.width() - self.margin
        bg_rect = QtCore.QRect(0, painter.device().height() / 2 - self.slider_width / 2 - self.slider_offset,
                               real_width, self.slider_width)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if len(self.driven_range) < 2:
            return
        # Create the path
        path = QtGui.QPainterPath()

        path.addRoundedRect(bg_rect, self.slider_width/2, self.slider_width/2)
        # painter.setClipPath(path)

        # Fill shape, draw the border and center the text.
        painter.fillPath(path, brush)
        painter.setFont(self.font)
        for key, center in zip(self.key_frames, self.__key_sense_area_centers):
            if key == self.selected_key:
                brush.setColor(self.selected_color)
                text_pen = QtGui.QPen(self.selected_color)
            elif key in self.__high_light_keys:
                brush.setColor(self.high_light_key_color)
                text_pen = QtGui.QPen(self.high_light_key_color)
            else:
                brush.setColor(self.key_color)
                text_pen = QtGui.QPen(self.key_color)
            painter.setBrush(brush)

            key_rect = QtCore.QRect(
                center.x() - self.key_radius / 2,
                center.y() - self.key_radius / 2,
                self.key_radius,
                self.key_radius)
            painter.setPen(self.transparent_pen)
            painter.drawEllipse(key_rect)
            text_point = QtCore.QPoint(
                center.x(),
                center.y() - self.key_radius / 2 - self.key_text_offset)

            painter.setPen(text_pen)
            painter.drawText(text_point, str(key))

        keys_under_current = self.get_keys_nearby(self.current)
        if self.draggable and not keys_under_current:
            tickle_rect = QtCore.QRect(
                real_width * (self.current - self.driven_range[0]) / (
                            self.driven_range[1] - self.driven_range[0]) - self.tickle_radius / 2,
                painter.device().height() / 2 - self.key_radius / 2,
                self.tickle_radius,
                self.tickle_radius)
            painter.setPen(self.transparent_pen)
            brush.setColor(self.tickle_color)
            painter.setBrush(brush)
            painter.drawEllipse(tickle_rect)

            # Fill shape, draw the border and center the text.

        painter.end()

    def mousePressEvent(self, event):
        pos = event.pos()
        pos_x = min(max(pos.x(), self.x()), self.x() + self.width()-self.margin)
        do_selection = False
        self.selected_key = None
        for key, key_center in zip(self.key_frames, self.__key_sense_area_centers):
            dist = abs(pos_x - key_center.x())
            if dist < self.key_radius:
                self.selected_key = key
                do_selection = True
                self.current = key
                break
        if self.selected_key is None:
            self.selection_changed_sg.emit((False, -1))
        else:
            self.selection_changed_sg.emit((True, self.selected_key))

        if do_selection:
            self.repaint()
            return

        if self.draggable:
            width = self.width()
            self.current = self.driven_range[0] + float((self.driven_range[1] - self.driven_range[0]))*pos.x() / width
            self.repaint()
            self.is_dragging = True

    def mouseMoveEvent(self, event):
        pos = event.pos()
        pos_x = min(max(pos.x(), self.x()), self.x() + self.width()-self.margin)
        high_light_keys = list()
        for key, key_center in zip(self.key_frames, self.__key_sense_area_centers):
            dist = abs(pos_x - key_center.x())
            if dist < self.key_radius:
                high_light_keys.append(key)
        if high_light_keys != self.__high_light_keys:
            self.__high_light_keys = high_light_keys

        if self.draggable and self.is_dragging:
            pos = event.pos()
            width = self.width()
            self.current = max(min(self.driven_range[0] + float((self.driven_range[1] - self.driven_range[0]))*pos.x() / width, self.driven_range[1]),
                               self.driven_range[0])
            self.slider_value_changed_sg.emit(self.current)
        self.repaint()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    def set_current_value(self, value):
        self.current = value


if __name__ == '__main__':
    ui = AnimCurveWidget(None)
    ui.show()

