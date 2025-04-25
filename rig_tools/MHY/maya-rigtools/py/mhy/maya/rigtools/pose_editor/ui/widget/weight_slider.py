"""
The action buttons collection for the pose.
"""
import math
from PySide2 import QtWidgets, QtCore, QtGui

from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.ui.widget.slider_widget import SliderWidget
import mhy.maya.rigtools.pose_editor.ui.manager as manager
from mhy.qt.core.utils import get_icon


class Slider(QtWidgets.QWidget):
    """
    The action buttons collection for the pose.
    """

    add_icon = get_icon('add.png', QtGui.QColor(179, 226, 131))
    remove_icon = get_icon('delete.png', QtGui.QColor(233, 148, 151))
    edit_icon = get_icon('edit_mode.png', QtGui.QColor(232, 228, 110))
    reset_icon = get_icon('cancel.png', QtGui.QColor(243, 197, 131))

    def __init__(self, parent):
        super(Slider, self).__init__(parent=parent)
        self.keys_group_widget = QtWidgets.QGroupBox("Weights:     CTRL+LMB to delete the key.")
        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.addWidget(self.keys_group_widget)
        self.weight_buttons = dict()
        self._init_ui()
        self.setMinimumHeight(140)
        SignalManager.pose_changed_signal.connect(self.update_key_view)

    def update_widgets(self, pose=None, value=None):
        """
        Update key button highlight based on current pose weight value.

        Args:
            pose(Pose):
            value(float):

        Returns:

        """
        if not manager.pose_controller:
            return
        active_pose = manager.pose_controller.active_pose
        if pose is None:
            pose = active_pose
        if value is None:
            value = pose.weight

        for weight, button in self.weight_buttons.items():
            # restore to default first.
            button.setStyleSheet("QPushButton {}")
            style = "border-radius: 8px;"
            if pose.has_target(weight/10.0):
                style += "font-weight: bold; background-color: #73a341;"
            else:
                style += "background-color: gray;"
            if weight == value:
                style += "border: 2px solid white;"

            button.setStyleSheet("QPushButton {{{0}}}".format(style))
            button.update()

        current_weight_is_key = pose.has_weight_key(value)

        if value != 0.0 and not current_weight_is_key:
            self.__slider_add_key_button.setIcon(Slider.add_icon)
            self.__slider_add_key_button.setToolTip("Add a new key at current weight")
        else:
            self.__slider_add_key_button.setIcon(Slider.edit_icon)
            self.__slider_add_key_button.setToolTip("Edit the key at current weight")

    def _init_ui(self):
        """
        initialize the children widgets.
        """
        v_layout = QtWidgets.QVBoxLayout(self)
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

        self.__slider_add_key_button = QtWidgets.QPushButton(Slider.add_icon, '', self)
        self.__slider_add_key_button.setToolTip("Add a new key at current weight")
        self.__slider_add_key_button.clicked.connect(self.do_key_current_pose)
        self.__slider_add_key_button.setFixedSize(37, 37)
        slider_layout.addWidget(self.__slider_add_key_button)
        button = QtWidgets.QPushButton(Slider.reset_icon, '', self)
        button.setToolTip("Reset active pose")
        button.setFixedSize(37, 37)
        button.clicked.connect(lambda: self.do_reset_pose(True))
        slider_layout.addWidget(button)
        self.weight_buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        slider_layout.addWidget(self.slider_widget)

        self.update_key_view()

    @staticmethod
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
        if not widget.delegate:
            return
        widget.delegate.weight = widget.value
        SignalManager.update_influence_attribute_signal.emit(widget.delegate)
        self.update_widgets(widget.delegate)

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
                manager.pose_controller.delete_key(pose=pose, weight=weight)
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

    def update_key_view(self, pose=None, weight=None):
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
        if weight is None:
            weight = pose.weight
        self.slider_widget.delegate = pose
        self.slider_widget.value = weight

        for key in keys:
            button = QtWidgets.QPushButton(self)
            button.setFixedSize(40, 40)
            display_key = math.floor(key * 100) / 100.0  # display only 2 decimals but not round it
            button.setText(str(display_key))
            button.clicked.connect(
                self.get_weight_button_pressed_callback(key))
            self.weight_buttons[key] = button
            self.weight_buttons_layout.addWidget(button)
        self.update_widgets(pose)
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
        pose.refresh_cache(False)
        self.update_key_view()
        self.update_widgets(pose)

    def do_reset_pose(self, prompt=True):
        """
        Clear all the data in the active pose
        Args:
            prompt(bool): If prompt a dialog to confirm action

        """
        pose = self.get_active_pose()
        if not pose:
            return
        if prompt:
            answer = QtWidgets.QMessageBox.question(
                self,
                'Delete all pose keys!',
                'Are you sure to delete all the keys of the pose:{}?'.format(pose.name),
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        manager.pose_controller.reset_pose(pose.name, remove_influence=False)

        pose.refresh_cache(False)
        # Trigger other widgets to update
        SignalManager.influence_update.emit()
        manager.Pose_Model.refresh_pose(pose)
        SignalManager.update_influence_attribute_signal.emit(pose)
        self.update_key_view(pose)
