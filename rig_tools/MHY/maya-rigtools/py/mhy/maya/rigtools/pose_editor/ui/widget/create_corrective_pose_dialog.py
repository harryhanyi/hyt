from PySide2 import QtCore, QtGui, QtWidgets
from mhy.maya.rigtools.pose_editor.ui.widget.adjust_widget import AdjustWidget
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
import mhy.maya.rigtools.pose_editor.api.utils as utils
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
import mhy.maya.rigtools.pose_editor.ui.manager as manager


class CreateCorrectivePoseDialog(QtWidgets.QDialog):
    """
    The Dialog for user to create corrective pose.
    """

    def __init__(self, controller, poses, parent=None):
        super(CreateCorrectivePoseDialog, self).__init__(parent=parent)
        self.setWindowTitle("Create Corrective")
        self.__delegate = controller
        self.__poses = poses
        self.__poses.sort(key=lambda pose: pose.name)
        root_layout = QtWidgets.QVBoxLayout()
        self.setLayout(root_layout)
        # Create the headers
        self.column_headers = ['', 'Driver Poses', 'Weight']
        self._data_model = QtGui.QStandardItemModel(0,
                                                    len(self.column_headers))
        for col, col_name in enumerate(self.column_headers):
            self._data_model.setHeaderData(col, QtCore.Qt.Horizontal, col_name)

        layout = QtWidgets.QHBoxLayout()
        root_layout.addLayout(layout)
        name_lable = QtWidgets.QLabel("Corrective Pose Name")
        name_lable.setFixedWidth(360)
        layout.addWidget(name_lable)
        weight_lable = QtWidgets.QLabel("weight")
        weight_lable.setFixedWidth(64)
        layout.addWidget(weight_lable)
        layout = QtWidgets.QHBoxLayout()
        self.name_edit = QtWidgets.QLineEdit(parent=self)
        self.name_edit.setText(self.candidate_name)
        self.name_edit.setFixedWidth(360)
        layout.addWidget(self.name_edit)
        self.weights = {pose.name: pose.weight for pose in self.__poses}
        self.weights["corrective pose weight"] = Settings.maximum_weight
        weight_item = AdjustWidget('corrective pose weight', delegate=None, value=Settings.maximum_weight,
                                   high=Settings.maximum_weight, low=0.0,
                                   step=0.1, callbacks={'changing': [self.weight_changed]},parent=self)
        weight_item.setFixedWidth(64)
        layout.addWidget(weight_item)
        root_layout.addLayout(layout)

        self.poses_view = self._init_pose_view()
        root_layout.addWidget(self.poses_view)

        root_layout.addWidget(QtWidgets.QLabel("Symmetry Information"))
        self.symmetry = Symmetry.CENTER
        self.symmetryWidget = QtWidgets.QComboBox()
        self.symmetryWidget.addItems(["Middle", "Left", "Right"])
        self.symmetryWidget.currentIndexChanged.connect(self.symmetry_changed)
        root_layout.addWidget(self.symmetryWidget)

        layout = QtWidgets.QHBoxLayout()
        root_layout.addLayout(layout)
        button = QtWidgets.QPushButton('Yes', self)
        button.clicked.connect(self._create_corrective_pose)
        layout.addWidget(button)
        button = QtWidgets.QPushButton('Cancel', self)
        button.clicked.connect(self.close)
        layout.addWidget(button)
        self.setFixedWidth(520)

    def weight_changed(self, widget):
        weight = utils.round_to_value(widget.value)
        pose_name = widget.property_name
        self.weights[pose_name] = weight

    @property
    def controller(self):
        return self.__delegate

    def symmetry_changed(self, idx):
        text = self.symmetryWidget.itemText(idx)
        if text == "Left":
            self.symmetry = Symmetry.LEFT
        elif text == "Right":
            self.symmetry = Symmetry.RIGHT
        else:
            self.symmetry = Symmetry.CENTER

    def _init_pose_view(self):
        """
        Generate UI for related poses.
        """
        poses_view = QtWidgets.QTreeView(parent=self)
        poses_view.setModel(self._data_model)

        root_item = self._data_model.invisibleRootItem()
        idx = 0
        for pose in self.__poses:
            items = [QtGui.QStandardItem(),
                     QtGui.QStandardItem(),
                     QtGui.QStandardItem()]
            items[1].setText(pose.name)
            root_item.appendRow(items)
            active_item = QtWidgets.QCheckBox()
            active_item.setChecked(True)
            widget_index = items[0].index()
            poses_view.setIndexWidget(widget_index, active_item)
            weight_item = AdjustWidget(pose.name, delegate=None, value=pose.weight,
                                       high=Settings.maximum_weight, low=0.0,
                                       step=0.1, callbacks={'changing': [self.weight_changed]})
            widget_index = items[2].index()

            poses_view.setIndexWidget(widget_index, weight_item)
            idx += 1
        poses_view.setColumnWidth(0, 48)
        poses_view.setColumnWidth(1, 300)
        poses_view.setColumnWidth(2, 64)
        return poses_view

    def _create_corrective_pose(self):
        name = self.name_edit.text()
        if name == "":
            name = "Corrective"
        name = self.get_unique_name(name, self.symmetry)
        for pose in self.poses:
            pose.weight = self.weights.get(pose.name, pose.weight)
        corrective_pose = self.controller.create_corrective_pose(
            name=name,
            drive_poses=self.poses,
            symmetry=self.symmetry,
            weight=self.weights["corrective pose weight"])

        # Update other ui widgets
        SignalManager.corrective_pose_update.emit(corrective_pose)
        if manager.Pose_Model:
            corrective_group = manager.Pose_Model.get_corrective_group()
            manager.Pose_Model.insert_pose(
                corrective_pose,
                corrective_group,
                corrective_group.child_count())
        self.close()

    @property
    def poses(self):
        """
        The selected poses which will be used to create correctives.
        """
        row_count = self._data_model.rowCount()
        poses = []
        for row in range(row_count):
            index = self._data_model.index(row, 0, QtCore.QModelIndex())
            checkbox_item = self.poses_view.indexWidget(index)
            if checkbox_item.isChecked():
                poses.append(self.__poses[row])
        return poses

    def get_unique_name(self, name, symmetry):
        """
        generate a corrective pose name based on the input poses.
        """
        guess_name = name
        final_name = "{}_{}".format(guess_name, Symmetry.to_str_table[symmetry])
        if final_name not in self.controller.poses:
            return guess_name
        idx = 0
        while final_name in self.controller.poses:
            final_name = "{}{}_{}".format(guess_name, idx, Symmetry.to_str_table[symmetry])
            idx += 1
        return "{}{}".format(guess_name, idx-1)

    @property
    def candidate_name(self):
        """
        generate a corrective pose name based on the input poses.
        """
        if not self.__poses:
            return 'Corrective'
        return self.__poses[0].main_name+"_Corrective"
