"""
This module contains a widget allow user to interactively review a sequence
of images on local disk
"""
from mhy.qt.core.widgets.sequence_widget import ImageSequenceWidget
from mhy.qt.core import QtWidgets, QtCore, QtGui
import mhy.maya.ui.model_panel as model_panel

import os
import tempfile

__all__ = ['ImageSequenceWidget']

STYLE = """
QToolBar {
    border: 0px solid black; 
    border-radius:2px;
    background-color: rgb(0,0,0,100);
}

QToolButton {
    background-color: transparent;
}
"""


class ThumbNailIcon(ImageSequenceWidget):
    DEFAULT_PLAYHEAD_COLOR = QtGui.QColor(59, 150, 255, 130)

    def __init__(self, static=True, editable=False, parent=None):
        super(ThumbNailIcon, self).__init__(parent=parent)
        self.static = static

        if editable:
            self.setToolTip("Click to update thumbnail images")
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
            self.clicked.connect(self.show_snap_shot_dialog_cb)

    def show_context_menu(self):
        menu = QtWidgets.QMenu(self)
        update_thumb_nail_action = QtWidgets.QAction("Update thumbnails", self)
        menu.addAction(update_thumb_nail_action)
        update_thumb_nail_action.triggered.connect(
            self.show_snap_shot_dialog_cb
        )
        menu.exec_(QtGui.QCursor.pos())

    def show_snap_shot_dialog_cb(self):
        tmp_path = self.get_thumb_nail_dir()
        ui = model_panel.ThumbnailWidget(
            static=self.static,
            out_directory=tmp_path,
            file_name='thumb_nail',
            parent=self)

        ui.thumb_nail_update_signal.connect(self.update_thumb_nail_cb)
        ui.show()

    def get_thumb_nail_dir(self):
        tmp_dir = tempfile.gettempdir()
        out_path = os.path.join(tmp_dir, 'thumb_nail_backup')
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        for img in os.listdir(out_path):
            img_path = os.path.join(out_path, img)
            os.remove(img_path)
        return out_path
