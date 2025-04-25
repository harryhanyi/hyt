"""
This module provides attribute editor widgets for different type of maya attributes

"""
import logging
import os
import json
import six

from PySide2 import QtGui, QtWidgets, QtCore
from mhy.qt.icon_lib.api import get_icon
from mhy.protostar.ui.widget.promote_dialog import PromptDialog
from mhy.protostar.ui.widget.expression_dialog import ExpressionDialog
from mhy.protostar.ui.config import Config


logger = logging.getLogger(__name__)

__all__ = ['EnumAttributeEditor', 'NullAttributeEditor', 'FloatAttrEditor',
           'IntegerAttrEditor', 'BooleanAttributeEditor',
           'ColorAttributeEditor', 'FileAttrEditor', 'DirAttrEditor',
           'VectorAttributeEditor', 'Vector2AttributeEditor',
           'Vector3AttributeEditor']


class AttributeEditorBase(QtCore.QObject):
    attribute_changed_signal = QtCore.Signal(list)

    def __init__(self, parameters, attr_name, draggable=False, parent=None):
        super(AttributeEditorBase, self).__init__(parent=parent)
        self.parameters = parameters
        self.attribute_name = attr_name
        self.draggable = draggable
        self._init_ui()
        if self.parameters and self.parameters[0].is_output:
            self.set_editable(False)

    def set_editable(self, state):
        """
        Override this method in child class to disable edition for
        output parameters
        Args:
            state(bool):

        """
        pass

    def show_context_menu(self):
        menu = QtWidgets.QMenu(self.name_widget)
        expression_action = QtWidgets.QAction(
            "Edit Expression")
        expression_action.triggered.connect(self.edit_expression_cb)
        menu.addAction(expression_action)

        if len(self.parameters) == 1:
            prompt_action = QtWidgets.QAction("Promote")
            prompt_action.triggered.connect(self.prompt_cb)
            menu.addAction(prompt_action)
        menu.exec_(QtGui.QCursor.pos())

    def _init_ui(self):
        """
        Virtual method for child class to implement
        Returns:

        """
        self.name_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        self.name_widget.setLayout(layout)

        self.status_label = QtWidgets.QLabel(self.name_widget)
        self.status_label.setFixedSize(12, 12)

        if self.draggable:
            attribute_label = DragAbleLabel(
                self.attribute_name,
                self.name_widget)
        else:
            attribute_label = QtWidgets.QLabel(
                self.attribute_name,
                self.name_widget)

        layout.addWidget(self.status_label)
        layout.addWidget(attribute_label)

        self.detailed_widget = QtWidgets.QWidget()
        detailed_layout = QtWidgets.QHBoxLayout()
        self.detailed_widget.setLayout(detailed_layout)
        self.content_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.content_widget.setLayout(self.main_layout)
        self.expression_line = QtWidgets.QLabel(self.detailed_widget)
        self.expression_line.hide()
        detailed_layout.addWidget(self.expression_line)
        detailed_layout.addWidget(self.content_widget)

        self.name_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.name_widget.customContextMenuRequested.connect(
            self.show_context_menu
        )

        self.content_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.content_widget.customContextMenuRequested.connect(
            self.show_context_menu
        )

    def init_parameters(self, parameters):
        """
        Virtual method that could be override in child classes.
        Called to refresh the ui states reflecting the states of
        given parameters
        Args:
            parameters(list):  A list of base_parameter instances

        """
        self.parameters = parameters
        self.load_value_from_parameters(parameters)

    def update_ui_for_value_change(self, value):
        """
        This is a virtual method to be override in child class.
        This method is called to update the status of the ui based
        on current value of the parameter.
        Usually the signal of the widget need to be blocked to avoid cycle
        updates.
        Args:
            value: Value type varies

        """
        pass

    def load_value_from_parameters(self, params):
        out_value = None
        exception = None
        try:
            for param in params:
                out_value = param.value
                break
            self.update_ui_for_value_change(out_value)
        except BaseException as e:
            logging.warning(str(e))
            exception = str(e)
        finally:
            self.refresh_status_indicator(params, exception=exception)

    def refresh_status_indicator(self, params, exception=None):
        """
        Check and refresh the status indicator. Draw indicator
        if the parameter has input connection, is not editable or is dynamic
        attribute
        Args:
            params(base_parameter): A parameter instance


        """
        if not params:
            return
        is_dynamic = False
        has_expression = False
        editable = True

        for param in params:
            if param.is_dynamic:
                is_dynamic = True
            if params[0].script:
                has_expression = True
            if not param.editable:
                editable = False
                break

        state_str = ""
        expression_str = ""
        if exception is not None:
            self.status_label.setStyleSheet(
                "background-color: rgb({r}, {g}, {b});".format(
                    r=Config.Color.title_color_failed[0],
                    g=Config.Color.title_color_failed[1],
                    b=Config.Color.title_color_failed[2]
                )
            )
            self.expression_line.setStyleSheet(
                "color: rgb({r}, {g}, {b});".format(
                    r=Config.Color.title_color_failed[0],
                    g=Config.Color.title_color_failed[1],
                    b=Config.Color.title_color_failed[2]
                )
            )
            self.expression_line.setText(str(exception))
            self.toggle_expression_layout(True)

        elif has_expression:
            script_code = params[0].script.code

            if params[0].has_direct_input:
                self.status_label.setStyleSheet(
                    "background-color: rgb({r}, {g}, {b});".format(
                        r=Config.Color.direct_connected_param[0],
                        g=Config.Color.direct_connected_param[1],
                        b=Config.Color.direct_connected_param[2]
                    )
                )
                self.expression_line.setStyleSheet(
                    "color: rgb({r}, {g}, {b});".format(
                        r=Config.Color.direct_connected_param[0],
                        g=Config.Color.direct_connected_param[1],
                        b=Config.Color.direct_connected_param[2]
                    )
                )
                state_str = "connected"
            else:
                self.status_label.setStyleSheet(
                    "background-color: rgb({r}, {g}, {b});".format(
                        r=Config.Color.expression_override_param[0],
                        g=Config.Color.expression_override_param[1],
                        b=Config.Color.expression_override_param[2]
                    )
                )
                self.expression_line.setStyleSheet(
                    "color: rgb({r}, {g}, {b});".format(
                        r=Config.Color.expression_override_param[0],
                        g=Config.Color.expression_override_param[1],
                        b=Config.Color.expression_override_param[2]
                    )
                )
                state_str = 'expression'
                expression_str = script_code

            self.toggle_expression_layout(True)
            scrip_review = script_code
            # Remove whitespace from end for reviewing
            scrip_review = scrip_review.rstrip()
            if len(scrip_review) > 30:
                scrip_review = scrip_review[0:30] + '...'

            self.expression_line.setText(scrip_review)

        else:
            self.toggle_expression_layout(False)
            self.expression_line.setText("")

            if not editable:
                self.status_label.setStyleSheet("background-color: red;")
                state_str = "locked"
            elif is_dynamic:
                self.status_label.setStyleSheet(
                    "background: rgb({r}, {g}, {b});".format(
                        r=Config.Color.dynamic_param[0],
                        g=Config.Color.dynamic_param[1],
                        b=Config.Color.dynamic_param[2]
                    )
                )
                state_str = "dynamic"

        if state_str:
            tool_tip = "<p><b>[{}]</b>({})<p>".format(
                params[0].param_type,
                state_str)
        else:
            tool_tip = "<p><b>[{}]</b><p>".format(
                params[0].param_type)

        if params[0].doc:
            tool_tip = tool_tip + '<p style="white-space: pre">{}</p>' \
                                  ''.format(params[0].doc)

        if expression_str:
            tool_tip = tool_tip +\
                       '<p style="color:orange;">{}</p>'.format(
                           expression_str
                       )

        self.content_widget.setToolTip(tool_tip)
        self.name_widget.setToolTip(tool_tip)

    def toggle_expression_layout(self, stat):
        if stat:
            self.expression_line.show()
            self.content_widget.hide()
        else:
            self.expression_line.hide()
            self.content_widget.show()

    def parameter_value_changed(self, value):
        """
        This method is called to change the value for internal parameter
        instance.

        Args:
            value: Value type varies from parameter to parameter

        """
        for param in self.parameters:
            param.value = value

        self.attribute_changed_signal.emit(self.parameters)

    def prompt_cb(self):
        """
        Called to prompt a dialog for promoting parameter to owner graph

        """
        param = self.parameters[0]
        owner = param.owner
        if owner:
            graph = owner.graph
            if graph:
                dialog = PromptDialog(
                    parameter=param,
                    graph=graph,
                    parent=self.name_widget)
                dialog.exec_()

    def edit_expression_cb(self):
        """
        Launch a dialog for user to modify the expression of this parameter

        """
        param = self.parameters[0]
        dialog = ExpressionDialog(
            parameter=param,
            parent=self.name_widget)
        dialog.exec_()


class NullAttributeEditor(AttributeEditorBase):
    """
    This is the placeholder widget for not defined attribute type
    """
    def _init_ui(self):
        super(NullAttributeEditor, self)._init_ui()
        line = QtWidgets.QFrame(self.content_widget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setToolTip(str(self.parameters[0].value))
        self.main_layout.addWidget(line)


class BooleanAttributeEditor(AttributeEditorBase):
    """

    Boolean typed attribute editor widget

    """
    def _init_ui(self):
        super(BooleanAttributeEditor, self)._init_ui()
        self.check_box = QtWidgets.QCheckBox(self.content_widget)
        self.main_layout.addWidget(self.check_box)
        self.check_box.stateChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        self.check_box.setEnabled(state)

    def update_ui_for_value_change(self, out_value):
        self.check_box.blockSignals(True)
        self.check_box.setChecked(bool(out_value))
        self.check_box.blockSignals(False)


class VectorAttributeEditor(AttributeEditorBase):
    """

    Boolean typed attribute editor widget

    """
    _LEN = 3

    def _init_ui(self):
        super(VectorAttributeEditor, self)._init_ui()
        self.spin_box_list = list()
        for i in range(self._LEN):
            box = QtWidgets.QDoubleSpinBox(self.content_widget)
            box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.spin_box_list.append(box)
            self.main_layout.addWidget(box)
            box.valueChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        for spin in self.spin_box_list:
            spin.setReadOnly(not state)

    def parameter_value_changed(self):
        value = [i.value() for i in self.spin_box_list]
        for param in self.parameters:
            param.value = value

        self.attribute_changed_signal.emit(self.parameters)

    def update_ui_for_value_change(self, value):
        for i in range(self._LEN):
            self.spin_box_list[i].blockSignals(True)
            self.spin_box_list[i].setValue(value[i])
            self.spin_box_list[i].blockSignals(False)


class Vector2AttributeEditor(VectorAttributeEditor):
    """

    Boolean typed attribute editor widget

    """
    _LEN = 2


class Vector3AttributeEditor(VectorAttributeEditor):
    """

    Boolean typed attribute editor widget

    """
    _LEN = 3


class StringAttributeEditor(AttributeEditorBase):
    """

    Boolean typed attribute editor widget

    """
    def _init_ui(self):
        super(StringAttributeEditor, self)._init_ui()
        self.line = QtWidgets.QLineEdit(self.content_widget)
        self.main_layout.addWidget(self.line)
        self.line.textChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        self.line.setReadOnly(not state)

    def update_ui_for_value_change(self, value):
        self.line.blockSignals(True)
        self.line.setText(value)
        self.line.blockSignals(False)


class EnumAttributeEditor(AttributeEditorBase):
    """

    Enum typed attribute editor widget

    """
    def _init_ui(self):
        super(EnumAttributeEditor, self)._init_ui()
        self.combo_box = QtWidgets.QComboBox(self.content_widget)
        self.main_layout.addWidget(self.combo_box)
        self.combo_box.currentTextChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        self.combo_box.setEnabled(state)

    def load_value_from_parameters(self, params):
        out_value = None
        enum_list = []
        for param in params:
            out_value = param.value
            enum_list = param.items

        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        self.combo_box.addItems(enum_list)
        self.combo_box.blockSignals(False)

        self.update_ui_for_value_change(out_value)
        self.refresh_status_indicator(params)

    def update_ui_for_value_change(self, value):
        self.combo_box.blockSignals(True)
        self.combo_box.setCurrentIndex(value)
        self.combo_box.blockSignals(False)


class FileAttrEditor(AttributeEditorBase):
    def __init__(self, parameters, attr_name, draggable=False, parent=None):
        self.extensions = None
        super(FileAttrEditor, self).__init__(
            parameters,
            attr_name,
            draggable,
            parent=parent)

    def set_editable(self, state):
        self.file_path_edit.setReadOnly(not state)
        self.bg_image_path_pb.setEnabled(state)

    def _init_ui(self):
        super(FileAttrEditor, self)._init_ui()
        self.file_path_edit = QtWidgets.QLineEdit(self.content_widget)
        self.file_path_edit.setPlaceholderText("The file path")
        self.bg_image_path_pb = QtWidgets.QPushButton()
        icon = get_icon(
            sub_dir='/WINDOWS10/text/svg/search.svg',
            color=(178, 233, 235))
        self.bg_image_path_pb.setIcon(icon)
        self.bg_image_path_pb.setFixedSize(32, 32)
        self.main_layout.addWidget(self.file_path_edit)
        self.main_layout.addWidget(self.bg_image_path_pb)

        self.file_path_edit.textChanged.connect(self.parameter_value_changed)
        self.bg_image_path_pb.clicked.connect(self.browse_path_cb)

    def update_ui_for_value_change(self, value):
        self.file_path_edit.blockSignals(True)
        value = value.replace('\\', '/')
        self.file_path_edit.setText(value)
        self.file_path_edit.blockSignals(False)

    def load_value_from_parameters(self, params):
        extensions = list()
        for param in params:
            if param.param_type == "file":
                extensions.extend(param.ext)
        self.extensions = list(set(extensions))
        super(FileAttrEditor, self).load_value_from_parameters(params)

    def browse_path_cb(self):
        """
        Called when image path push button clicked. It will launch a file
        dialog that user can specify an image as the back ground of this
        container

        """
        file_dialog = QtWidgets.QFileDialog(self.content_widget, "Select File")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        if self.extensions:
            extension_str = " ".join(["*.{}".format(ext) for
                                      ext in self.extensions])
            file_dialog.setNameFilters(["Data files ({})".
                                       format(extension_str)])

        current_txt = self.file_path_edit.text()
        if os.path.isfile(current_txt):
            current_dir = os.path.dirname(current_txt)
            file_dialog.setDirectory(current_dir)
        result = file_dialog.exec_()
        if result:
            image_path = file_dialog.selectedFiles()[0]
            image_path = image_path.replace('\\', '/')
        else:
            return
        self.file_path_edit.setText(image_path)


class DirAttrEditor(FileAttrEditor):
    def _init_ui(self):
        super(DirAttrEditor, self)._init_ui()
        self.file_path_edit.setPlaceholderText("The directory path")

    def browse_path_cb(self):
        """
        Called directory browser push button clicked. It will launch a file
        dialog that user can specify an image as the back ground of this
        container

        """
        result = QtWidgets.QFileDialog.getExistingDirectory(
            self.content_widget,
            "Open a folder",
            self.file_path_edit.text()
        )
        if result:
            image_path = result.replace('\\', '/')
        else:
            return
        self.file_path_edit.setText(image_path)


class ColorAttributeEditor(AttributeEditorBase):
    """
    Color typed attribute editor widget
    """

    def __init__(self, parameters, attr_name, draggable=False, parent=None):
        super(ColorAttributeEditor, self).__init__(
            parameters=parameters,
            attr_name=attr_name,
            draggable=draggable,
            parent=parent
        )
        self.__color = QtGui.QColor()

    def _init_ui(self):
        super(ColorAttributeEditor, self)._init_ui()
        self.color_pb = QtWidgets.QPushButton(parent=self.content_widget)
        self.color_pb.setFixedSize(27, 27)
        self.main_layout.addWidget(self.color_pb)
        self.setLayout(self.main_layout)
        self.color_pb.clicked.connect(self.pick_color)

    def set_editable(self, state):
        self.color_pb.setEnabled(state)

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
                    value[0],
                    value[1],
                    value[2]))

            self.__color = value

    def pick_color(self):
        """
        Launch a color picker dialog.
        Returns:

        """
        dialog = QtWidgets.QColorDialog(parent=self.content_widget)
        if isinstance(self.color, (list, tuple)):
            color = QtGui.QColor(*self.color)
        else:
            color = self.color
        dialog.setCurrentColor(color)
        result = dialog.exec_()
        if result:
            color = dialog.selectedColor()
            self.color = [color.red(), color.green(), color.blue()]
            self.parameter_value_changed(self.color)

    def update_ui_for_value_change(self, value):
        self.color = value


class FloatAttrEditor(AttributeEditorBase):
    def _init_ui(self):
        super(FloatAttrEditor, self)._init_ui()
        self.value_spin = QtWidgets.QDoubleSpinBox(self.content_widget)
        self.value_spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.value_spin.setSingleStep(0.001)
        self.main_layout.addWidget(self.value_spin)
        self.value_spin.valueChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        self.value_spin.setReadOnly(not state)

    def update_ui_for_value_change(self, value):
        self.value_spin.blockSignals(True)
        self.value_spin.setValue(value)
        self.value_spin.blockSignals(False)


class IntegerAttrEditor(AttributeEditorBase):
    def _init_ui(self):
        super(IntegerAttrEditor, self)._init_ui()
        self.value_spin = QtWidgets.QSpinBox(self.content_widget)
        self.value_spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.value_spin.setSingleStep(1)

        self.main_layout.addWidget(self.value_spin)
        self.value_spin.valueChanged.connect(self.parameter_value_changed)

    def set_editable(self, state):
        self.value_spin.setReadOnly(not state)

    def update_ui_for_value_change(self, value):
        self.value_spin.blockSignals(True)
        self.value_spin.setValue(value)
        self.value_spin.blockSignals(False)


class ListAttrEditor(AttributeEditorBase):
    def _init_ui(self):
        super(ListAttrEditor, self)._init_ui()
        self.list_editor = QtWidgets.QLineEdit(self.content_widget)
        self.current_value = []
        self.main_layout.addWidget(self.list_editor)

        self.list_editor.editingFinished.connect(self.update_list_value)

    def update_list_value(self):
        txt = self.list_editor.text()
        self.list_editor.blockSignals(True)
        txt = txt.replace("'", '"')
        try:
            new_list = json.loads(txt)
            if self.validate_list(new_list):
                self.current_value = new_list
                self.parameter_value_changed(self.current_value)
                j_str = json.dumps(self.current_value)
                self.list_editor.setText(j_str)
            else:
                logger.error("{} is not a valid list".format(new_list))
        except Exception as e:
            logger.error(str(e))
            j_str = json.dumps(self.current_value)
            self.list_editor.setText(j_str)
        finally:
            self.list_editor.blockSignals(False)

    def set_editable(self, state):
        self.list_editor.setReadOnly(not state)

    def validate_list(self, val):
        if not isinstance(val, list):
            return False
        for i in val:
            if not isinstance(i, (six.string_types, int, float)):
                return False
        return True

    def update_ui_for_value_change(self, value):
        if not self.validate_list(value):
            self.list_editor.setText("")
            return

        self.list_editor.blockSignals(True)
        try:
            j_str = json.dumps(value)
            self.current_value = value
            self.list_editor.setText(j_str)
        except Exception as e:
            logger.error(str(e))
        finally:
            self.list_editor.blockSignals(False)


parameter_type_widget_map = {
    'pyobject': NullAttributeEditor,
    'message': None,
    'bool': BooleanAttributeEditor,
    'vector2': Vector2AttributeEditor,
    'vector3': Vector3AttributeEditor,
    'rgb': ColorAttributeEditor,
    'int': IntegerAttrEditor,
    'float': FloatAttrEditor,
    'enum': EnumAttributeEditor,
    'str': StringAttributeEditor,
    'dir': DirAttrEditor,
    'file': FileAttrEditor,
    'callback': None,
    'list': ListAttrEditor,
    'iter': None,
    'dict': None
}


class DragAbleLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(DragAbleLabel, self).__init__(*args, **kwargs)
        self.drag_start_position = None
        self.selected_param_name = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.selected_param_name = self.text()
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not event.buttons() & QtCore.Qt.LeftButton:
            return

        if not self.drag_start_position or \
                (event.pos() - self.drag_start_position).manhattanLength() \
                < QtWidgets.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()

        if self.selected_param_name:
            mime_data.setText(self.selected_param_name)
        else:
            mime_data.setText("")

        drag.setMimeData(mime_data)
        drag.exec_(QtCore.Qt.MoveAction)
