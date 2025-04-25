from mhy.qt.core import QtGui
import six


class Color(QtGui.QColor):

    @classmethod
    def fromColor(cls, color):
        """
        :type color: QtGui.QColor
        """
        color = ('rgb(%d, %d, %d, %d)' % color.getRgb())
        return cls.fromString(color)

    @classmethod
    def fromString(cls, text):
        """
        :type text: str
        """
        a = 255
        text = text.replace(";", "")

        try:
            r, g, b, a = text.replace("rgb(", "").replace(")", "").split(",")
        except ValueError:
            r, g, b = text.replace("rgb(", "").replace(")", "").split(",")

        return cls(int(r), int(g), int(b), int(a))

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.toString() == other.toString()
        else:
            return QtGui.QColor.__eq__(self, other)

    def toString(self):
        """
        :type: str
        """
        rgb = self.getRgb()
        return 'rgb({}, {}, {}, {})'.format(rgb[0], rgb[1], rgb[2], rgb[3])

    def isDark(self):
        """
        :type: bool
        """
        return self.red() < 125 and self.green() < 125 and self.blue() < 125


