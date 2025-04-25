from PySide2 import QtWidgets, QtCore
import mhy.maya.animtools.picker_manager.ui.attribute_widget as paw
from mhy.maya.animtools.picker_manager.node.viewport_picker import ViewportPicker


class PickerPropertyWidget(QtWidgets.QWidget):
    """
    This widget controls the property of the picker items
    """
    attribute_changed_signal = QtCore.Signal(tuple)
    picker_movable = False

    def __init__(self, parent=None):
        super(PickerPropertyWidget, self).__init__(parent=parent)
        self.items = None
        scroll = QtWidgets.QScrollArea(self)
        main_widget = QtWidgets.QWidget(self)
        self.property_widgets_layout = QtWidgets.QVBoxLayout()
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self.move_able_check = QtWidgets.QCheckBox("Movable")
        self.move_able_check.setChecked(self.picker_movable)
        main_layout.addWidget(self.move_able_check)

        self.picker_property_widgets = list()
        self.add_property_widgets()
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.property_widgets_layout.addSpacerItem(spacer)
        main_widget.setLayout(self.property_widgets_layout)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(main_widget)
        main_layout.addWidget(scroll)
        self.move_able_check.stateChanged.connect(self.update_movable)

    def update_movable(self, state):
        """
        Callback when movable checkbox state changed to change the movable states of items in the
        view

        Args:
            state:

        Returns:

        """
        self.picker_movable = state
        if self.items:
            for item in self.items:
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, enabled=state)

    def add_property_widgets(self):
        ui_type = ViewportPicker.ui_type
        ui_type_names = [i for i in ui_type if i != 'image']
        option_string = ":".join(ui_type_names)
        ui_type_widget = paw.EnumAttributeEditor([], 'uiType', option_string)
        self.property_widgets_layout.addWidget(ui_type_widget)
        self.picker_property_widgets.append(ui_type_widget)

        for col_att in ['color', 'highLightColor']:
            color_widget = paw.ColorAttributeEditor([], col_att, parent=self)
            self.property_widgets_layout.addWidget(color_widget)
            self.picker_property_widgets.append(color_widget)

        for attr in ['radius', 'width', 'height']:
            widget = paw.NumericAttrEditor([], attr, parent=self, default_value=20)
            self.property_widgets_layout.addWidget(widget)
            self.picker_property_widgets.append(widget)

        widget = paw.NumericAttrEditor([], 'alpha', parent=self, default_value=1.0)
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        widget = paw.NumericAttrEditor([], 'rotate', parent=self, default_value=0.0, default_min=0.0, default_max=360)
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        widget = paw.NumericAttrEditor([], 'lineWidth', parent=self, default_value=2.0)
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        for widget in self.picker_property_widgets:
            widget.attribute_changed_signal.connect(self.attribute_changed_cb)

    def attribute_changed_cb(self, data):
        self.attribute_changed_signal.emit(data)

    def set_items(self, items):
        """
        Set the target items of this property widget. The target items will be updated
        when the property widgets change values
        Args:
            items(list): A list of items

        """
        self.items = items
        for item in items:
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, enabled=self.picker_movable)
        for widget in self.picker_property_widgets:
            widget.update_items(items)
