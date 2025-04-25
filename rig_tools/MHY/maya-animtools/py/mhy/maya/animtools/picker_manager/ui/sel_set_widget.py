"""

The UI for selection set management

"""

from PySide2 import QtWidgets, QtCore
import mhy.maya.animtools.picker_manager.api.sel_set as sel_set_api
from mhy.qt.icon_lib.api import get_icon

import maya.cmds as cmds


class SelSetWidget(QtWidgets.QWidget):
    """
    This widget display the selection set as action buttons. User
    can add selection button in the rig file or remove existing ones
    """
    sel_set_clicked_signal = QtCore.Signal()

    def __init__(self, parent=None):
        super(SelSetWidget, self).__init__(parent=parent)
        self.current_namespace = ""
        layout = QtWidgets.QHBoxLayout(self)
        dummy_widget = QtWidgets.QWidget()
        self.pb_layout = QtWidgets.QHBoxLayout()
        self.pb_layout.setContentsMargins(0, 0, 0, 0)
        dummy_widget.setLayout(self.pb_layout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(dummy_widget)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(65)
        layout.addWidget(scroll)
        icon = get_icon(sub_dir='/IOS/general/png/48/add.png', color=[255, 255, 255])
        self.add_pb = QtWidgets.QPushButton(icon, '')
        self.add_pb.setFixedSize(40, 40)
        self.add_pb.setToolTip("Add a selection set for selected pickers")

        icon = get_icon(sub_dir='/IOS/general/png/48/delete.png', color=[255, 255, 255])
        self.remove_pb = QtWidgets.QPushButton(icon, "")
        self.remove_pb.setFixedSize(40, 40)
        self.remove_pb.setToolTip("Remove selection set")
        self.remove_pb.clicked.connect(self.remove_set_set_cb)

        layout.addWidget(self.add_pb)
        layout.addWidget(self.remove_pb)
        layout.setContentsMargins(2, 2, 2, 2)
        self.add_pb.clicked.connect(self.add_set_cb)
        self.setFixedHeight(65)
        self.setToolTip("The Selection Set Action for selected picker(s)")

    def refresh_pb(self, targets=None):
        """
        Refresh the push buttons based on selected objects. Only the push button for selection
        sets the any of the selected objects are belong to will be prompted

        Args:
            targets(list): Selected objects

        """
        for i in reversed(range(self.pb_layout.count())):
            self.pb_layout.itemAt(i).widget().setParent(None)

        root = sel_set_api.find_root_set(self.current_namespace)
        if root:
            results = list()
            if targets:
                for tgt in targets:
                    sel_sets = sel_set_api.find_related_selection_set(obj=tgt, name_space=self.current_namespace)
                    results.extend(sel_sets)
                results = list(set(results))
                for sel_set in results:
                    set_name = sel_set.name
                    set_name = sel_set_api.simplfy_set_name(set_name)
                    pb = QtWidgets.QPushButton(set_name)
                    pb.clicked.connect(lambda checked=True, set_obj=sel_set: self.sel_action_clicked(set_obj))
                    tool_tip_str = ','.join(sel_set.members)
                    pb.setToolTip(tool_tip_str)
                    self.pb_layout.addWidget(pb)

    def sel_action_clicked(self, sel_obj):
        """
        Called when a push button is clicked to select a selection set
        Args:
            sel_obj(str): The name of the selection set

        Returns:

        """
        sel_set_api.select_set(sel_obj)
        self.sel_set_clicked_signal.emit()

    def add_set_cb(self):
        """
        Called when add selection button is clicked

        """
        dialog = QtWidgets.QInputDialog(parent=self)
        sel = cmds.ls(sl=True)
        set_name, ok = QtWidgets.QInputDialog.getText(
            dialog, 'Set Name', 'Enter the name of the selection set')
        if not ok:
            return
        sel_set_api.create_selection_set(name=set_name)
        self.refresh_pb(sel)

    def remove_set_set_cb(self):
        """
        Called when remove selection set buton is clicked
        """
        dialog = DeleteSelSetDialog(self)
        dialog.refresh_list()
        dialog.show()


class DeleteSelSetDialog(QtWidgets.QDialog):
    """
    A dialog to delete picker selection set from the scene
    """
    def __init__(self, parent=None):
        super(DeleteSelSetDialog, self).__init__(parent=parent)
        self.setWindowTitle("Delete Selection Set")
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.apply_cb)
        button_box.rejected.connect(self.close)

        layout.addWidget(self.list_widget)
        layout.addWidget(button_box)

    def refresh_list(self):
        """
        Refresh the selection set list widget

        """
        self.list_widget.clear()
        sel_sets = sel_set_api.list_picker_sets_with_namespace()
        sel_set_names = [i.name for i in sel_sets]
        self.list_widget.addItems(sel_set_names)

    def apply_cb(self):
        """
        Called when Ok button is clicked. Selected selection sets will be deleted
        """
        selection = self.list_widget.selectedItems()
        selection = [i.data(QtCore.Qt.DisplayRole) for i in selection]
        selection = [i for i in selection if cmds.objExists(i)]

        result = QtWidgets.QMessageBox.question(self, "Delete", "Deletion is non-revertible. Are you sure?")
        if result != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        cmds.delete(selection)
        self.close()
