"""
The action buttons collection for the pose.
"""
from PySide2 import QtWidgets, QtCore, QtGui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import cmds
import maya.OpenMaya as OpenMaya
import math
from mhy.maya.rigtools.pose_editor.api.influence import get_influence_names
from mhy.maya.nodezoo.node import Node
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.ui.widget.slider_widget import SliderWidget
import mhy.maya.rigtools.pose_editor.ui.manager as manager
from mhy.qt.core.utils import get_icon
from mhy.maya.utils import undoable


class PoseActionView(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """
    The action buttons collection for the pose.
    """

    add_icon = get_icon('add.png', QtGui.QColor(179, 226, 131))
    remove_icon = get_icon('delete.png', QtGui.QColor(233, 148, 151))
    edit_icon = get_icon('edit_mode.png', QtGui.QColor(232, 228, 110))
    reset_icon = get_icon('cancel.png', QtGui.QColor(243, 197, 131))

    def __init__(self, parent):
        super(PoseActionView, self).__init__(parent=parent)
        self.setWindowTitle('Deformers')
        self.dialog = None
        self.keys_group_widget = QtWidgets.QGroupBox("Weights:     CTRL+LMB to delete the key.")
        self.tab_widget = QtWidgets.QTabWidget(self)
        tab_bar = QtWidgets.QTabBar(self)
        self.tab_widget.setTabBar(tab_bar)
        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.addWidget(self.keys_group_widget)
        self.root_layout.addWidget(self.tab_widget)
        self.weight_buttons = dict()
        self._init_ui()
        SignalManager.pose_selection_changed.connect(
            self.__update_widgets)
        SignalManager.update_influence_attribute_signal.connect(self.__update_widgets)

    def __update_widgets(self, pose=None):
        """
        Update key button highlight based on current pose weight value.

        Args:
            pose(Pose):

        Returns:

        """
        if not manager.pose_controller:
            return
        active_pose = manager.pose_controller.active_pose
        if pose is None:
            pose = active_pose
        if not pose or active_pose != pose:
            return
        value = pose.weight
        # update slider
        # self.slider_widget.value = value
        # update weight buttons
        for weight, button in self.weight_buttons.items():
            # restore to default first.
            button.setStyleSheet("QPushButton {}")
            style = "border-radius: 8px;"
            if pose.has_target(weight/10.0):
                style += "font-weight: bold; background-color: green;"
            else:
                style += "background-color: gray;"
            if weight == value:
                style += "border: 2px solid white;"

            button.setStyleSheet("QPushButton {{{0}}}".format(style))
            button.update()

        current_weight_is_key = pose.has_weight_key(value)

        if value != 0.0 and not current_weight_is_key:
            self.__slider_add_key_button.setIcon(PoseActionView.add_icon)
            self.__slider_add_key_button.setToolTip("Add a new key at current weight")
        else:
            self.__slider_add_key_button.setIcon(PoseActionView.edit_icon)
            self.__slider_add_key_button.setToolTip("Edit the key at current weight")

        current_value_is_target = pose.has_target(value/10.0)
        self.__mirror_target_button.setEnabled(current_value_is_target)
        self.__delete_target_button.setEnabled(current_value_is_target)

    def _init_ui(self):
        """
        initialize the children widgets.
        """
        v_layout = QtWidgets.QVBoxLayout(self.tab_widget)
        self.root_layout.addLayout(v_layout)
        keys_layout = QtWidgets.QVBoxLayout(self.keys_group_widget)
        weight = Settings.maximum_weight
        pose = self.get_active_pose()
        if pose:
            weight = pose.weight
        self.slider_widget = SliderWidget(
            delegate=None,
            value=weight,
            parent=self,
            callbacks={'changing': [self.changing_callback],
                       'changed': [self.changed_callback]},
            change_signal=SignalManager.pose_changed_signal)

        buttons_widget = QtWidgets.QWidget(self)
        keys_layout.addWidget(buttons_widget)
        slider_layout = QtWidgets.QHBoxLayout(self.keys_group_widget)
        keys_layout.addLayout(slider_layout)
        slider_layout.addWidget(self.slider_widget)

        self.__slider_add_key_button = QtWidgets.QPushButton(PoseActionView.add_icon, '', self)
        self.__slider_add_key_button.setToolTip("Add a new key at current weight")
        self.__slider_add_key_button.clicked.connect(self.do_key_current_pose)
        self.__slider_add_key_button.setFixedSize(37, 37)
        slider_layout.addWidget(self.__slider_add_key_button)
        button = QtWidgets.QPushButton(PoseActionView.reset_icon, '', self)
        button.setToolTip("Reset active pose")
        button.setFixedSize(37, 37)
        button.clicked.connect(lambda: self.do_reset_pose(True))
        slider_layout.addWidget(button)
        self.weight_buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)

        v_layout.addWidget(self.tab_widget)
        pose_widget = QtWidgets.QWidget(parent=self)
        self.tab_widget.addTab(pose_widget, "Influence")
        v_layout = QtWidgets.QVBoxLayout(pose_widget)
        influence_group_widget = QtWidgets.QWidget(self)
        v_layout.addWidget(influence_group_widget)
        g_layout = QtWidgets.QHBoxLayout(influence_group_widget)
        button = QtWidgets.QPushButton('Add Influences', self)
        button.clicked.connect(self.do_influences_add)
        g_layout.addWidget(button)

        button = QtWidgets.QPushButton('Select Influences', self)
        button.clicked.connect(self.do_influences_select_all)
        g_layout.addWidget(button)

        button = QtWidgets.QPushButton('Remove Influences', self)
        button.clicked.connect(self.do_influences_remove)
        g_layout.addWidget(button)

        # Target Action Tab.
        target_widget = QtWidgets.QWidget(self)
        v_layout = QtWidgets.QVBoxLayout()
        target_widget.setLayout(v_layout)

        self.__switch_sculpt_mode_button = QtWidgets.QPushButton('Enter Sculpt Mode', self)
        self.__switch_sculpt_mode_button.clicked.connect(self.switch_sculpt_mode)
        v_layout.addWidget(self.__switch_sculpt_mode_button)

        g_layout = QtWidgets.QGridLayout()
        v_layout.addLayout(g_layout)

        self.__save_sculpt_target = QtWidgets.QPushButton(
            'Save Sculpt', self)
        self.__save_sculpt_target.clicked.connect(self.do_save_sculpt)
        g_layout.addWidget(self.__save_sculpt_target, 0, 0)

        self.__save_selected_target = QtWidgets.QPushButton(
            'Save Selected Target', self)
        g_layout.addWidget(self.__save_selected_target, 0, 1)

        self.__delete_target_button = QtWidgets.QPushButton(
            'Delete Target', self)
        self.__delete_target_button.clicked.connect(self.do_target_delete)
        g_layout.addWidget(self.__delete_target_button, 1, 0)

        self.__mirror_target_button = QtWidgets.QPushButton(
            'Mirror Target Mesh', self)
        self.__mirror_target_button.clicked.connect(self.do_target_mirror)
        g_layout.addWidget(self.__mirror_target_button, 1, 1)

        self.tab_widget.addTab(target_widget, "Target")

        self.update_key_view()
        self.__update_widgets()

    @ staticmethod
    def changing_callback(widget):
        """
        Called while value is changing
        Args:
            widget:

        Returns:

        """
        weight = widget.value
        if not widget.delegate:
            return
        widget.delegate.weight = weight
        manager.Pose_Model.update_pose_weight(widget.delegate, weight)

    def changed_callback(self, widget):
        """
        Called while value been changed
        Args:
            widget:

        Returns:

        """
        widget.delegate.weight = widget.value
        if not widget.delegate:
            return
        SignalManager.update_influence_attribute_signal.emit(widget.delegate)
        self.__update_widgets(widget.delegate)

    def select_delta(self):
        """
        select delta meshes.
        """
        pose = self.get_active_pose()
        if pose is None:
            return
        target = pose.get_target(pose.weight)
        if target:
            target.select_sculpt_mesh()
        else:
            cmds.select(deselect=True)

    def get_weight_button_pressed_callback(self, weight):
        """
        The function generate the call back for key buttons.
        """
        def weight_button_callback():
            """
            Push the weight button call back.
            Press to set the current wight to button's weight value.
            Press with CTRL to delete the key.
            """
            pose = manager.pose_controller.active_pose
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier and weight not in [0.0]:
                manager.pose_controller.delete_key(weight)
                self.update_key_view()
            else:
                for _, button in self.weight_buttons.items():
                    button.setChecked(False)
                    button.update()
                pose.weight = weight
                manager.Pose_Model.update_pose_weight(pose, weight)
                SignalManager.update_influence_attribute_signal.emit(pose)
                SignalManager.pose_changed_signal.emit(pose, weight)
        return weight_button_callback

    def update_key_view(self, pose=None):
        """
        Update the keys buttons view.
        The function should be excuted when add/del the keys.
        """
        # keys buttons layout
        for i in reversed(range(self.weight_buttons_layout.count())):
            item = self.weight_buttons_layout.itemAt(i)
            item.widget().deleteLater()
            self.weight_buttons_layout.removeItem(item)
        self.weight_buttons.clear()

        if not pose:
            if not manager.pose_controller:
                return
            pose = manager.pose_controller.active_pose
            if not pose:
                return
        keys = pose.weight_keys
        weight = pose.weight
        self.slider_widget.delegate = pose
        self.slider_widget.value = weight
        for key in keys:
            button = QtWidgets.QPushButton(self)
            display_key = math.floor(key * 100) / 100.0  # display only 2 decimals but not round it
            button.setText(str(display_key))
            button.setMaximumWidth(64)
            button.clicked.connect(
                self.get_weight_button_pressed_callback(key))
            self.weight_buttons[key] = button
            self.weight_buttons_layout.addWidget(button)
        self.__update_widgets()
        self.keys_group_widget.update()

    def update_ui(self, pose=None):
        """
        update the view when information changed.
        """
        if pose:
            self.slider_widget.delegate = pose
            self.keys_group_widget.setEnabled(True)
        else:
            self.slider_widget.delegate = None
            self.keys_group_widget.setEnabled(False)
        self.update_key_view()
        self.update_switch_sculpt_pb()

    @staticmethod
    def get_active_pose():
        """
        get the active pose of the controller
        """
        if manager.pose_controller and manager.pose_controller.active_pose:
            return manager.pose_controller.active_pose
        return None

    # Pose action implementations.
    def do_key_current_pose(self):
        """
        do save pose action.
        """
        pose = self.get_active_pose()
        if not pose:
            return
        manager.pose_controller.key_current_pose()
        self.update_key_view()
        self.__update_widgets(pose)

    def do_reset_pose(self, prompt=True):
        """
        do remove pose action.
        """
        pose = self.get_active_pose()
        if not pose:
            return
        if prompt:
            confirm_info = cmds.confirmDialog(
                title='Delete all pose keys!',
                message='Are you sure to delete all the keys of the pose:{}?'.format(pose.name),
                button=['Yes', 'No'],
                defaultButton='No',
                cancelButton='No',
                dismissString='No')
            if confirm_info != 'Yes':
                return
        manager.pose_controller.reset_pose(pose.name, remove_influence=False)
        SignalManager.influence_update.emit()
        manager.Pose_Model.refresh_pose(pose)
        SignalManager.update_influence_attribute_signal.emit(pose)
        self.__update_widgets(pose)

    def do_influences_add(self):
        """
        do add target action.
        """
        active_pose = self.get_active_pose()
        if not active_pose:
            return
        influence_names = get_influence_names() or []
        added_influences = active_pose.add_influences(influence_names)

        # UI updates
        manager.pose_controller.selected_influences = set(added_influences)
        manager.Influence_Model.populate(active_pose.influences.values())
        active_pose.select_influences(added_influences)
        SignalManager.update_influence_attribute_signal.emit(active_pose)
        manager.Pose_Model.refresh_pose(active_pose)

    @undoable
    def do_influences_remove(self):
        """
        Call back method to remove selected influences from active pose
        """
        active_pose = self.get_active_pose()
        if not active_pose:
            return
        answer = QtWidgets.QMessageBox.question(
            self,
            "Delete selected influences?",
            'Are you sure to delete the selected influences?')
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            highlight_influences = manager.pose_controller.selected_influences
            active_pose.delete_influences(highlight_influences)
            SignalManager.update_influence_attribute_signal.emit(active_pose)
            manager.Pose_Model.refresh_pose(active_pose)
            cmds.select(clear=True)

    @staticmethod
    def do_influences_select_all():
        """
        select all influences.
        """
        manager.select_active_pose_influences()
        active_pose = manager.pose_controller.active_pose
        if not active_pose:
            return
        manager.pose_controller.selected_influences = set(active_pose.influences.keys())
        SignalManager.influence_update.emit()

    # Target Action Tab.
    def switch_sculpt_mode(self):
        """
        do add target action.
        """
        if not manager.pose_controller:
            return
        if manager.pose_controller.is_sculpting:
            manager.pose_controller.remove_sculpt_mesh()

        else:
            sculpt_geo = manager.pose_controller.create_sculpt_mesh()
            if sculpt_geo:
                OpenMaya.MGlobal.displayInfo("Created sculpt geo")
        self.__update_widgets()
        self.update_switch_sculpt_pb()

    def update_switch_sculpt_pb(self):
        """
        Update switch sculpt push button based on current state

        """
        if not manager.pose_controller:
            return
        if manager.pose_controller.is_sculpting:
            self.__switch_sculpt_mode_button.setText("Leave Sculpt Mode")
            self.__switch_sculpt_mode_button.setStyleSheet("background-color: #AB6B51")
        else:
            self.__switch_sculpt_mode_button.setText("Enter Sculpt Mode")
            self.__switch_sculpt_mode_button.setStyleSheet("background-color: #2F435A")

    def do_save_sculpt(self):
        if not manager.pose_controller:
            return
        active_sculpt_mesh = manager.pose_controller.active_sculpt_mesh
        if not active_sculpt_mesh:
            OpenMaya.MGlobal.displayError("No Sculpting is active")
            return

        sculpt_mesh = active_sculpt_mesh[0]
        sculpt_mesh = Node(sculpt_mesh)
        if sculpt_mesh.type_name == 'transform':  # If get transform node as sculpt mesh, look for mesh
            shapes = sculpt_mesh.get_shapes()
            if shapes:
                sculpt_mesh = shapes[0]

        manager.pose_controller.save_sculpt_to_target(sculpt_mesh)
        # Remove points tweak from sculpt mesh
        for i in sculpt_mesh.pnts:
            i.remove()

        self.update_key_view()

    def do_target_enable(self):
        """
        Enable current target sculpt.
        """
        pose = self.get_active_pose()
        if not pose:
            return
        weight = pose.weight
        target = pose.get_target(weight=weight)
        if target:
            target.enable = True
            self.update_key_view()
        else:
            cmds.confirmDialog(title='Error',
                               message="Can't find the delta pose at current weight!")

    def do_target_disable(self):
        """
        Disable current target sculpt.
        """
        pose = self.get_active_pose()
        if not pose:
            return
        weight = pose.weight
        target = pose.get_target(weight=weight)
        if target:
            target.enable = False
            self.update_key_view()
        else:
            cmds.confirmDialog(title='Error',
                               message="Can't find the delta pose at current weight!")

    def do_target_mirror(self):
        """
        Mirror the target model.
        """
        pose = self.get_active_pose()
        weight = pose.weight
        target = pose.get_target(weight=weight)
        if target:
            confirm_info = cmds.confirmDialog(
                title='Mirror the target!',
                message='Are you sure to mirror the target'
                        ' vertex position? Half side of geometry changing will lost!',
                button=['Left To Right', 'Right To Left', 'Cancel'],
                defaultButton='Left To Right',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            if confirm_info == "Left To Right":
                target.mirror(source=Symmetry.LEFT)
            if confirm_info == "Right To Left":
                target.mirror(source=Symmetry.RIGHT)

        else:
            cmds.confirmDialog(title='Error',
                               message="Can't find the delta pose at current weight!")

    def do_target_delete(self):
        """
        Action callback to remove the target at the active pose.
        """
        pose = self.get_active_pose()
        weight = pose.weight/10.0
        if pose.get_target(weight=weight):
            answer = QtWidgets.QMessageBox.question(
                self,
                "Remove the target!",
                'Are you sure to remove the target '
                'at current weight? The action is undoable!')
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                manager.pose_controller.delete_target(pose, weight)
                self.update_key_view()
                manager.Pose_Model.refresh_pose(pose)
        else:
            QtWidgets.QMessageBox.warning(
                self,
                'Warning',
                "Can't find the delta pose at current weight!"
            )
