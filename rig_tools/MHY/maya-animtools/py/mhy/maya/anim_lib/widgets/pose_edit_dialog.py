from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
from mhy.maya.anim.lib.collection import Collection
import getpass
import json
from datetime import datetime
import os
from mhy.maya.anim_lib.utils import find_footage_folder
from mhy.maya.anim_lib.widgets.sequence_widget import ThumbNailIcon
from mhy.maya.anim_lib.signal_manager import SignalManager


class PoseEditDialog(QtWidgets.QDialog):
    pose_created_signal = QtCore.Signal(object)

    def __init__(self, pose_item, parent=None):
        super(PoseEditDialog, self).__init__(parent=parent)
        self.item = pose_item
        self.root_path = None
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Edit Pose: {}'.format(pose_item.name))
        main_layout = QtWidgets.QGridLayout(self)
        self.snap_shot_view = ThumbNailIcon(
            static=pose_item.is_static,
            editable=True,
            parent=self)

        footage_folder = find_footage_folder(self.item.path)
        if footage_folder:
            self.snap_shot_view.setPath(footage_folder)

        pose_name_label = QtWidgets.QLabel("Pose Name: {}".format(self.item.name))

        comment_label = QtWidgets.QLabel("Comment: ")
        self.comment_line = QtWidgets.QTextEdit(self)
        self.comment_line.setPlaceholderText("Type in comment for this pose")
        self.comment_line.setText(self.item.comment)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        self.update_anim_data_check = QtWidgets.QCheckBox("Update Anim Data")
        self.update_anim_data_check.setToolTip("If recreate pose data from selected objects.")
        self.update_anim_data_check.setChecked(False)

        main_layout.addWidget(self.snap_shot_view, 0, 0, 1, 2)
        main_layout.addWidget(pose_name_label, 2, 0, 1, 2)
        main_layout.addWidget(comment_label, 3, 0)
        main_layout.addWidget(self.comment_line, 3, 1)
        main_layout.addWidget(self.update_anim_data_check, 4, 0, 1, 2)
        main_layout.addWidget(button_box, 5, 0, 6, 0)
        button_box.accepted.connect(lambda: self.apply_cb(pose_item.is_static))
        button_box.rejected.connect(self.close)

    def apply_cb(self, static):
        update_data = self.update_anim_data_check.isChecked()
        comment = self.comment_line.toPlainText() or ""
        user = getpass.getuser()
        date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not update_data:
            current_file = cmds.file(query=True, sceneName=True)
            self.update_data(comment=comment, user=user, date_created=date_created, source_file=current_file)

        else:
            selection = cmds.ls(sl=True)
            if not selection:
                QtWidgets.QMessageBox.critical(self,
                                               'No Selection',
                                               "No objects selected")
                return
            result = Collection.export_selection_to(
                name=self.item.name,
                path=self.item.path,
                static=static,
                comment=comment,
                user_created=user,
                date_created=date_created)

            if not result:
                return

        if not self.snap_shot_view.image_updated:
            self.close()
            return

        footage_path = find_footage_folder(self.item.path)
        if os.path.isdir(footage_path):
            for img in os.listdir(footage_path):
                fp = os.path.join(footage_path, img)
                os.remove(fp)

        if self.snap_shot_view.thumb_nail_dir and os.path.isdir(self.snap_shot_view.thumb_nail_dir):
            for img in os.listdir(self.snap_shot_view.thumb_nail_dir):
                full_path = os.path.join(self.snap_shot_view.thumb_nail_dir, img)
                target_path = os.path.join(footage_path, img)
                os.rename(full_path, target_path)

        root = os.path.dirname(self.item.path)
        SignalManager.pose_files_changed.emit([root])
        self.close()

    def update_data(self, comment=None, user=None, date_created=None, source_file=None):
        file_path = self.item.path
        if not os.path.isfile(file_path):
            return
        with open(file_path, 'r') as f:
            data = json.load(f)

        if comment is not None:
            data['comment'] = comment

        if user is not None:
            data['user_created'] = user

        if date_created is not None:
            data['date_created'] = date_created

        if source_file is not None:
            data['source_file'] = source_file

        data_str = json.dumps(data,
                              indent=4)
        with open(file_path, 'w') as f:
            f.write(data_str)

    def set_root_path(self, path):
        self.root_path = path








