from mhy.qt.core import QtWidgets, QtCore
import maya.cmds as cmds
import getpass
from datetime import datetime
import os

from mhy.maya.anim.lib.collection import Collection
from mhy.maya.anim_lib.widgets.sequence_widget import ThumbNailIcon
from mhy.maya.anim_lib.signal_manager import SignalManager


class PoseCreationDialog(QtWidgets.QDialog):
    pose_created_signal = QtCore.Signal(object)

    def __init__(self, title, static, parent=None):
        super(PoseCreationDialog, self).__init__(parent=parent)
        self.root_path = None
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        main_layout = QtWidgets.QGridLayout(self)
        self.snap_shot_view = ThumbNailIcon(
            static=static, editable=True, parent=self)

        pose_name_label = QtWidgets.QLabel("Data Name: ")
        self.pose_name = QtWidgets.QLineEdit(self)

        comment_label = QtWidgets.QLabel("Comment: ")
        self.comment_line = QtWidgets.QTextEdit(self)

        if static:
            self.comment_line.setPlaceholderText(
                "Type in comment for this pose")
        else:
            self.comment_line.setPlaceholderText(
                "Type in comment for this animation")

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        main_layout.addWidget(self.snap_shot_view, 0, 0, 1, 2)
        main_layout.addWidget(pose_name_label, 2, 0)
        main_layout.addWidget(self.pose_name, 2, 1)
        main_layout.addWidget(comment_label, 3, 0)
        main_layout.addWidget(self.comment_line, 3, 1)

        main_layout.addWidget(button_box, 4, 0, 5, 0)
        button_box.accepted.connect(lambda: self.apply_cb(static))
        button_box.rejected.connect(self.close)

    def apply_cb(self, static):
        pose_name = self.pose_name.text()
        if not pose_name:
            return
        full_path = os.path.join(self.root_path, pose_name + '.apd')

        selection = cmds.ls(sl=True)
        if not selection:
            QtWidgets.QMessageBox.critical(self,
                                           'No Selection',
                                           "No objects selected")
            return

        if os.path.isfile(full_path):
            result = QtWidgets.QMessageBox.question(
                self, 'Duplicated File Name',
                "Pose data file named `{}` exists already."
                "Do you want to replace it?".format(pose_name))
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        comment = self.comment_line.toPlainText() or ""
        user = getpass.getuser()
        date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = Collection.export_selection_to(
            name=pose_name,
            path=full_path,
            static=static,
            comment=comment,
            user_created=user,
            date_created=date_created)

        if not result:
            return

        footage_path = self.get_footage_path(self.root_path, pose_name)

        if self.snap_shot_view.thumb_nail_dir and \
                os.path.isdir(self.snap_shot_view.thumb_nail_dir):
            footage_dir = os.path.dirname(footage_path)
            for img in os.listdir(self.snap_shot_view.thumb_nail_dir):
                full_path = os.path.join(self.snap_shot_view.thumb_nail_dir, img)
                target_path = os.path.join(footage_dir, img)
                os.rename(full_path, target_path)

        SignalManager.pose_files_changed.emit([self.root_path])
        self.close()

    @staticmethod
    def get_footage_path(root_path, pose_name):
        folder_name = pose_name + '_footage'
        path_name = os.path.join(root_path, folder_name)
        if os.path.exists(path_name):
            # Clear existing imgages
            for i in os.listdir(path_name):
                f = os.path.join(path_name, i)
                if os.path.isfile(f):
                    os.remove(f)
        else:
            os.mkdir(path_name)
        path_name = os.path.join(path_name, 'thumbnails')
        return path_name

    def set_root_path(self, path):
        self.root_path = path








