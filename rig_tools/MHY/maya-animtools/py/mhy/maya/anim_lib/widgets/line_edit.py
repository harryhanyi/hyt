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

from PySide2 import QtGui, QtWidgets, QtCore
from mhy.maya.anim_lib.widgets.icon import Icon
from mhy.maya.anim_lib.qt_lib import Color
logger = logging.getLogger(__name__)


class LineEdit(QtWidgets.QLineEdit):

    def __init__(self, *args):
        QtWidgets.QLineEdit.__init__(self, *args)

        self._iconButton = QtWidgets.QPushButton(self)
        self._iconButton.setObjectName("icon")
        self._iconButton.clicked.connect(self._iconClicked)
        self._iconButton.setStyleSheet("QPushButton{background-color: transparent;}")

        self._clearButton = QtWidgets.QPushButton('C', self)
        self._clearButton.setObjectName("clear")
        self._clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self._clearButton.setToolTip("Clear all search text")
        self._clearButton.clicked.connect(self._clear_clicked)
        self._clearButton.setStyleSheet("QPushButton{background-color: transparent;}")

        self.textChanged.connect(self._text_changed)

        color = Color.fromString("rgb(250,250,250,115)")
        self.setIconColor(color)

        self.update()

    def update(self):
        self.updateIconColor()
        self.updateClearButton()

    def _text_changed(self, text):
        """
        Triggered when the text changes.

        :type text: str
        :rtype: None
        """
        self.updateClearButton()

    def _clear_clicked(self):
        """
        Triggered when the user clicks the cross icon.

        :rtype: None
        """
        self.setText("")
        self.setFocus()

    def _iconClicked(self):
        """
        Triggered when the user clicks on the icon.

        :rtype: None
        """
        if not self.hasFocus():
            self.setFocus()

    def updateClearButton(self):
        """
        Update the clear button depending on the current text.

        :rtype: None
        """
        text = self.text()
        if text:
            self._clearButton.show()
        else:
            self._clearButton.hide()

    def contextMenuEvent(self, event):
        """
        Triggered when the user right clicks on the search widget.

        :type event: QtCore.QEvent
        :rtype: None
        """
        self.showContextMenu()

    def setIcon(self, icon):
        """
        Set the icon for the search widget.

        :type icon: QtWidgets.QIcon
        :rtype: None
        """
        self._iconButton.setIcon(icon)

    def setIconColor(self, color):
        """
        Set the icon color for the search widget icon.

        :type color: QtGui.QColor
        :rtype: None
        """
        icon = self._iconButton.icon()
        icon = Icon(icon)
        icon.setColor(color)
        self._iconButton.setIcon(icon)

        icon = self._clearButton.icon()
        icon = Icon(icon)
        icon.setColor(color)
        self._clearButton.setIcon(icon)

    def updateIconColor(self):
        """
        Update the icon colors to the current foregroundRole.

        :rtype: None
        """
        color = self.palette().color(self.foregroundRole())
        color = Color.fromColor(color)
        self.setIconColor(color)

    def settings(self):
        """
        Return a dictionary of the current widget state.

        :rtype: dict
        """
        settings = {
            "text": self.text(),
        }
        return settings

    def set_settings(self, settings):
        """
        Restore the widget state from a settings dictionary.

        :type settings: dict
        :rtype: None
        """
        text = settings.get("text", "")
        self.setText(text)

    def resizeEvent(self, event):
        """
        Reimplemented so the icon maintains the same height as the widget.

        :type event:  QtWidgets.QResizeEvent
        :rtype: None
        """
        QtWidgets.QLineEdit.resizeEvent(self, event)

        height = self.height()
        size = QtCore.QSize(16, 16)

        self.setTextMargins(20, 0, 0, 0)

        self._iconButton.setIconSize(size)
        self._iconButton.setGeometry(0, 0, height, height)

        x = self.width() - height

        self._clearButton.setIconSize(size)
        self._clearButton.setGeometry(x, 0, height, height)
