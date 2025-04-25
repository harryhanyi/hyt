"""
This module create a simple collapsible box with
a push button to toggle visibility of content
layout

Basic usage:
    from mhy.qt.core.widgets.collapsible_box import CollapsibleBox
    from mhy.qt.core import QtWidgets
    box = CollapsibleBox(title="test")
    layout = QtWidgets.QVBoxLayout()
    for i in range(10):
        pb = QtWidgets.QPushButton(str(i))
        layout.addWidget(pb)
    box.set_content_layout(layout)
    box.show()
"""
from mhy.qt.core import QtWidgets, QtCore, QtGui

__all__ = ['CollapsibleBox', 'ToggleButton']


class CollapsibleBox(QtWidgets.QFrame):
    collapsed_toggled_signal = QtCore.Signal(bool)

    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_button = ToggleButton(text=title, parent=self)
        self.toggle_button.pressed.connect(self.on_pressed)
        self.content_area = QtWidgets.QWidget(self)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

    @property
    def collapsed(self):
        return self.toggle_button.collapsed

    @collapsed.setter
    def collapsed(self, stat):
        self.toggle_button.collapsed = stat

    @QtCore.Slot()
    def on_pressed(self):
        self.collapsed = not self.collapsed
        if not self.collapsed:
            self.content_area.show()
        else:
            self.content_area.hide()
        self.collapsed_toggled_signal.emit(bool(self.collapsed))

    def set_content_layout(self, layout):
        """
        Attach a layout of widgets to this frame
        widget. Any objects in the given layout
        will be collapsed if push button clicked
        Args:
            layout(QLayout):

        """
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)


class ToggleButton(QtWidgets.QPushButton):
    arrow_margin = 4
    arrow_size = 6

    def __init__(self, text, parent, collapsed=False):
        super(ToggleButton, self).__init__(text, parent=parent)
        self.__collapsed = collapsed

    @property
    def collapsed(self):
        return self.__collapsed

    @collapsed.setter
    def collapsed(self, stat):
        self.__collapsed = stat
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        text_rect = QtCore.QRect(
            self.height()+self.arrow_margin,
            0,
            self.width(),
            self.height()
        )
        painter.drawText(text_rect, alignment, self.text())
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        path = QtGui.QPainterPath()
        arrow_center = self.height()/2
        if not self.collapsed:
            path.moveTo(arrow_center-self.arrow_size,
                        arrow_center-self.arrow_size)
            path.lineTo(arrow_center+self.arrow_size,
                        arrow_center-self.arrow_size)
            path.lineTo(arrow_center,
                        arrow_center+self.arrow_size)
            path.lineTo(arrow_center - self.arrow_size,
                        arrow_center - self.arrow_size)
            painter.fillPath(path, QtGui.QBrush(QtCore.Qt.white))
        else:
            path.moveTo(arrow_center-self.arrow_size,
                        arrow_center-self.arrow_size)
            path.lineTo(arrow_center+self.arrow_size,
                        arrow_center)
            path.lineTo(arrow_center-self.arrow_size,
                        arrow_center+self.arrow_size)
            path.lineTo(arrow_center - self.arrow_size,
                        arrow_center - self.arrow_size)
            painter.fillPath(path, QtGui.QBrush(QtCore.Qt.white))
