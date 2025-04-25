"""
This module create a widget for display and editing poses for a given controller.

"""
from PySide2 import QtWidgets, QtCore
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import mhy.maya.rigtools.pose_editor.ui.manager as manager
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
import mhy.maya.rigtools.pose_editor.ui.model.pose_tree_model as ptm
import mhy.maya.rigtools.pose_editor.ui.view.pose_tree_view as ptv
import mhy.maya.rigtools.pose_editor.ui.delegate.pose_tree_delegate as ptd


class PoseTreeWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(PoseTreeWidget, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle('Pose Tree View')
        self.setLayout(layout)

        self.view = ptv.PoseListView(parent=self)
        manager.Pose_View = self.view
        self.model = ptm.PoseTreeModel()
        manager.Pose_Model = self.model
        self.view.setModel(self.model)
        self.view.setMinimumWidth(600)
        self.view.setColumnWidth(0, 280)
        self.view.setColumnWidth(1, 180)
        self.view.setColumnWidth(2, 90)
        self.view.setColumnWidth(3, 48)
        sel_model = self.view.selectionModel()
        section_header = self.view.header()
        section_header.setSectionsClickable(True)
        section_header.sectionClicked.connect(self.switch_targets_mode_cb)
        delegate = ptd.ActionListItemDelegate()
        self.view.setItemDelegate(delegate)
        self.drag_check_box = QtWidgets.QCheckBox('Enable draggable', parent=self)
        self.drag_check_box.stateChanged.connect(self.view.set_draggable_cb)
        self.drag_check_box.setChecked(False)
        layout.addWidget(self.view)
        layout.addWidget(self.drag_check_box)

        self.model.Update_Select_Signal.connect(self.view.setCurrentIndex)
        sel_model.selectionChanged.connect(self.sel_changed_cb)

    def switch_targets_mode_cb(self, index):
        """
        Callback method to swtich the blend shape enabled/disabled mode
        Args:
            index(int):

        """
        if index == self.model.Targets_Index and self.model.controller:
            if self.model.controller.target_is_enabled():
                self.model.controller.set_target_status(0.0)
            else:
                self.model.controller.set_target_status(1.0)
            self.model.update_target_status()

    def set_controller(self, controller):
        """
        Set the internal controller of the data model. This call will also update
        selection based on the controller's active pose

        Args:
            controller(PoseController):

        """
        if not controller:
            controller = None
        manager.pose_controller = controller
        self.model.controller = controller  # Populate pose items to the pose tree model
        SignalManager.pose_selection_changed.emit(None)

    def sel_changed_cb(self, sel, desel):
        """
        Callback triggered when user select different pose in the view
        Args:
            sel(QItemSelection): Selected items
            desel(QItemSelection): Deselected items(not used)


        """
        del desel

        indexes = sel.indexes()
        item = None
        if indexes:
            item = self.model.item_from_index(indexes[0])
        if not item:
            return

        if self.model:
            if item.type_str == 'pose':
                self.model.controller.active_pose = item.pose
            else:
                self.model.controller.active_pose = None

        SignalManager.pose_selection_changed.emit(item)

        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()

        if modifiers == QtCore.Qt.AltModifier and item.type_str == 'pose':
            self.model.reset_weights()
            self.model.update_pose_weight(item, 10)
