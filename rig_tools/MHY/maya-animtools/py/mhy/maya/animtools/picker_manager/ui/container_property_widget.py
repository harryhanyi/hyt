from mhy.maya.animtools.picker_manager.ui.picker_property_widget import PickerPropertyWidget
import mhy.maya.animtools.picker_manager.ui.attribute_widget as paw


class ContainerPropertyWidget(PickerPropertyWidget):
    def __init__(self, parent=None):
        super(ContainerPropertyWidget, self).__init__(parent=parent)

    def add_property_widgets(self):
        image_widget = paw.FileAttrEditor([], 'imagePath', parent=self)
        self.property_widgets_layout.addWidget(image_widget)
        self.picker_property_widgets.append(image_widget)

        widget = paw.NumericAttrEditor(
            [],
            'alpha',
            parent=self,
            default_value=1.0
        )
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        widget = paw.NumericAttrEditor(
            [],
            'width',
            parent=self,
            default_value=1000,
            default_min=200,
            default_max=1000
        )
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        widget = paw.NumericAttrEditor(
            [],
            'height',
            parent=self,
            default_value=1000,
            default_min=200,
            default_max=1000
        )
        self.property_widgets_layout.addWidget(widget)
        self.picker_property_widgets.append(widget)

        color_widget = paw.ColorAttributeEditor(
            [],
            'containerTextColor',
            parent=self)
        self.property_widgets_layout.addWidget(color_widget)
        self.picker_property_widgets.append(color_widget)

    def update_children_info(self, data):
        """
        Update the information in the container's chidlren information attribute
        Args:
            data:

        Returns:

        """
        if not data:
            return
        node, attr = data
        for item in self.items:
            container_node = item.node
            info = container_node.get_children_information()
            node_name = node.name.split(':')[0]
            info[node_name] = node.export()
            container_node.set_children_information(info)
