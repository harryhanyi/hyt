# Copyright 2020 by Kurt Rathjen. All Rights Reserved.
#
# This library is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. This library is distributed in the
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.

import logging

import six
import os
from PySide2 import QtWidgets, QtGui, QtCore
import mhy.maya.anim_lib.qt_lib as qt_lib
from mhy.qt.icon_lib.api import get_pixmap
from mhy.maya.anim_lib.qt_lib.pixmap import Pixmap

__all__ = ["SidebarWidgetItem"]

logger = logging.getLogger(__name__)


class SidebarWidgetItem(QtWidgets.QTreeWidgetItem):
    PIXMAP_CACHE = {}

    def __init__(self, *args):
        QtWidgets.QTreeWidgetItem.__init__(self, *args)

        self._path = ""
        self._bold = None
        self._iconVisible = True
        self._iconPath = None
        self._iconColor = None
        self._textColor = None
        self._iconKey = None
        self._expandedIconPath = None
        self._collapsedIconPath = None

        font = QtGui.QFont()
        font.setPointSize(13)
        self.setFont(0, font)
        self._settings = {}

    def create_pixmap(self, path, color):
        """
        Create a new Pixmap from the given path.

        :type path: str
        :type color: str or QtCore.QColor
        :rtype: QtCore.QPixmap
        """
        dpi = self.treeWidget().dpi()
        key = path + color + "DPI-" + str(dpi)
        pixmap = self.PIXMAP_CACHE.get(key)

        if not pixmap:

            width = 20 * dpi
            height = 18 * dpi

            pixmap2 = Pixmap(get_pixmap(path))
            pixmap2.setColor(color)
            pixmap2 = pixmap2.scaled(
                22 * dpi,
                22 * dpi,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            x = (width - pixmap2.width()) / 2
            y = (height - pixmap2.height()) / 2

            pixmap = QtGui.QPixmap(QtCore.QSize(width, height))
            pixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(pixmap)
            painter.drawPixmap(x, y, pixmap2)
            painter.end()

            self.PIXMAP_CACHE[key] = pixmap

        return pixmap

    def set_icon_path(self, path):
        """
        Return the icon path for the item.

        :type path: str
        :rtype: None
        """
        self._iconPath = path
        self.update_icon()

    def set_icon_visible(self, visible):
        """
        Set the icon visibility for the folder item

        :type visible: bool
        """
        self._iconVisible = visible

    def is_icon_visible(self):
        """
        Check if the icon is visible.

        :rtype: bool
        """
        return True

    def icon_color(self):
        """
        Return the icon color.

        :rtype: QtGui.QColor or None
        """
        return self._iconColor or self.default_icon_color()

    def default_icon_color(self):
        """
        Return the default icon color.

        :rtype: QtGui.QColor or None
        """
        palette = self.treeWidget().palette()

        color = palette.color(self.treeWidget().foregroundRole())
        color = qt_lib.Color.fromColor(color).toString()

        return str(color)

    def set_icon_color(self, color):
        """
        Set the icon color.

        :type color: QtGui.QColor or str
        :rtype: None
        """
        if color:
            if isinstance(color, QtGui.QColor):
                color = qt_lib.Color.fromColor(color)

            elif isinstance(color, six.string_types):
                color = qt_lib.Color.fromString(color)

            self._iconColor = color.toString()
        else:
            self._iconColor = None

        self.update_icon()

    def set_path(self, path):
        """
        Set the path for the navigation item.

        :type path: str
        :rtype: None
        """
        self._path = path

    def path(self):
        """
        Return the item path.

        :rtype: str
        """
        return self._path

    def parents(self):
        """
        Return all item parents.

        :rtype: list[SidebarWidgetItem]
        """
        parents = []
        parent = self.parent()

        if parent:
            parents.append(parent)

            while parent.parent():
                parent = parent.parent()
                parents.append(parent)

        return parents

    def url(self):
        """
        Return the url path.

        :rtype: str
        """
        return QtCore.QUrl(self.path())

    def update(self):
        """
        :rtype: None
        """
        self.update_icon()

    def update_icon(self):
        """
        Force the icon to update.

        :rtype: None
        """
        if self.is_icon_visible():
            if os.path.isfile(self.path()):
                path = "/WINDOWS10/transportation/png/32/pedestrian_traffic_light_walk.png"
            elif self.isExpanded():
                path = "/GLYPH/general/png/38/folder_open.png"
            else:
                path = "/GLYPH/general/png/38/folder.png"

            pixmap = self.create_pixmap(path, self.icon_color())

            self.setIcon(0, pixmap)

    def bold(self):
        """
        Returns true if weight() is a value greater than QFont::Normal

        :rtype: bool
        """
        return self.font(0).bold()

    def set_bold(self, enable):
        """
        If enable is true sets the font's weight to

        :rtype: bool
        """
        if enable:
            self._settings["bold"] = enable

        font = self.font(0)
        font.setBold(enable)
        self.setFont(0, font)

    def setTextColor(self, color):
        """
        Set the foreground color to the given color

        :type color: QtGui.QColor or str
        :rtype: None
        """
        if isinstance(color, QtGui.QColor):
            color = qt_lib.Color.fromColor(color)

        elif isinstance(color, six.string_types):
            color = qt_lib.Color.fromString(color)

        self._settings["textColor"] = color.toString()

        brush = QtGui.QBrush()
        brush.setColor(color)
        self.setForeground(0, brush)

    def textColor(self):
        """
        Return the foreground color the item.

        :rtype: QtGui.QColor
        """
        color = self.foreground(0).color()
        return qt_lib.Color.fromColor(color)

    def settings(self):
        """
        Return the current state of the item as a dictionary.

        :rtype: dict
        """
        settings = {}

        is_selected = self.isSelected()
        if is_selected:
            settings["selected"] = is_selected

        is_expanded = self.isExpanded()
        if is_expanded:
            settings["expanded"] = is_expanded

        bold = self._settings.get("bold")
        if bold:
            settings["bold"] = bold

        text_color = self._settings.get("textColor")
        if text_color:
            settings["textColor"] = text_color

        return settings

    def setExpandedParents(self, expanded):
        """
        Set all the parents of the item to the value of expanded.

        :type expanded: bool
        :rtype: None
        """
        parents = self.parents()
        for parent in parents:
            parent.setExpanded(expanded)

    def setSelected(self, select):
        """
        Sets the selected state of the item to select.

        :type select: bool
        :rtype: None
        """
        QtWidgets.QTreeWidgetItem.setSelected(self, select)

        if select:
            self.setExpandedParents(select)

    def set_settings(self, settings):
        """
        Set the current state of the item from a dictionary.

        :type settings: dict
        """
        text = settings.get("text")
        if text:
            self.setText(0, text)

        icon_path = settings.get("icon")
        if icon_path is not None:
            self.set_icon_path(icon_path)

        icon_color = settings.get("color")
        if icon_color is not None:
            self.set_icon_color(icon_color)

        selected = settings.get("selected")
        if selected is not None:
            self.setSelected(selected)

        expanded = settings.get("expanded")
        if expanded is not None and self.childCount() > 0:
            self.setExpanded(expanded)
            self.update_icon()

        bold = settings.get("bold")
        if bold is not None:
            self.set_bold(bold)

        text_color = settings.get("textColor")
        if text_color:
            self.setTextColor(text_color)
