"""
This module provides attribute editor widgets for different type of maya attributes

"""
from PySide2 import QtWidgets, QtCore, QtGui
import mhy.maya.animtools.picker_manager.node.viewport_picker as vp
from mhy.qt.icon_lib.api import get_icon
import maya.cmds as cmds
import mhy.maya.utils as mutil
import logging

logger = logging.getLogger(__name__)


class AttributeEditorBase(QtWidgets.QWidget):
    attribute_changed_signal = QtCore.Signal(tuple)

    def __init__(self, items, attr_name, attr_changed_callback=None, parent=None):
        super(AttributeEditorBase, self).__init__(parent=parent)
        self.items = items
        self.nodes = list()
        self.attribute_name = attr_name
        self.attribute_changed_callback = attr_changed_callback

    def update_items(self, items):
        self.items = items
        self.update_nodes_from_items(items)

    def update_nodes_from_items(self, items):
        self.nodes = list()
        for item in items:
            if cmds.objExists(item.name):
                node = vp.ViewportPicker(item.name)
                self.nodes.append(node)

    @mutil.undoable
    def update_attribute_value(self, value):
        for item, node in zip(self.items, self.nodes):
            try:
                getattr(node, self.attribute_name).value = value
            except RuntimeError as e:
                logger.warning(str(e))
            item.refresh_state()
            self.attribute_changed_signal.emit((node, self.attribute_name))


class ColorAttributeEditor(AttributeEditorBase):
    """

    Color typed attribute editor widget

    """
    def __init__(self, items, attr_name, attr_changed_callback=None, parent=None):
        super(ColorAttributeEditor, self).__init__(
            items=items,
            attr_name=attr_name,
            attr_changed_callback=attr_changed_callback,
            parent=parent)
        self.__color = QtGui.QColor()
        main_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("{}: ".format(attr_name), parent=self)
        self.color_pb = QtWidgets.QPushButton(parent=self)
        self.color_pb.setFixedSize(27, 27)
        main_layout.addWidget(label)
        main_layout.addWidget(self.color_pb)
        self.setLayout(main_layout)
        self.color_pb.clicked.connect(self.pick_color)
        self.update_items(self.items)

    @property
    def color(self):
        return self.__color

    @color.setter
    def color(self, value):
        if value is None:
            self.color_pb.setStyleSheet("")
            self.__color = QtGui.QColor()
        else:
            self.color_pb.setStyleSheet(
                "QPushButton {{background-color: rgb({},{},{})}}".format(
                    value.red(),
                    value.green(),
                    value.blue()))

            self.__color = value

    def pick_color(self):
        """
        Launch a color picker dialog.
        Returns:

        """
        dialog = QtWidgets.QColorDialog()
        dialog.setCurrentColor(self.color)
        result = dialog.exec_()
        if result:
            color = dialog.selectedColor()
            self.color = color
            self.update_attribute_value(
                [self.color.red() / 255.0, self.color.green() / 255.0, self.color.blue() / 255.0])

    def update_items(self, items):
        super(ColorAttributeEditor, self).update_items(items)
        if self.nodes:
            node = self.nodes[-1]
            color = getattr(node, self.attribute_name).value
            color = [i*255 for i in color]
            self.color = QtGui.QColor(*color)
        else:
            self.color = None


class NumericAttrEditor(AttributeEditorBase):
    def __init__(self, items, attr_name, attr_changed_callback=None,
                 parent=None, default_value=0,
                 default_min=None, default_max=None):
        super(NumericAttrEditor, self).__init__(
            items=items,
            attr_name=attr_name,
            attr_changed_callback=attr_changed_callback,
            parent=parent)
        self.__hard_max_val = None
        self.__hard_min_val = None
        self.__default_value = default_value
        self.__default_min = default_min
        self.__default_max = default_max
        main_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("{}: ".format(attr_name), parent=self)
        self.value_spin = QtWidgets.QDoubleSpinBox()
        self.value_spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        self.value_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        main_layout.addWidget(label)
        main_layout.addWidget(self.value_spin)
        main_layout.addWidget(self.value_slider)
        self.setLayout(main_layout)

        if self.__default_max is not None:
            self.value_spin.setMaximum(self.__default_max)
            self.value_slider.setMaximum(self.__default_max*100.0)
        else:
            self.value_spin.setMaximum(99999)

        if self.__default_min is not None:
            self.value_spin.setMinimum(self.__default_min)
            self.value_slider.setMinimum(self.__default_min * 100.0)
        else:
            self.value_spin.setMinimum(-99999)

        self.value_slider.sliderPressed.connect(self.open_undo)
        self.value_slider.sliderReleased.connect(self.close_undo)
        self.value_slider.valueChanged.connect(self.__slider_updated_cb)
        self.value_spin.valueChanged.connect(self.__spin_updated_cb)
        self.update_items(self.items)
        self.value_spin.setValue(default_value)

    @staticmethod
    def open_undo():
        cmds.undoInfo(ock=True)

    @staticmethod
    def close_undo():
        cmds.undoInfo(cck=True)

    def __slider_updated_cb(self, value):
        """
        This is callback method called when the slider widget changes value.
        Notice: The slider value is scaled by 100 to support float value when
        it sync with QDoubleSpinBox
        Args:
            value(float): Slider value

        """
        round_value = round((value/100.0), 2)
        self.value_spin.blockSignals(True)
        self.value_spin.setValue(round_value)
        self.value_spin.blockSignals(False)
        self.update_attribute_value(round_value)

    def __spin_updated_cb(self, value):
        """
        This is callback method called when the QDoubleSpinBox widget changes value
        Args:
            value(float): spin box value

        """
        self.value_slider.blockSignals(True)
        if value > round(self.value_slider.maximum()/100, 2):
            if self.__hard_max_val is None:
                self.value_slider.setMaximum(100*value)
            else:
                value = self.__hard_max_val
                self.value_spin.setValue(value)

        elif value < round(self.value_slider.minimum()/100, 2):
            if self.__hard_min_val is None:
                self.value_slider.setMinimum(100*value)
            else:
                value = self.__hard_min_val
                self.value_spin.setValue(value)

        self.value_slider.setValue(value*100)
        self.value_slider.blockSignals(False)

        self.update_attribute_value(value)

    def update_items(self, items):
        super(NumericAttrEditor, self).update_items(items)
        max_values = [getattr(node, self.attribute_name).maximum_value for node in self.nodes]
        min_values = [getattr(node, self.attribute_name).minimum_value for node in self.nodes]
        max_values = [i for i in max_values if i is not None]
        min_values = [i for i in min_values if i is not None]

        if not max_values:
            if self.__default_max is None:
                max_val = 100
            else:
                max_val = self.__default_max

            self.__hard_max_val = None
        else:
            max_val = min(max_values)
            if self.__default_max is not None and self.__default_max < max_val:
                max_val = self.__default_max
            self.__hard_max_val = max_val

        if not min_values:
            if self.__default_min is None:
                min_val = -100
            else:
                min_val = self.__default_min
            self.__hard_min_val = None
        else:
            min_val = max(min_values)
            if self.__default_min is not None and self.__default_min > min_val:
                min_val = self.__default_min
            self.__hard_min_val = min_val

        # display current value as the last selection
        if self.nodes:
            val = getattr(self.nodes[-1], self.attribute_name).value
        else:
            val = self.__default_value

        self.value_spin.blockSignals(True)
        self.value_slider.blockSignals(True)

        slider_val = val*100
        if slider_val > max_val*100:
            self.value_slider.setMaximum(slider_val)
        else:
            self.value_slider.setMaximum(max_val*100)

        if slider_val < min_val*100:
            self.value_slider.setMinimum(slider_val)
        else:
            self.value_slider.setMinimum(min_val * 100.0)

        self.value_slider.setValue(val*100)
        self.value_spin.setValue(val)
        self.value_slider.blockSignals(False)
        self.value_spin.blockSignals(False)


class FileAttrEditor(AttributeEditorBase):
    def __init__(self,
                 items,
                 attr_name,
                 attr_changed_callback=None,
                 parent=None):
        super(FileAttrEditor, self).__init__(
            items=items,
            attr_name=attr_name,
            attr_changed_callback=attr_changed_callback,
            parent=parent)
        main_layout = QtWidgets.QHBoxLayout()
        bg_image_label = QtWidgets.QLabel("{}: ".format(attr_name))
        self.bg_image_path_edit = QtWidgets.QLineEdit()
        self.bg_image_path_edit.setPlaceholderText("The image file of container background")
        bg_image_path_pb = QtWidgets.QPushButton()
        icon = get_icon(sub_dir='/WINDOWS10/text/svg/search.svg', color=(178, 233, 235))
        bg_image_path_pb.setIcon(icon)
        bg_image_path_pb.setFixedSize(32, 32)
        main_layout.addWidget(bg_image_label)
        main_layout.addWidget(self.bg_image_path_edit)
        main_layout.addWidget(bg_image_path_pb)
        self.setLayout(main_layout)

        self.update_items(self.items)
        self.bg_image_path_edit.textChanged.connect(self.update_attribute_value)
        bg_image_path_pb.clicked.connect(self.browse_image_cb)

    def update_items(self, items):
        super(FileAttrEditor, self).update_items(items)
        if self.nodes:
            self.bg_image_path_edit.blockSignals(True)
            self.bg_image_path_edit.setText(getattr(self.nodes[-1], self.attribute_name).value)
            self.bg_image_path_edit.blockSignals(False)

    def update_attribute_value(self, value):
        # Support workspace relative path
        workspace_root = cmds.workspace(query=True, rootDirectory=True)
        value = value.replace('\\', '/')
        if value.startswith(workspace_root):
            value = value.replace(workspace_root, "")
        self.bg_image_path_edit.blockSignals(True)
        self.bg_image_path_edit.setText(value)
        self.bg_image_path_edit.blockSignals(False)
        super(FileAttrEditor, self).update_attribute_value(value)

    def browse_image_cb(self):
        """
        Called when image path push button clicked. It will launch a file dialog that user
        can specify an image as the back ground of this container

        """
        workspace_root = cmds.workspace(query=True, rootDirectory=True)
        file_dialog = QtWidgets.QFileDialog(self, "Select Image", workspace_root)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        file_dialog.setNameFilters(["Image files (*.png *.xpm *.jpg)"])
        result = file_dialog.exec_()
        if result:
            image_path = file_dialog.selectedFiles()[0]
            image_path = image_path.replace('\\', '/')
        else:
            return
        self.bg_image_path_edit.setText(image_path)


class EnumAttributeEditor(AttributeEditorBase):
    """

    Enum typed attribute editor widget

    """
    def __init__(self, items, attr_name, enum_name, attr_changed_callback=None, parent=None):
        super(EnumAttributeEditor, self).__init__(
            items=items,
            attr_name=attr_name,
            attr_changed_callback=attr_changed_callback,
            parent=parent)

        main_layout = QtWidgets.QHBoxLayout()
        self.combo_box = QtWidgets.QComboBox()
        self.__enums = enum_name.split(':')
        self.combo_box.addItems(self.__enums)
        label = QtWidgets.QLabel("{}: ".format(attr_name), parent=self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.combo_box)
        self.setLayout(main_layout)
        self.update_items(self.items)
        self.combo_box.currentTextChanged.connect(self.update_attribute_value)

    def update_items(self, items):
        """
        Update items
        Args:
            items(list): A list of PickerItem

        Returns:

        """
        super(EnumAttributeEditor, self).update_items(items)
        self.combo_box.blockSignals(True)
        if self.nodes:
            enum_value = getattr(self.nodes[-1], self.attribute_name).enum_value
            self.combo_box.setCurrentText(enum_value)
        else:
            self.combo_box.setCurrentIndex(0)
        self.combo_box.blockSignals(False)


class BooleanAttributeEditor(AttributeEditorBase):
    """

    Enum typed attribute editor widget

    """
    def __init__(self, items, attr_name, attr_changed_callback=None, parent=None):
        super(BooleanAttributeEditor, self).__init__(
            items=items,
            attr_name=attr_name,
            attr_changed_callback=attr_changed_callback,
            parent=parent)

        main_layout = QtWidgets.QHBoxLayout()
        self.check_box = QtWidgets.QCheckBox(attr_name, self)
        main_layout.addWidget(self.check_box)
        self.setLayout(main_layout)
        self.update_items(self.items)
        self.check_box.stateChanged.connect(self.update_attribute_value)

    def update_items(self, items):
        """
        Update items
        Args:
            items(list): A list of PickerItem

        Returns:

        """
        super(BooleanAttributeEditor, self).update_items(items)
        self.check_box.blockSignals(True)
        if self.nodes:
            check_state_value = getattr(self.nodes[-1], self.attribute_name).value
            self.check_box.setChecked(bool(check_state_value))
        else:
            self.check_box.setChecked(True)
        self.check_box.blockSignals(False)

    @mutil.undoable
    def update_attribute_value(self, value):
        state = self.check_box.isChecked()
        for item, node in zip(self.items, self.nodes):
            try:
                getattr(node, self.attribute_name).value = state
            except RuntimeError as e:
                logger.warning(str(e))
            item.refresh_state()
            self.attribute_changed_signal.emit((node, self.attribute_name))
