"""
Pose splitter dialog module
"""
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import mhy.maya.rigtools.pose_editor.ui.manager as manager


class PoseSplitDialog(QtWidgets.QDialog):
    def __init__(self, pose_item, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.pose_item = pose_item
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        child_pose_layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(
            "Transform Driver objects to split pose {}. \n"
            "Add selected objects and apply splitting".format(pose_item.name),
            parent=self)

        self.list_widget = QtWidgets.QListWidget(parent=self)

        button_layout = QtWidgets.QHBoxLayout()
        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_pose_cb)
        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(self.remove_pose_cb)
        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(self.clear_cb)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(clear_button)
        child_pose_layout.addWidget(label)
        child_pose_layout.addWidget(self.list_widget)
        child_pose_layout.addLayout(button_layout)

        config_layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel("Dropoff off:")
        self.drop_off_slider = QtWidgets.QDoubleSpinBox()
        self.drop_off_slider.setMinimum(0)
        self.drop_off_slider.setValue(0.6)
        self.drop_off_slider.setSingleStep(0.05)

        self.influence_check = QtWidgets.QCheckBox("Influence")
        self.influence_check.setChecked(True)
        self.target_check = QtWidgets.QCheckBox("Target")
        self.target_check.setChecked(True)

        config_layout.addWidget(label, 0, 0)
        config_layout.addWidget(self.drop_off_slider, 0, 1)
        config_layout.addWidget(self.influence_check, 1, 0)
        config_layout.addWidget(self.target_check, 1, 1)

        button_layout = QtWidgets.QHBoxLayout()
        apply_button = QtWidgets.QPushButton('Apply')
        cancel_button = QtWidgets.QPushButton('Cancel')
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(child_pose_layout)
        main_layout.addLayout(config_layout)
        main_layout.addLayout(button_layout)

        apply_button.clicked.connect(self.apply)
        cancel_button.clicked.connect(self.close)

    def __get_drivers(self):
        drivers = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            driver = item.data(QtCore.Qt.DisplayRole)
            drivers.append(driver)
        return drivers

    def add_pose_cb(self):
        sel = cmds.ls(sl=True, type='transform')
        self.list_widget.addItems(sel)
        count = self.list_widget.count()

        self.list_widget.setCurrentRow(count - 1)

    def remove_pose_cb(self):
        item = self.list_widget.takeItem(self.list_widget.currentRow())
        del item

    def clear_cb(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.takeItem(i)
            del item

    def apply(self):
        fall_off = self.drop_off_slider.value()
        drivers = self.__get_drivers()
        manager.Pose_Model.reset_weights()

        if_influence = self.influence_check.isChecked()
        if_target = self.target_check.isChecked()
        manager.Pose_Model.split_pose(
            self.pose_item,
            fall_off=fall_off,
            drivers=drivers,
            influence=if_influence,
            target=if_target)
        self.close()


if __name__ == "__main__":
    inst = PoseSplitDialog()
    inst.show()