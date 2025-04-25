"""
This modules contains api for DagNode
"""
from maya import cmds, OpenMaya, OpenMayaUI
import six
import json
import os
from mhy.maya.nodezoo.node import Node, DagNode, Transform


def _get_all_picker_shapes():
    """
    This method get the shape names based on environment var which
    is sync with the plugin source code
    Returns:
        list: A list of picker names
    """
    resource_env = os.environ.get('MHY_RESOURCE_PATH')
    shape_names = ['rect', 'circle', 'image']
    for root in resource_env.split(';'):
        shape_path = os.path.join(root, 'picker_shapes')
        if os.path.isdir(shape_path):
            for i in os.listdir(shape_path):
                full_path = os.path.join(shape_path, i)
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    name = data.get('name')
                    if name:
                        shape_names.append(name)
    return shape_names


class ViewportPicker(DagNode):
    """
    ls viewport picker class.
    """
    __NODETYPE__ = 'mhyViewportPicker'

    children_info_attr = "children_information"
    ui_type = ['rect', 'circle', 'image']
    try:
        ui_type = _get_all_picker_shapes()
    except Exception as e:
        OpenMaya.MGlobal.displayError(str(e))

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            cmds.loadPlugin('mhy.mll', quiet=True)
        except RuntimeError:
            pass
        name = kwargs.get('name', 'mhyViewportPicker')
        parent = kwargs.get('parent', None)
        if not parent:
            parent = Transform.create(name=name)
            kwargs['name'] = name + "Shape" + parent.name.replace(name, '')
            kwargs['parent'] = parent.name
        elif not cmds.objExists(parent):
            parent = Transform.create(name=parent)
            kwargs['parent'] = parent.name

        picker_node = super(ViewportPicker, cls).create(*args, **kwargs)
        picker_node.make_picker_attrs()
        picker_node.set_visibility(True)
        return picker_node

    @classmethod
    def clear_pickers(cls):
        """
        Remove all viewport picker node from the scene.

        """
        pickers = cmds.ls(type=ViewportPicker.api_type_str)
        pickers = [Node(picker) for picker in pickers]

        for picker in pickers:
            cls.remove_picker(picker)

    @classmethod
    def remove_picker(cls, picker):
        """
        Remove a picker from the scene. This method will delete
        the picker shape.
        If the transform node it's nested to has no other child shape,
        remove it as well
        Args:
            picker(ViewportPicker): A picker instance

        """
        parent = picker.get_parent()
        picker.delete()
        if not parent.get_children():
            parent.delete()

    def make_picker_attrs(self):
        """
        Create required attributes which are not defined in the
        plugin

        """
        self.add_attr(
            "string",
            name=ViewportPicker.children_info_attr)

    def delete(self):
        """
        Override delete method that switch viewport picker to ls controller

        """
        self.set_visibility(False)
        DagNode.delete(self)

    def get_picker_color(self):
        """
        Get the color value of this picker
        Returns:
            list: Color in RGB

        """
        return self.get_attr('color')

    def set_picker_color(self, value):
        self.color.value = value

    def get_picker_highlight_color(self):
        return self.get_attr('highLightColor')

    def set_picker_highlight_color(self, value):
        self.highLightColor.value = value

    def get_picker_alpha(self):
        return self.get_attr('alpha')

    def set_picker_alpha(self, value):
        self.alpha.value = value

    def get_ui_type(self):
        ui_idx = self.get_attr('uiType')
        if ui_idx < len(self.ui_type):
            return self.ui_type[ui_idx]
        else:
            return self.ui_type[-1]

    def set_ui_type(self, val):
        if isinstance(val, six.string_types):
            self.set_attr('uiType', val)
        self.set_attr('uiType', val)

    def get_picker_position(self):
        return self.get_attr('pickerPosition')

    def set_picker_position(self, val):
        self.set_attr('pickerPosition', val)

    def set_image_path(self, path):
        self.set_attr('imagePath', path)

    def get_image_path(self):
        return self.get_attr('imagePath')

    def get_line_width(self):
        return self.get_attr('lineWidth')

    def set_line_width(self, val):
        self.set_attr('lineWidth', val)

    def get_width(self):
        return self.get_attr('width')

    def set_width(self, val):
        self.set_attr('width', val)

    def get_height(self):
        return self.get_attr('height')

    def set_height(self, val):
        self.set_attr('height', val)

    def get_radius(self):
        return self.get_attr('radius')

    def set_radius(self, val):
        return self.set_attr('radius', val)

    # ---------------------------------
    # Methods handle abstract hierarchy
    # ---------------------------------
    def init_position_from_current_view(self, target=None):
        """

        This method init the 2d position of the picker from the active 3d view by
        casting the world position to camera space.
        Args:
            target(Transform or None): A Transform node. If None, self will be the target

        """
        view = OpenMayaUI.M3dView.active3dView()
        if target is None:
            target = self.get_parent()
        position = target.get_translation(space='world', as_tuple=False)
        x_util = OpenMaya.MScriptUtil(0.0)
        x_ptr = x_util.asShortPtr()
        y_util = OpenMaya.MScriptUtil(0.0)
        y_ptr = y_util.asShortPtr()
        position = OpenMaya.MPoint(position)
        view.worldToView(position, x_ptr, y_ptr)
        x = x_util.getShort(x_ptr)
        y = y_util.getShort(y_ptr)
        self.pickerPosition0.value = x
        self.pickerPosition1.value = y

    @property
    def parent_picker(self):
        """
        Get the parent picker. Parent picker is an abstract relationship saved as
        an attribute on the node. It will be used to query the position and
        scale when editing the picker with UI
        Returns:
            Node: The parent node
        """
        if not self.has_attr(ViewportPicker.parent_picker_attr):
            return None
        else:
            parent_name = self.attr(ViewportPicker.parent_picker_attr).value
            if parent_name and cmds.objExists(parent_name):
                return Node(parent_name)

    @parent_picker.setter
    def parent_picker(self, parent):
        if not self.has_attr(ViewportPicker.parent_picker_attr):
            self.add_attr(ViewportPicker.parent_picker_attr)
        self.set_attr(ViewportPicker.parent_picker_attr, str(parent))

    @property
    def children(self):
        children_info = self.get_children_information() or []
        children_list = []
        for child in children_info:
            if cmds.objExists(child):
                children_list.append(ViewportPicker(child))
            else:
                OpenMaya.MGlobal.displayWarning("{} does not exists in the scene".format(child))
        return children_list

    def child_count(self):
        """
        Get the number of children directly under this item
        Returns:
            int: The number of children
        """
        return len(self.__children)

    def append_child(self, child):
        """
        Append a child item to this
        Args:
            child(PoseItem or GroupItem):

        """

        self.__children.append(child)
        child.parent = self

    def remove_child_pickers(self, pickers):
        """
        Remove the child picker from this container's children list
        Args:
            pickers(list): A list of pickers to remove

        """
        children_info = self.get_children_information()
        for picker in pickers:
            if picker.name in children_info:
                del children_info[picker.name]
        self.set_children_information(children_info)

    def add_child_pickers(self, pickers):
        """
        Add pickers to the children list of this container node
        Args:
            pickers(list): A list of picker instances

        """
        current_children_info = self.get_children_information() or {}
        for picker in pickers:
            data = picker.export()
            current_children_info[picker.name] = data

        self.set_children_information(current_children_info)
        return current_children_info

    def is_container(self):
        """
        Check if this node is labeled as container node
        Returns:

        """
        return self.get_ui_type() == ViewportPicker.ui_type[2]

    def get_children_information(self):
        """
        Get information of each child item under this container
        Returns:

        """
        if not self.has_attr(ViewportPicker.children_info_attr):
            return None

        data = self.get_attr(ViewportPicker.children_info_attr)
        if data:
            return json.loads(data)

    def set_children_information(self, data):
        """
        This method will serialize data using json dumps function and save the
        string data to children info attribute of this node
        Args:
            data(dict):  Any data format that json dumps supports

        """
        data = json.dumps(data)
        if not self.has_attr(ViewportPicker.children_info_attr):
            self.add_attr(
                "string",
                name=ViewportPicker.children_info_attr)
        self.set_attr(ViewportPicker.children_info_attr, data)

    def get_children_pickers(self):
        """
        Get the children pickers
        Returns:
            list: A list of children nodes
        """
        children = []
        name_space = self.get_name_space()
        children_info = self.get_children_information()
        if not children_info:
            return children
        for child in self.get_children_information():
            if name_space:
                child = '{}:{}'.format(name_space, child)
            if cmds.objExists(child):
                child = Node(child)
                children.append(child)
        return children

    def show_all_children(self):
        """
        Show all children pickers of this container node
        """
        for child in self.get_children_pickers():
            child.show()

    def hide_all_children(self):
        """
        Hide all children pickers of this container node
        """
        for child in self.get_children_pickers():
            child.hide()

    def switch_children_viewport_picker(self, stat=True):
        """
        Switch all children pickers between picker mode and controller mode
        Args:
            stat(bool): If switch to picker mode

        Returns:

        """
        for child in self.get_children_pickers():
            child.set_visibility(stat)

    def update_children_with_info_attr(self):
        """
        Update children node's attributes based on cached information
        in the children information attribute

        """
        info = self.get_children_information()
        if not info:
            return
        name_space = self.get_name_space()
        for child_name, val in info.items():
            if name_space:
                child_name = name_space + ':' + child_name
            if cmds.objExists(child_name):
                child_node = Node(child_name)
                child_node.load(val)

    @property
    def attributes_to_export(self):
        return ['uiType', 'color', 'highLightColor', 'alpha',
                'pickerPosition', 'pickerLocalScale', 'lineWidth',
                'imagePath', 'radius', 'width', 'height']

    def export(self):
        """
        Override the export method
        Returns:

        """
        parent = self.get_parent()

        data = {"name": self.name.split(':')[-1],
                "position": self.get_picker_position(),
                "uiType": self.get_ui_type(),
                "color": self.get_picker_color(),
                "hiColor": self.get_picker_highlight_color(),
                'alpha': self.get_picker_alpha(),
                'radius': self.get_radius(),
                'width': self.get_width(),
                'height': self.get_height(),
                'image_path': self.get_image_path(),
                'is_filled': self.isFilled.value,
                'line_width': self.lineWidth.value
                }
        if parent:
            data['parent'] = parent.name.split(':')[-1]

        if self.has_attr(ViewportPicker.children_info_attr):
            child_info = self.get_children_information()
            if child_info:
                data['children'] = self.get_children_information()

        return data

    def load(self, data):
        """
        Load data to this node
        Args:
            data:

        Returns:

        """
        self.set_ui_type(data.get('uiType', 0))
        self.set_picker_color(data.get('color', (1, 0, 0)))
        self.set_picker_highlight_color(data.get('hiColor', (1, 1, 1)))
        self.set_picker_alpha(data.get('alpha', 1))
        self.set_picker_position(data.get('position', 1))
        self.set_radius(data.get('radius', 20))
        self.set_width(data.get('width', 20))
        self.set_height(data.get('height', 20))
        self.set_image_path(data.get('image_path', ""))

        is_filled = data.get('is_filled')
        if is_filled is not None:
            self.isFilled.value = bool(is_filled)

        line_width = data.get('line_width')
        if line_width is not None:
            self.lineWidth.value = line_width

        if data.get('children'):
            self.set_children_information(data.get('children'))

    @classmethod
    def list_containers(cls):
        """
        Get all the container picker from current scene
        Returns:
            list: A list of container picker instances
        """
        containers = []
        pickers = cmds.ls(type='mhyViewportPicker')
        for picker in pickers:
            node = Node(picker)
            if node.get_ui_type() == ViewportPicker.ui_type[2]:
                containers.append(node)

        return containers

    @classmethod
    def create_container(cls, name=None):
        """
        Create a picker node and make a container
        Returns:
            ViewportPicker:
        """
        if not name:
            name = "picker_container"
        container = ViewportPicker.create(name=name)
        container.set_ui_type('image')
        return container

    def init_from_controller(self, controller):
        """
        Initialize some attribute based on the controller shape node it is associated with
        Args:
            controller(mhyController or str): A ls controller Node

        """
        if not controller:
            self.set_ui_type('circle')
            self.set_radius(20)
            return

        if isinstance(controller, six.string_types):
            controller = Node(controller)
        color_r = controller.colorR.value
        color_g = controller.colorG.value
        color_b = controller.colorB.value
        self.set_picker_color([color_r, color_g, color_b])
        shape_type = controller.shapeType.value

        if shape_type == 1 or shape_type == 2:
            # For now only square shape is shared by picker and controller
            self.set_ui_type('rect')
            self.set_width(20)
            self.set_height(20)
        else:
            self.set_ui_type('circle')
            self.set_radius(20)

    def set_visibility(self, status):
        """
        If show view port picker or / regular ls controller
        Args:
            status:

        Returns:

        """
        if status:
            self.show()
        else:
            self.hide()

    def get_sibling_controller(self):
        """
        Find the ls controller shape node under the same transform node with this node
        Returns:
            mhyController or None:
        """
        parent = self.get_parent()
        children = parent.get_children()

        for i in children:
            if i.type_name == "mhyController":
                return i

    def mirror_from(self, other, container):
        """
        Mirror the position, shape and properties from another picker node across the middle line
        of the container node
        Args:
            other(ViewportPicker):
            container(ViewportPicker):

        """
        container_pos = container.get_picker_position()
        mid_x = container_pos[0]

        # Mirror position
        other_pos = other.get_picker_position()
        self_pos = [mid_x - (other_pos[0] - mid_x), other_pos[1]]
        self.set_picker_position(self_pos)

        # Mirror properties
        self.set_width(other.get_width())
        self.set_height(other.get_height())
        self.set_radius(other.get_radius())

        self.set_picker_alpha(other.get_picker_alpha())
        self.set_ui_type(other.get_ui_type())

        self.lineWidth.value = other.lineWidth.value

        self.rotate.value = -1*other.rotate.value



