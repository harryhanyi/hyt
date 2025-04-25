from mhy.qt.core import QtGui, QtWidgets, QtCore


class ColorPushButton(QtWidgets.QPushButton):
    """
    A push button that triggers a color picker.
    """

    color_changed = QtCore.Signal(QtGui.QColor)

    def __init__(self, default=None, *args, **kwargs):
        super(ColorPushButton, self).__init__(*args, **kwargs)
        if default:
            self.__default = default
        else:
            self.__default = QtGui.QColor()
        self.__color = default
        self.clicked.connect(self.pick_color)

    @property
    def color(self):
        """The current color.

        :type: QColor
        :setter: Sets the current color.
        """
        return self.__color

    @color.setter
    def color(self, value):
        if value is None:
            self.setStyleSheet('')
            self.__color = QtGui.QColor()
        else:
            self.setStyleSheet(
                'QPushButton {{background-color: rgb({},{},{})}}'.format(
                    value.red(), value.green(), value.blue()))
            self.__color = value

    @QtCore.Slot()
    def reset(self):
        """Resets the default color."""
        self.color = self.__default

    @QtCore.Slot()
    def pick_color(self):
        """Launches a QColorDialog allowing the user to pick a color.

        Returns:
            None
        """
        dialog = QtWidgets.QColorDialog()
        dialog.setCurrentColor(self.color)
        result = dialog.exec_()
        if result:
            color = dialog.selectedColor()
            if color.isValid():
                self.color = color
                self.color_changed.emit(color)
