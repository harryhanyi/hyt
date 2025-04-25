from mhy.qt.core import QtGui
from mhy.maya.anim_lib.qt_lib.color import Color
import six


class Pixmap(QtGui.QPixmap):

    def __init__(self, *args):
        QtGui.QPixmap.__init__(self, *args)

        self._color = None

    def setColor(self, color):
        """
        :type color: QtGui.QColor
        :rtype: None
        """
        if isinstance(color, six.string_types):
            color = Color.fromString(color)

        if not self.isNull():
            painter = QtGui.QPainter(self)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawRect(self.rect())
            painter.end()
