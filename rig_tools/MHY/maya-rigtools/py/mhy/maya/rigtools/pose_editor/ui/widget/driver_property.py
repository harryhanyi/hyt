"""
Pose driver property setting dialog
"""

from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from mhy.maya.nodezoo.attribute import Attribute
import mhy.maya.rigtools.pose_editor.ui.widget.set_driven_key_slider as sds


class DriverPropertyWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DriverPropertyWidget, self).__init__(parent=parent)
        self.driver_obj = None
        layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle('Driver Property')
        self.setLayout(layout)
        self.pose = None
        driver_attr_group = QtWidgets.QGroupBox("Driver: ")
        driver_attr_layout = QtWidgets.QVBoxLayout(driver_attr_group)
        driver_attr_group.setLayout(driver_attr_layout)
        self.driver_node_loader = QtWidgets.QPushButton(self)
        button_group = QtWidgets.QButtonGroup()
        self.keyable_radio = QtWidgets.QRadioButton('keyable', self)
        self.connectable_radio = QtWidgets.QRadioButton('connectable', self)
        self.keyable_radio.setChecked(True)
        button_group.addButton(self.keyable_radio)
        button_group.addButton(self.connectable_radio)

        radio_widget = QtWidgets.QWidget(self)
        radio_layout = QtWidgets.QHBoxLayout()
        radio_widget.setLayout(radio_layout)
        radio_layout.addWidget(self.keyable_radio)
        radio_layout.addWidget(self.connectable_radio)

        self.attr_list = QtWidgets.QListWidget(self)

        driver_layout = QtWidgets.QHBoxLayout(self)
        driver_label = QtWidgets.QLabel("Driver:")
        driver_label.setFixedWidth(80)
        self.anim_curve_widget = sds.AnimCurveWidget(True, self)
        self.anim_curve_widget.set_range([0, 1])
        driver_layout.addWidget(driver_label)
        driver_layout.addWidget(self.anim_curve_widget)

        self.radio_box = QtWidgets.QRadioButton()

        driver_attr_layout.addWidget(self.driver_node_loader)
        driver_attr_layout.addWidget(radio_widget)
        driver_attr_layout.addWidget(self.attr_list)

        neutral_value_layout = QtWidgets.QGridLayout()
        neutral_value_label = QtWidgets.QLabel("Neutral Value:", self)
        self.neutral_value_spin = QtWidgets.QDoubleSpinBox(self)
        self.neutral_value_spin.setRange(-999, 999)
        neutral_value_layout.addWidget(neutral_value_label, 0, 0)
        neutral_value_layout.addWidget(self.neutral_value_spin, 0, 1)

        driven_range_layout = QtWidgets.QGridLayout(self)

        driven_value_label = QtWidgets.QLabel("Driven:", self)
        self.driven_value_spin = QtWidgets.QDoubleSpinBox(self)
        self.driven_value_spin.setRange(-999, 999)

        driven_range_layout.addWidget(driven_value_label, 0, 0)
        driven_range_layout.addWidget(self.driven_value_spin, 0, 1)

        key_button_layout = QtWidgets.QHBoxLayout(self)

        self.add_key_button = QtWidgets.QPushButton("Add Key")
        self.add_key_button.setDisabled(True)
        self.del_key_button = QtWidgets.QPushButton("Delete Key")
        self.del_key_button.setDisabled(True)

        key_button_layout.addWidget(self.add_key_button)
        key_button_layout.addWidget(self.del_key_button)

        button_layout = QtWidgets.QGridLayout(self)
        close_button = QtWidgets.QPushButton("Close")

        remove_driver = QtWidgets.QPushButton("Reset")
        button_layout.addWidget(remove_driver, 0, 0)
        button_layout.addWidget(close_button, 0, 1)
        remove_driver.clicked.connect(self.remove_driver_cb)
        close_button.clicked.connect(self.close)

        layout.addWidget(driver_attr_group)
        layout.addLayout(driver_layout)
        layout.addLayout(driven_range_layout)
        layout.addLayout(neutral_value_layout)
        layout.addLayout(key_button_layout)
        layout.addLayout(button_layout)

        sel_model = self.attr_list.selectionModel()
        self.driver_node_loader.clicked.connect(self.load_driver_object)
        self.add_key_button.clicked.connect(self.add_key_cb)
        self.del_key_button.clicked.connect(self.delete_key_cb)
        sel_model.selectionChanged.connect(self.selected_attr_changed_cb)
        self.anim_curve_widget.slider.selection_changed_sg.connect(self.selected_key_changed_cb)
        self.keyable_radio.toggled.connect(self.radio_state_changed_cb)
        self.connectable_radio.toggled.connect(self.radio_state_changed_cb)

    def init_widgets(self, pose):
        """
        Init widget stats based on a pose
        Args:
            pose(Pose): A pose instance

        """
        self.pose = pose
        driver_node = pose.get_driver_node()

        self.driver_node_loader.setText("Click to load driver object >>")
        self.driver_node_loader.setStyleSheet('QPushButton {color: lightGray;}')
        self.driven_value_spin.setValue(10)
        self.attr_list.clear()

        if driver_node:
            if driver_node.type_name.startswith('animCurve'):
                driver_attribute, default_value, extreme_value =\
                    pose.get_driver_range_from_anim_curve(driver_node)
                if driver_attribute:
                    attr = Attribute(driver_attribute)
                    node = attr.node
                    self.driver_node_loader.setText(node.name)
                    self.driver_node_loader.setText(node.name)
                    self.driver_node_loader.setStyleSheet('QPushButton {background-color: #466b59; color: white;}')
                    self.driven_value_spin.setValue(default_value)
                    # self.driven_value_spin.setValue(extreme_value)
                    self.set_driver_attr(node.name, attr.name)
                self.anim_curve_widget.set_internal_anim_curve(driver_node)
                return
        self.anim_curve_widget.set_internal_anim_curve(None)

    def selected_key_changed_cb(self, data):
        driver_node = self.pose.get_driver_node()
        if_select = data[0]
        if if_select:
            self.add_key_button.setText('Edit Key')
            self.del_key_button.setDisabled(False)
            if driver_node:
                if driver_node.type_name.startswith('animCurve'):
                    val = driver_node.find_closest_out_value(data[1])
                    self.driven_value_spin.setValue(val)
        else:
            self.add_key_button.setText('Add Key')
            self.del_key_button.setDisabled(True)

    def set_driver_attr(self, node, attribute):
        """
        Set the driver node and attribute so that attribute list will refresh to load
        all the available attributes
        Args:
            node(str): node name
            attribute(str): Attribute name


        """
        self.refresh_driver_node(node)
        for index in range(self.attr_list.count()):
            item = self.attr_list.item(index)
            if item.data(QtCore.Qt.DisplayRole) == attribute:
                self.attr_list.setCurrentItem(item)
                return

    def remove_driver_cb(self):
        """
        Called to remove the driver connection from this pose

        """
        input_attr = self.pose.input_attribute_full_name
        source = Attribute(input_attr).sourceWithConversion
        if source:
            source.disconnect(Attribute(input_attr))
            source_node = source.node
            if source_node.type_name.startswith('animCurve') or source_node.type_name == "unitConversion":
                cmds.delete(source_node.name)
        self.driver_obj = None
        self.init_widgets(self.pose)

    def load_driver_object(self):
        """
        Select node object from the current maya scene

        """
        if not self.driver_obj:
            sel = cmds.ls(selection=True)
            if len(sel) != 1:
                OpenMaya.MGlobal.displayError("Please only select on object as driver")
                return
            node = sel[0]
            self.refresh_driver_node(node)
        else:
            if self.driver_obj and cmds.objExists(self.driver_obj):
                cmds.select(self.driver_obj)

    def radio_state_changed_cb(self):
        self.refresh_driver_node(self.driver_obj)

    def refresh_driver_node(self, node):
        """
        Set the node object and refresh the attribute list
        Args:
            node(str): Node name

        """
        self.driver_obj = node
        self.driver_node_loader.setText(node)
        self.driver_node_loader.setStyleSheet('QPushButton {background-color: #466b59; color: white;}')
        self.attr_list.clear()
        if node and cmds.objExists(node):
            attrs = []
            if self.keyable_radio.isChecked():
                attrs = cmds.listAttr(node, keyable=True, multi=True) or []
            elif self.connectable_radio.isChecked():
                attrs = cmds.listAttr(node, connectable=True, multi=True) or []
            # Only support 1 level array attribute maximum
            for attr in attrs:
                if '.' in attr and '[' not in attr:
                    continue
                attr = Attribute('{}.{}'.format(node, attr))
                if not attr:
                    continue
                if attr.is_array:
                    for i in attr:
                        self.attr_list.addItem(i.name)
                else:
                    self.attr_list.addItem(attr.name)

    def selected_attr_changed_cb(self, selected, deselected):
        """

        Args:
            selected:
            deselected:

        Returns:

        """
        sel = self.attr_list.selectedItems()
        if sel:
            self.add_key_button.setEnabled(True)
        else:
            self.add_key_button.setEnabled(False)

    def add_key_cb(self):
        """
        When applied, check if need to override the set driven key node to a new range.

        """
        # So firstly we get the target attribute from the dialog
        node_name = self.driver_obj
        sel = self.attr_list.selectedItems()
        attr_name = sel[0].data(QtCore.Qt.DisplayRole)

        default_value_to_set = self.neutral_value_spin.value()
        driven_value_to_set = round(self.driven_value_spin.value(), 2)
        driver_value_to_set = round(self.anim_curve_widget.value, 2)

        target_attr_full_name = "{}.{}".format(node_name, attr_name)
        if not cmds.objExists(target_attr_full_name):
            OpenMaya.MGlobal.displayError('{} does not exists'.format(target_attr_full_name))
            return
        input_attr = self.pose.input_attribute_full_name

        # Check if the set driven key is already created. If
        # so, we only need to set the values. Otherwise, we make
        # set driven key
        driver_node = self.pose.get_driver_node()
        if driver_node:
            if driver_node.type_name.startswith('animCurve'):
                driver_attribute, _, _ =\
                    self.pose.get_driver_range_from_anim_curve(driver_node)
                source = Attribute(input_attr).sourceWithConversion
                if driver_attribute != target_attr_full_name:
                    if source:
                        source.disconnect(Attribute(input_attr))
                        source_node = source.node
                        if source_node.type_name.startswith('animCurve') or source_node.type_name == "unitConversion":
                            cmds.delete(source_node.name)

        current_value = cmds.getAttr(target_attr_full_name)
        # Trying to add neutral key
        cmds.setDrivenKeyframe(
            input_attr,
            currentDriver=target_attr_full_name,
            driverValue=default_value_to_set,
            value=0,
            inTangentType='linear',
            outTangentType='linear')

        cmds.setDrivenKeyframe(
            input_attr,
            currentDriver=target_attr_full_name,
            driverValue=driver_value_to_set,
            value=driven_value_to_set,
            inTangentType='linear',
            outTangentType='linear')
        cmds.setInfinity(
            attribute=input_attr,
            preInfinite='linear',
            postInfinite='linear')
        self.init_widgets(self.pose)
        self.anim_curve_widget.value = current_value

    def delete_key_cb(self):
        """
        Delete selected key
        Returns:

        """
        key = self.anim_curve_widget.selected_key()
        if key is not None:
            anim_curve = self.get_associated_anim_curve()
            if anim_curve:
                anim_curve.delete_key(key)
                self.del_key_button.setDisabled(True)
        self.init_widgets(self.pose)

    def get_associated_anim_curve(self):
        """
        Get the associated anim curve node as the driver of this pose
        Returns:
            nodezoo.AnimCurve
        """
        driver_node = self.pose.get_driver_node()
        if driver_node:
            if driver_node.type_name.startswith('animCurve'):
                return driver_node
