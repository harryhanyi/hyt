"""
A pose influence elements widget for pose influence management.
"""
from maya import cmds
import maya.OpenMaya as OpenMaya
from PySide2 import QtCore, QtGui, QtWidgets
from mhy.maya.nodezoo.node import Node
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.maya.rigtools.pose_editor.ui.widget.adjust_widget import AdjustWidget
import mhy.maya.rigtools.pose_editor.api.utils as utils
import mhy.maya.rigtools.pose_editor.ui.manager as manager
import mhy.maya.rigtools.pose_editor.api.pose_controller as pose_controller
import mhy.maya.rigtools.pose_editor.ui.actions as action_api


class CorrectivePoseView(QtWidgets.QTreeView):
    """
    The tree view for CorrectivePoses.
    """
    column_headers = ['Corrective Pose',
                      'Index',
                      'Current Weight',
                      'Key Weight']

    def __init__(self, delegate, *args, **kwargs):
        super(CorrectivePoseView, self).__init__(*args, **kwargs)
        self._data_model = None

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.controller = delegate
        self.update_ui()

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.launch_context_menu)

        SignalManager.corrective_pose_update.connect(self.update_corrective_pose)
        SignalManager.refresh_corrective_view_signal.connect(self.update_ui)

    @property
    def controller(self):
        return self.__delegate.controller

    @controller.setter
    def controller(self, control):
        self.__delegate = control
        self.update_ui()

    def launch_context_menu(self, position):
        """
        the context menu of an item.
        Args:
            position(QPoint): The position where menu will be created
        """
        index = self.indexAt(position)
        if index is None:
            return

        menu = self.make_context_menu(index)
        if menu:
            menu.exec_(self.viewport().mapToGlobal(position))

    def make_context_menu(self, index):
        """
        Create a menu based on the selected index
        Args:
            index(QModelIndex):

        Returns:
            QtWidgets.QMenu: Created menu instance

        """
        if not index or not index.isValid():
            return
        menu = QtWidgets.QMenu(self)
        if index.data(QtCore.Qt.UserRole) != "DrivePose":
            menu.addAction(self.tr("Add Pose"), self.__delegate.add_corrective_drive)
            menu.addSeparator()
            menu.addAction(self.tr('Add New Key'), self.__delegate.add_corrective_pose_key)
            menu.addAction(self.tr("Delete Key"), self.__delegate.delete_corrective_key)
            menu.addSeparator()
            menu.addAction(self.tr('Update Key'), self.__delegate.update_corrective_pose_key)
            menu.addAction(self.tr('Modify Falloff'), self.update_fall_off)

        else:
            menu.addAction(self.tr("Delete Pose"), self.__delegate.delete_drive_pose)

        return menu

    def get_row(self, corrective_pose):
        row_count = self._data_model.rowCount()
        for row in range(row_count):
            index = self._data_model.index(row, 0, QtCore.QModelIndex())
            parent_item = self._data_model.itemFromIndex(index)
            if corrective_pose.name == parent_item.text():
                return row
        return -1

    def _select_default_row(self, corrective_name=None, drive_name=None):
        selection_model = self.selectionModel()
        if corrective_name:
            row_number = self._data_model.rowCount()
            for row in range(row_number):
                index = self._data_model.index(row, 0, QtCore.QModelIndex())
                item = self._data_model.itemFromIndex(index)
                if item.text() == corrective_name:
                    if drive_name is None:
                        selection_model.select(index, QtCore.QItemSelectionModel.Rows |
                                               QtCore.QItemSelectionModel.Select)
                        return
                    children_num = self._data_model.rowCount(index)
                    for sub_row in range(children_num):
                        sub_index = index.child(sub_row, 0)
                        item = self._data_model.itemFromIndex(sub_index)
                        if item.text() == drive_name:
                            selection_model.select(
                                sub_index, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.Select)
                            return
                    # can't find the drive_pose just select parent corrective pose.
                    selection_model.select(index, QtCore.QItemSelectionModel.Rows |
                                           QtCore.QItemSelectionModel.Select)
        # default selection
        indexes = selection_model.selectedIndexes()
        if not indexes and self._data_model.rowCount() > 0:
            index = self._data_model.index(0, 0, QtCore.QModelIndex())
            selection_model.select(
                index, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.Select)

    def update_corrective_pose(self, corrective_pose):
        """
        Refresh callback that update a single corrective pose
        Args:
            corrective_pose(Pose):

        """
        corrective_name, drive_name = self.get_selected_corrective_and_drive_name()
        if corrective_pose is None:
            self.update_ui()
            self._select_default_row(corrective_name, drive_name)
            return
        # handle selection
        row_count = self._data_model.rowCount()
        for row in range(row_count):
            index = self._data_model.index(row, 0, QtCore.QModelIndex())
            parent_item = self._data_model.itemFromIndex(index)
            if corrective_pose.name == parent_item.text():
                self.populate_pose(corrective_pose, row)
                self._select_default_row(corrective_name, drive_name)
                return
        self.populate_pose(corrective_pose, row_count)
        self._select_default_row(corrective_name, drive_name)

    def update_ui(self):
        """

        Updated the corrective view

        """
        self._data_model = QtGui.QStandardItemModel(0, len(CorrectivePoseView.column_headers))
        if not self.controller:
            corrective_poses = []
        else:
            corrective_poses = self.controller.corrective_poses or []
        self.setModel(self._data_model)
        self._data_model.clear()
        self._data_model.setColumnCount(len(CorrectivePoseView.column_headers))
        for column_id, column_name in enumerate(CorrectivePoseView.column_headers):
            self._data_model.setHeaderData(
                column_id, QtCore.Qt.Horizontal, column_name)
        self.setColumnWidth(0, 348)
        self.setColumnWidth(1, 64)
        self.setColumnWidth(2, 128)
        self.setColumnWidth(3, 128)
        self.populate_model(corrective_poses)
        self._select_default_row()

    def populate_model(self, corrective_poses):
        """
        populate the data model.
        """
        # Recurse through child widgets
        if corrective_poses is not None:
            for idx, corrective_pose in enumerate(corrective_poses):
                self.populate_pose(corrective_pose, idx)

    def weight_changing_callback(self, widget):
        weight = utils.round_to_value(widget.value)
        widget.delegate.weight = weight
        manager.Pose_Model.update_pose_weight(widget.delegate, weight)
        if not widget.delegate.is_corrective:
            self.update_corrective_weight_from_maya()

    def update_corrective_weight_from_maya(self):
        controller = self.controller
        if not controller or not Settings.live_update_corrective_weight:
            return
        row_count = self._data_model.rowCount()
        for row in range(row_count):
            name_column = self.column_headers.index('Corrective Pose')
            name_index = self._data_model.index(
                row, name_column, QtCore.QModelIndex())
            weight_column = self.column_headers.index('Current Weight')
            weight_index = name_index.sibling(name_index.row(), weight_column)
            item = self._data_model.itemFromIndex(name_index)
            pose_name = item.text()
            corrective_pose = controller.poses.get(pose_name, None)
            weight = cmds.getAttr(corrective_pose.output_attribute_full_name)
            weight = utils.round_to_value(weight)
            weight_widget = self.indexWidget(weight_index)
            weight_widget.set_value(weight)
            pose = self.controller.poses.get(pose_name, None)
            if pose and manager.Pose_Model:
                manager.Pose_Model.update_pose_weight(pose, weight)

    def index_changed_callback(self, widget):
        corrective_pose = widget.delegate
        corrective_pose.current_corrective_index = widget.value
        key_column = self.column_headers.index('Key Weight')
        row = self.get_row(corrective_pose)
        index = self._data_model.index(row, key_column, QtCore.QModelIndex())
        widget = self.indexWidget(index)

        widget.setText(utils.round_to_str(corrective_pose.weight))
        index = self._data_model.index(row, 0, QtCore.QModelIndex())
        parent_item = self._data_model.itemFromIndex(index)
        for row in range(parent_item.rowCount()):
            pose_name_column = self.column_headers.index('Corrective Pose')
            name_item = parent_item.child(row, pose_name_column)
            drive_pose_name = name_item.text()
            for drive_pose in corrective_pose.drive_poses:
                if drive_pose.name == drive_pose_name:
                    key_item = parent_item.child(row, key_column)
                    index = key_item.index()
                    widget = self.indexWidget(index)
                    widget.setText(utils.round_to_str(drive_pose.weight))
                    break

    def populate_pose(self, corrective_pose, row):
        """
        add the corrective pose driver.
        """
        # pose name
        corrective_pose_item = QtGui.QStandardItem(corrective_pose.name)
        corrective_pose_item.setEditable(False)
        self._data_model.setItem(row, 0, corrective_pose_item)
        self.setExpanded(corrective_pose_item.index(), True)
        # corrective pose key index.
        widget = AdjustWidget(property_name="index", delegate=corrective_pose,
                              value=corrective_pose.current_corrective_index,
                              high=len(corrective_pose.corrective_keys)-1, low=0,
                              step=0.2, mode=AdjustWidget.kInt | AdjustWidget.kShowTotal,
                              offset=1, callbacks={'changed': [self.index_changed_callback]},
                              change_signal=SignalManager.pose_changed_signal)
        widget_index = self._data_model.index(row, 1, QtCore.QModelIndex())
        self.setIndexWidget(widget_index, widget)

        widget = QtWidgets.QLabel(str(corrective_pose.current_corrective_key))
        key_column = self.column_headers.index('Key Weight')
        widget_index = self._data_model.index(
            row, key_column, QtCore.QModelIndex())
        self.setIndexWidget(widget_index, widget)
        # pose weight.
        weight_widget = AdjustWidget(property_name="weight", delegate=corrective_pose, value=corrective_pose.weight,
                                     high=Settings.maximum_weight, low=0.0,
                                     step=0.1, callbacks={'changing': [self.weight_changing_callback]},
                                     change_signal=SignalManager.pose_changed_signal)
        weight_column = self.column_headers.index('Current Weight')
        widget_index = self._data_model.index(
            row, weight_column, QtCore.QModelIndex())
        self.setIndexWidget(widget_index, weight_widget)

        for drive_pose, key in corrective_pose.current_drive_pose.items():
            items = [QtGui.QStandardItem(drive_pose.name),
                     QtGui.QStandardItem(),
                     QtGui.QStandardItem(),
                     QtGui.QStandardItem()]
            items[0].setEditable(False)
            items[0].setData('DrivePose', QtCore.Qt.UserRole)
            corrective_pose_item.appendRow(items)

            widget = QtWidgets.QLabel(str(key))
            key_column = self.column_headers.index('Key Weight')
            weight_index = items[key_column].index()
            self.setIndexWidget(weight_index, widget)
            widget = AdjustWidget(property_name="weight", delegate=drive_pose, value=drive_pose.weight,
                                  high=Settings.maximum_weight, low=0.0, step=0.1,
                                  callbacks={'changing': [self.weight_changing_callback]},
                                  change_signal=SignalManager.pose_changed_signal)
            weight_column = self.column_headers.index('Current Weight')
            weight_index = items[weight_column].index()
            self.setIndexWidget(weight_index, widget)

    def get_selected_corrective_and_drive_name(self):
        controller = self.controller
        if not controller:
            return None, None
        selection_model = self.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not selection_model or not indexes:
            return None, None
        index = indexes[0]
        index = index.sibling(index.row(), 0)
        item = self._data_model.itemFromIndex(index)
        pose_name = item.text()
        parent_index = index.parent()
        parent_index = parent_index.sibling(parent_index.row(), 0)
        item = self._data_model.itemFromIndex(parent_index)
        if not item:
            return pose_name, None
        corrective_pose_name = item.text()
        return corrective_pose_name, pose_name

    def get_selected_corrective_and_drive(self):
        controller = self.controller
        if not controller:
            return None, None
        selection_model = self.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not selection_model:
            return None, None
        index = indexes[0]
        index = index.sibling(index.row(), 0)
        item = self._data_model.itemFromIndex(index)
        pose_name = item.text()
        pose = controller.poses.get(pose_name, None)
        if pose is None:
            return None, None
        if pose.is_corrective:
            return pose, None
        else:
            drive_pose = pose
        index = index.parent()
        index = index.sibling(index.row(), 0)
        item = self._data_model.itemFromIndex(index)
        if not item:
            return None, None
        pose_name = item.text()
        pose = controller.poses.get(pose_name, None)
        return pose, drive_pose

    def get_weight_of_selected_index(self):
        selection_model = self.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not selection_model:
            return None, None
        index = indexes[0]
        weight_index = index.sibling(index.row(), 2)
        widget = self.indexWidget(weight_index)
        if widget:
            return widget.value

    def update_fall_off(self):
        """
        Called to launch a dialog to modify the fall off value
        of selected corrective pose

        """
        pose, drive_pose = self.get_selected_corrective_and_drive()
        if not pose or not pose.is_corrective:
            OpenMaya.MGlobal.displayWarning("Selected item is not a valid corrective pose")
            return
        rbf_node_name = pose.rbf_node_name
        if not Node.object_exist(rbf_node_name):
            OpenMaya.MGlobal.displayWarning("{} does not exist".format(rbf_node_name))
            return
        rbf = Node(rbf_node_name)
        dialog = ScaleValueDialog(rbf, parent=self)
        dialog.show()


class CorrectivePoseEditor(QtWidgets.QWidget):
    """
    The GUI to manage all the CorrectivePoses.
    """

    def __init__(self, parent=None):
        super(CorrectivePoseEditor, self).__init__(parent=parent)
        self.setWindowTitle('Corrective Pose Editor')
        self.controller = None
        root_layout = QtWidgets.QVBoxLayout(self)
        self.pose_view = CorrectivePoseView(delegate=self)
        manager.corrective_pose_view = self.pose_view
        root_layout.addWidget(self.pose_view)
        actions_bar = QtWidgets.QToolBar("CorrectiveBar")
        actions_bar.setIconSize(QtCore.QSize(25, 25))
        actions_bar.addAction(action_api.PoseActions.new_corrective_action)
        actions_bar.addAction(action_api.PoseActions.del_corrective_action)
        root_layout.addWidget(actions_bar)

    def update_corrective_weight_from_maya(self):
        self.pose_view.update_corrective_weight_from_maya()

    def delete_drive_pose(self):
        controller = self.controller
        if controller:
            corrective_pose, drive_pose = self.pose_view.get_selected_corrective_and_drive()
            pose_controller.delete_corrective_drive(
                drive_pose,
                corrective_pose)
            SignalManager.corrective_pose_update.emit(corrective_pose)

    def delete_corrective_pose(self):
        controller = self.controller
        if controller:
            corrective_pose, _ = self.pose_view.get_selected_corrective_and_drive()
            if manager.Pose_Model:
                item = manager.Pose_Model.get_pose_item_by_pose_name(corrective_pose.name)
                manager.Pose_Model.delete_item(item)
            SignalManager.refresh_corrective_view_signal.emit()

    def delete_corrective_key(self):
        controller = self.controller
        if controller:
            corrective_pose, _ = self.pose_view.get_selected_corrective_and_drive()
            if len(corrective_pose.corrective_keys) <= 2:
                QtWidgets.QMessageBox.information(
                    self,
                    "Can't delete the current key!",
                    'The corrective pose must contain at least two keys!'
                )
                return
            corrective_pose.delete_corrective_key()
            SignalManager.corrective_pose_update.emit(corrective_pose)

    def add_corrective_pose_key(self):
        controller = self.controller
        if controller:
            corrective_pose, _ = self.pose_view.get_selected_corrective_and_drive()
            weight_index = corrective_pose.get_weight_index()
            if weight_index >= 0:
                answer = QtWidgets.QMessageBox.question(
                    self,
                    "Corrective key exists!",
                    'Found the corrective key weight:{0} exists at index:{1}. '
                    'Do you want to delete original key.'.format(corrective_pose.weight, weight_index)
                )
                if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                    corrective_pose.delete_corrective_key(weight_index)
                else:
                    return

            weight = self.pose_view.get_weight_of_selected_index()

            corrective_pose.add_corrective_key(weight=weight)
            SignalManager.corrective_pose_update.emit(corrective_pose)

    def update_corrective_pose_key(self):
        controller = self.controller
        if controller:
            corrective_pose, _ = self.pose_view.get_selected_corrective_and_drive()
            weight_index = corrective_pose.get_weight_index()
            if weight_index >= 0 and weight_index != corrective_pose.current_corrective_index:
                answer = QtWidgets.QMessageBox.question(
                    self,
                    "Corrective key exists!",
                    'Found the corrective key weight:{0} exists at index:{1}. '
                    'Do you want to delete original key.'.format(corrective_pose.weight, weight_index)
                )
                if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                    corrective_pose.delete_corrective_key(weight_index)
                    corrective_pose.add_corrective_key()
                    SignalManager.corrective_pose_update.emit(corrective_pose)
                else:
                    return
            corrective_pose.update_corrective_key()
            SignalManager.corrective_pose_update.emit(corrective_pose)

    def add_corrective_drive(self):
        """

        add pose to current corrective pose.

        """
        controller = self.controller
        if controller:
            corrective_pose, _ = self.pose_view.get_selected_corrective_and_drive()
            drive_pose = manager.pose_controller.active_pose
            if not drive_pose:
                return
            if drive_pose.is_corrective:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error!",
                    "You can't use a corrective pose({0}) as the drive pose.".format(drive_pose.name)
                )
                return
            pose_controller.add_corrective_drive(
                drive_pose, corrective_pose)
            SignalManager.corrective_pose_update.emit(None)


class ScaleValueDialog(QtWidgets.QDialog):
    def __init__(self, rbf_node, parent=None):
        super(ScaleValueDialog, self).__init__(parent=parent)
        self.setWindowTitle("Rbf Fall Off Setter")
        self.rbf_node = rbf_node
        layout = QtWidgets.QHBoxLayout(self)
        label = QtWidgets.QLabel("Fall off:")
        self.spin = QtWidgets.QDoubleSpinBox(self)
        self.spin.setMaximum(2)
        self.spin.setMinimum(0.01)
        self.spin.setSingleStep(0.02)
        layout.addWidget(label)
        layout.addWidget(self.spin)
        self.setMinimumWidth(250)
        current_val = self.rbf_node.scale.value
        self.spin.setValue(current_val)
        self.spin.valueChanged.connect(self.set_fall_off_cb)

    def set_fall_off_cb(self, value):
        try:
            self.rbf_node.scale.value = value
        except RuntimeError as e:
            OpenMaya.MGlobal.displayWarning(str(e))



