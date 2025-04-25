"""
A pose tree Widget to manage the poses.
"""
import json
import os
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import mhy.maya.rigtools.pose_editor.api.pose_controller as p_ctrl
from PySide2 import QtCore, QtGui, QtWidgets
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.maya.rigtools.pose_editor.settings import Settings
import mhy.maya.rigtools.pose_editor.api.utils as utils
import mhy.maya.rigtools.pose_editor.ui.model.pose_tree_model as pose_model
import mhy.maya.rigtools.pose_editor.ui.widget.driver_property as dp
from mhy.python.core.compatible import gzip_export
import mhy.maya.rigtools.pose_editor.ui.widget.pose_splitter_dialog as psd
import mhy.maya.rigtools.pose_editor.ui.manager as manager


class PoseListView(MayaQWidgetDockableMixin, QtWidgets.QTreeView):
    """
    The list view of face expression pose.
    """
    _pre_excluded = 9
    kInt = 1
    kShowTotal = 2

    def __init__(self, parent=None):
        super(PoseListView, self).__init__(parent=parent)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setStyleSheet("selection-background-color: #595d58")

        # Drag weight related variables
        self._drag_current_count = 0
        self.dragging_pose = None
        self.is_dragging = False
        self.__last_position = None
        self.__origin_position = None
        self.__last_index = None

        # Connect signals
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.launch_context_menu)
        self.setDropIndicatorShown(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setMouseTracking(True)
        self.entered.connect(self.enter_item)

    def select_pose(self, pose_name):
        index = self.data_model.get_index_by_pose_name(pose_name)
        if not index:
            print('failed to find pose {}'.format(pose_name))
        sel_model = self.selectionModel()
        if sel_model:
            sel_model.select(
                index,
                QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)

    @property
    def data_model(self):
        """
        Get the model of this view
        Returns:
            (PoseTreeModel)

        """
        return self.model()

    def mouseDoubleClickEvent(self, event):
        """
        Override double click event to turn on/off selected pose
        Args:
            event(QMouseEvent): Passed in

        """
        position = event.pos()
        index = self.indexAt(position)
        item = self.model().item_from_index(index)
        if item.type_str == 'pose':
            if item.weight < 0.01:
                self.model().update_pose_weight(item, Settings.maximum_weight)
            else:
                self.model().update_pose_weight(item, 0)
            self.update(index.parent())
            SignalManager.pose_selection_changed.emit(item)
            SignalManager.update_influence_attribute_signal.emit(item.pose)

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
        menu.exec_(self.viewport().mapToGlobal(position))

    def make_context_menu(self, index):
        """
        Create a menu based on the selected index
        Args:
            index(QModelIndex):

        Returns:
            QtWidgets.QMenu: Created menu instance

        """
        item = self.data_model.item_from_index(index)

        menu = QtWidgets.QMenu()
        menu.addAction(self.tr("Export Pose(s)"), lambda: self.do_export_cb(item))
        menu.addSeparator()

        menu.addAction(self.tr("Add Group"), lambda: self.do_add_group_cb(index))
        menu.addAction(self.tr("Add Pose"), lambda: self.do_add_pose_cb(index))
        menu.addSeparator()

        if item.type_str == 'pose':
            menu.addAction(self.tr("Import Pose"), lambda: self.do_import_cb(item))
            menu.addAction(self.tr("Delete Pose"), lambda: self.do_delete_cb(item))
            menu.addAction(self.tr("Rename Pose"), lambda: self.do_rename_cb(index))
            menu.addSeparator()
            menu.addAction(self.tr("Split Pose"), lambda: self.launch_pose_splitter_cb(item))
            menu.addAction(self.tr("Driver Property"), lambda: self.launch_driver_property_cb(item))

        elif item.type_str == 'group':
            menu.addAction(self.tr("Delete Group"), lambda: self.do_delete_cb(item))
            menu.addAction(self.tr("Rename Group"), lambda: self.do_rename_cb(index))

        return menu

    # =========================================
    # Action callback methods
    # =========================================
    def do_import_cb(self, item):
        """
        This callback triggered when user is about to import and merge a json data to an item

        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Choose import file name",
            "",
            "Pose data files (*.mhy) ;; Compressed Pose data files (*.gmhy);; All files (*.*)")

        self.data_model.import_data_to_item(file_path, item)

    def do_export_cb(self, item):
        """
        This callback triggered when user is about to export a json data from an item
        Args:
            item(PoseItem or GroupItem): The item and the children below it will be exported

        Returns:
            dict: Exported data in dict format

        """
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Choose export file name",
            "",
            "Pose data files (*.mhy) ;; Compressed Pose data files (*.gmhy);; All files (*.*)")

        if file_path:
            data = self.export_data(file_path=file_path, root=item, compress=False)
            return data

    def do_rename_cb(self, index):
        """
        This callback triggered when user is about to rename an item
        Args:
            index(QModelIndex): The index associated with the item to be renamed

        """
        if index.isValid:
            self.edit(index)

    def do_delete_cb(self, item):
        """
        This callback triggered when user is about to delete an item
        Args:
            item(PoseItem or GroupItem): The item passed in to be deleted

        """
        answer = QtWidgets.QMessageBox.question(
            self,
            "Delete action",
            "Deletion is non-revertible. Are you sure?")
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            self.data_model.delete_item(item)

    def do_add_pose_cb(self, index):
        """
        This callback triggered when user is about to add a pose item
        Args:
            index(QModelIndex): The index under which the new pose will be created

        """
        dialog = QtWidgets.QInputDialog()
        pose_name, ok = QtWidgets.QInputDialog.getText(
            dialog, 'text', 'Enter some text')
        if ok and pose_name:
            item = self.data_model.item_from_index(index)
            added_index = None

            if item.type_str == 'pose':
                parent = item.parent
                added_index = self.data_model.create_pose(
                    pose_name,
                    parent=parent,
                    after_row=item.row+1)

            elif item.type_str == 'group':
                added_index = self.data_model.create_pose(
                    pose_name,
                    parent=item)

            if added_index:
                selection_model = self.selectionModel()
                if selection_model:
                    selection_model.select(
                        added_index,
                        QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)

    def do_add_group_cb(self, index):
        """
        This callback triggered when user is about to add a group item
        Args:
            index(QModelIndex): The index under which the new group will be created

        """
        dialog = QtWidgets.QInputDialog()
        group_name, ok = QtWidgets.QInputDialog.getText(
            dialog, 'text', 'Enter some text')
        if ok and group_name:
            item = self.data_model.item_from_index(index)
            group_name = group_name.upper()
            for child in item.children:
                if child.name == group_name:
                    QtWidgets.QMessageBox.information(
                        self,
                        "Duplicated Group Name",
                        "Child group named {} already exists under group".format(group_name, item.full_path()))
                    return
            added_index = None
            if item.type_str == 'pose':
                parent = item.parent
                added_index = self.data_model.create_group(
                    group_name,
                    parent=parent,
                    after_row=item.row+1)

            elif item.type_str == 'group':
                added_index = self.data_model.create_group(
                    group_name,
                    parent=item)

            if added_index:
                selection_model = self.selectionModel()
                if selection_model:
                    selection_model.setCurrentIndex(
                        added_index,
                        QtCore.QItemSelectionModel.ClearAndSelect|QtCore.QItemSelectionModel.Rows)

    def launch_pose_splitter_cb(self, item):
        """
        This callback triggered when user is about to split the pose
        Args:
            item(PoseItem): The pose item to be splitted

        """
        if item.type_str == "pose":
            ui = psd.PoseSplitDialog(item, self)
            ui.show()

    def launch_driver_property_cb(self, item):
        """
        This callback triggered when user is about to set the driver configuration for an item
        Args:
            item(PoseItem): The item whose driver property will be modified

        """
        if item.type_str == "pose":
            pose = item.pose
            ui = dp.DriverPropertyWidget(self)
            ui.init_widgets(pose)
            ui.show()

    def set_draggable_cb(self, state):
        """
        Enable/Disable the drag and drop mode
        Args:
            state(bool): If turn on the drag drop mode

        """
        self.setDragEnabled(state)
        self.setAcceptDrops(state)

    # =========================================
    # Utility methods
    # =========================================

    def __get_pose_expand_recurse(self, parent_item):
        """
        Recursively Go through the descendent of a given item, and return all expanded ones
        in a dictionary
        Args:
            parent_item(GroupItem):

        Returns:
            dict: Expanded items

        """
        pose_expand = {}
        for child in parent_item.children:
            pose_name = child.name
            index = self.data_model.index_of(child)
            if child.children and self.isExpanded(index):
                pose_expand[pose_name] = self.__get_pose_expand_recurse(child)
        return pose_expand

    def set_pose_expand_recurse(self, parent_item, pose_expand):
        """
        Update the expanded status of the descendents of a given item according
        to a dictionary.
        Args:
            parent_item(GroupItem):
            pose_expand(dict):

        """
        for child in parent_item.children:
            pose_name = child.name
            if child.children:
                index = self.data_model.index_of(child)
                if pose_name in pose_expand:
                    self.setExpanded(index, True)
                    self.set_pose_expand_recurse(
                        child, pose_expand.get(pose_name))
                else:
                    self.setExpanded(index, False)

    def export_data(self, file_path=None, root=None, compress=False):
        """
        This method will export data from selected item. The tree view will add expand information
        on top of data exported from model
        Args:
            file_path(str):
            root(GroupItem or PoseItem):
            compress(bool):

        Returns:

        """
        progress_lambda = utils.progress_lambda_begin(
            title='Exporting Poses',
            status='Preparing for exporting: {}'.format(file_path),
            isInterruptable=False)
        data = self.data_model.export_data(
            None,
            progress_lambda=progress_lambda,
            root=root)
        if file_path:
            data_str = json.dumps([data],
                                  sort_keys=True,
                                  indent=4,
                                  separators=(',', ': '))
            if compress:
                gzip_export(data_str, file_path)
            else:
                with open(file_path, 'w') as out_file:
                    out_file.write(data_str)
        utils.progress_lambda_end()
        return data

    def export_all_data(self, file_path):
        pose_controls = p_ctrl.list_pose_controllers()
        for pc in pose_controls:
            output_file_path = os.path.join(file_path, '{}.mhy'.format(pc))
            progress_lambda = utils.progress_lambda_begin(
                title='Exporting Poses from'.format(pc),
                status='Preparing for exporting: {}'.format(file_path),
                isInterruptable=False)
            if pc == self.data_model.controller.node_name:
                data = self.data_model.export_data(
                    None,
                    progress_lambda=progress_lambda)
            else:
                pc = p_ctrl.PoseController(pc)
                data = pc.export_data(progress_lambda=progress_lambda)

            if file_path:
                data_str = json.dumps([data],
                                      sort_keys=True,
                                      indent=4,
                                      separators=(',', ': '))
                with open(output_file_path, 'w') as out_file:
                    out_file.write(data_str)
            utils.progress_lambda_end()

    # ===============================================
    # Override virtual methods to mimic slider widget
    # ===============================================

    def enter_item(self, index):
        """
        Override enter event to update cursor to indicate weight slider
        Args:
            index(QModelIndex):

        Returns:

        """
        if self.is_dragging:
            return
        if index.isValid():
            item = self.data_model.item_from_index(index)
            if index.column() == 1 and item.type_str == "pose":
                self.setCursor(QtCore.Qt.IBeamCursor)
                return
        self.setCursor(QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit mouseMoveEvent.
        update the value while dragging the mouse.
        """
        super(PoseListView, self).mouseMoveEvent(event)
        if self.is_dragging:
            self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            if self._drag_current_count == PoseListView._pre_excluded:
                self.on_drag_enter()
            if self._drag_current_count >= PoseListView._pre_excluded:
                # item = self.data_model.item_from_index(self.__last_index)
                self.on_drag(self.__last_index)
                # self.data_model.update_pose_weight(item.pose, item.weight)

            self._drag_current_count += 1

    def on_drag_enter(self):
        """function will be called if the mouse was hold down for the amount
        of on_dragEnter"""
        self.setCursor(QtCore.Qt.BlankCursor)

    def on_drag(self, index):
        """function will be called everytime you drag your mouse but first
        after on_drag"""
        current_position = QtGui.QCursor.pos()
        current_x = current_position.x()
        if abs(current_x - self.__last_position.x()) < 10:
            return
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        item = self.data_model.item_from_index(index)
        step_size = item.step
        # ignore the drag move less than 10 pixels.
        tolerate = 10.0
        if modifiers == QtCore.Qt.ControlModifier:
            step_size = 0.1*item.step
        current_weight = item.weight
        current_weight += step_size * round((current_x - self.__last_position.x()) / tolerate)
        value = max(min(current_weight, item.high), item.low)
        # sets the new text
        self.data_model.setData(index, value)
        self.__last_position = current_position
        # reset the cursor if it reaches the end of the screen
        desktop_width = QtWidgets.QApplication.desktop().availableGeometry().width()
        if current_x == (desktop_width - 1):
            QtGui.QCursor.setPos(0, QtGui.QCursor.pos().y())
        elif current_x == 0:
            QtGui.QCursor.setPos(desktop_width - 1, QtGui.QCursor.pos().y())
        pose = item.pose
        if pose:
            SignalManager.pose_changed_signal.emit(pose, value)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit mousePressEvent.
        record the initial value when begin drag mouse.
        """
        super(PoseListView, self).mousePressEvent(event)

        index = self.indexAt(event.pos())
        if index.isValid():
            item = self.data_model.item_from_index(index)
            if not item.type_str == 'pose':
                return
            pose = item.pose
            if pose.is_corrective:
                return
            if index.column() == pose_model.PoseTreeModel.Weight_Index:
                self.setCursor(QtCore.Qt.SplitHCursor)
                self.is_dragging = True
                current_pos = QtGui.QCursor.pos()
                self.__last_position = current_pos
                self.__origin_position = current_pos
                self.__last_index = index

    def mouseReleaseEvent(self, event):
        """
        function will be called if the mouse was released
        """
        super(PoseListView, self).mouseReleaseEvent(event)
        if self.is_dragging:
            # if the mouse was released we need to put the mouse to its last pos
            QtGui.QCursor.setPos(self.__origin_position)
            self.setCurrentIndex(self.__last_index)
            self.setCursor(QtCore.Qt.IBeamCursor)
            self.__last_position = None
            item = self.data_model.item_from_index(self.__last_index)
            if manager.pose_controller.active_pose == item.pose:
                SignalManager.update_influence_attribute_signal.emit(item.pose)
            self.__last_index = None

            self.__origin_position = None
            self.is_dragging = False
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
