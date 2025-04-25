import json
import six

import shiboken2
from PySide2 import QtWidgets, QtGui

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI

from mhy.maya.standard.name import NodeName
from mhy.python.core.compatible import long
from mhy.maya.animtools.picker_manager.api.sel_set import export_sel_set_data, load_sel_set_data
from mhy.maya.nodezoo.node import Node
import mhy.maya.nodezoo.utils as utils
import mhy.maya.animtools.picker_manager.node.viewport_picker as vp
import mhy.maya.utils as mutil

picker_type_name = 'mhyViewportPicker'


def create_picker_for_selected(container):
    """
    Create picker shape for selected controllers
    Returns:
        list: list of pickers
    """
    sel = utils.ls(sl=True, type='transform')
    pickers = []
    for i in sel:
        control_shapes = i.get_shapes()
        if control_shapes:
            picker = get_picker(i, parent=container)
            pickers.append(picker)
    container.add_child_pickers(pickers)
    return pickers


def find_pickers(nodes=None):
    """
    Find pickers from nodes. If the node is transform, search its
    shape children
    Args:
        nodes(list): A list of objects

    Returns:
        list: Found pickers
    """
    if nodes is None:
        nodes = cmds.ls(sl=True)
    if isinstance(nodes, six.string_types):
        nodes = [nodes]

    pickers = []
    for node in nodes:
        node = Node(node)
        if node.type_name == "transform":
            for child in node.get_children():
                if child.type_name == picker_type_name:
                    pickers.append(child)
        elif node.type_name == picker_type_name:
            pickers.append(node)
    pickers = list(set(pickers))
    return pickers


def hide_all_pickers():
    """
    Hide all picker nodes in the scene
    Returns:

    """
    nodes = utils.ls(type=picker_type_name)
    for node in nodes:
        node.hide()


def switch_all_picker_node_mode(picker_mode=True):
    """
    Switch picker nodes between picker mode and controller mode
    Returns:

    """
    nodes = utils.ls(type=picker_type_name)
    for node in nodes:
        node.set_visibility(picker_mode)

    if picker_mode:
        containers = vp.ViewportPicker.list_containers()
        for cnt in containers:
            parent = cnt.get_parent()
            if parent and parent.v.value:
                switch_container_to(cnt)
                return

        if containers:
            switch_container_to(containers[0])


def get_picker(transform, parent=None):
    """
    Get the picker node under transform node. If not exists, create one.
    Args:
        transform:
        parent(ViewportPicker): The container node the search picker from
    Returns:

    """
    for child in transform.get_children():
        if child.type_name == picker_type_name:
            if parent and child not in parent.children:
                child.init_position_from_current_view()
            return child

    valid_name = NodeName.is_valid(transform.name)
    if valid_name:
        name = NodeName(transform.name)
        ext = name.ext
        ext = ext.replace('CTRL', 'PICKER')
        name = name.replace_ext(ext)
    else:
        name = transform.name + '_PICKER'
    picker = vp.ViewportPicker.create(name=name, parent=transform)
    picker.init_position_from_current_view()
    controller = picker.get_sibling_controller()
    picker.init_from_controller(controller)
    picker.set_visibility(True)
    picker.add_marking_menu('mhy_picker_marking_menu', mod='ctrl')
    return picker


def export_data_to_file(file_path, pickers):
    """
    Export data from some picker objects to a disk path in json format.
    This function will also export selection set data
    Args:
        file_path(str): The path of a file
        pickers(list): A list of picker objects

    Returns:
        dict: Exported dictionary data

    """
    data_to_export = {'pickers': dict(),
                      'selection_sets': dict()}

    for picker in pickers:
        data = picker.export()
        data_to_export['pickers'][picker.name] = data

    sel_set_data = export_sel_set_data()
    if sel_set_data:
        data_to_export['selection_sets'] = sel_set_data

    file_path = file_path.replace('\\', '/')
    json_obj = json.dumps(data_to_export)
    with open(file_path, "w") as f:
        f.write(json_obj)
    OpenMaya.MGlobal.displayInfo("Exported data to `{}`".format(file_path))
    return data_to_export


def load_data_from_file(file_path):
    """
    Load data from a file path.
    Args:
        file_path(str): The path of a file

    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    if 'pickers' in data:
        # This is new format data with selection set data
        picker_data = data['pickers']
    else:
        picker_data = data

    for name, item_data in picker_data.items():
        ui_type = item_data.get('uiType')

        parent = item_data.get('parent', None)
        if ui_type != 'image' and not Node.object_exist(parent):
            OpenMaya.MGlobal.displayWarning("{} does not exist".format(parent))
            continue
        name = item_data.get('name', None)
        picker = vp.ViewportPicker.create(
            name=name,
            parent=parent)
        picker.load(item_data)
        picker.add_marking_menu('mhy_picker_marking_menu', mod='ctrl')

    sel_set_data = data.get('selection_sets')
    if sel_set_data:
        load_sel_set_data(sel_set_data)

    containers = vp.ViewportPicker.list_containers()
    if containers:
        switch_container_to(containers[0], sync_children=False)


def switch_container_to(container, sync_children=False):
    """
    Switch active picker container to a given container.
    if it is edit mode, show controllers not in the this container after switch
    so user can continue add them to other containers. Otherwise, all the picker and
    controller will be hidden except for the ones as children of this container

    This action will hide/show container shape/parent at the same time to record active
    container by the visibility of container node. This will work with hide/show all pickers
    so that previous active container can be found by checking the state of parent node of
    container shape
    Args:
        container(str or ViewportPicker)88:
        sync_children(bool): If sync children info attribute value based on children pickers before
        switching the active container node

    Returns:

    """
    containers = vp.ViewportPicker.list_containers()
    for ctn in containers:
        if ctn.v.value:
            if sync_children:
                sync_container_children_info(ctn)
            ctn.hide()
            parent = ctn.get_parent()
            parent.hide()

    hide_all_pickers()

    container = vp.ViewportPicker(container)
    container.show()
    parent = container.get_parent()
    parent.show()
    container.show_all_children()

    container.update_children_with_info_attr()


def sync_container_children_info(container):
    """
    Sync the container children info by getting data from each child node
    in the scene and update the information dictionary
    Args:
        container(str or ViewportPicker):

    Returns:

    """
    container = vp.ViewportPicker(container)
    children_info = container.get_children_information() or {}
    children_pickers = container.get_children_pickers()
    for child in children_pickers:
        data = child.export()
        child_name = child.name.split(':')[-1]
        children_info[child_name].update(data)
    container.set_children_information(children_info)


def get_current_container():
    """
    Assume only one container is visible at a time as active container.

    Returns:
        ViewportPicker:

    """
    containers = vp.ViewportPicker.list_containers()
    for container in containers:
        if container.v.value:
            return container


def scale_container_and_children(container=None, factor=1, pivot='C'):
    """
    Scale container and its children at a given factor from a specific pivot.
    Accepted pivots are: 'C', 'N', 'NE', 'NW', 'W', 'E', 'SW', 'S', 'SE'.
    'NE' is short for 'North East' representing the top left most point of the bounding
    box in viewport space.

    Args:
        container(str or ViewportPicker):
        factor(float):
        pivot(str):

    Returns:

    """
    if not container:
        container = get_current_container()
    else:
        container = vp.ViewportPicker(container)
    positions = list()
    pickers = container.get_children_pickers() + [container]
    for picker in pickers:
        pos = picker.get_picker_position()
        positions.append(pos)

    box = bounding_box(positions)
    if pivot == 'C':
        pivot_cord = ((box[0][0] + box[1][0]) / 2, (box[0][1] + box[1][1]) / 2)

    for picker in pickers:
        orig_pos = picker.get_picker_position()
        new_pos = ((orig_pos[0] - pivot_cord[0]) * factor + pivot_cord[0],
                   (orig_pos[1] - pivot_cord[1]) * factor + pivot_cord[1])
        picker.set_picker_position(new_pos)
        picker.set_height(picker.get_height() * factor)
        picker.set_width(picker.get_width() * factor)
        picker.set_line_width(picker.get_line_width() * factor)
        picker.set_radius(picker.get_radius() * factor)

    sync_container_children_info(container)


@mutil.undoable
def move_all_container(direction, container=None):
    """
    Move container and its children at a given direction from a specific pivot.

    Args:
        direction(list): a two dimensional list as moving direction. e.g. [0, 1] is moving toward +y direction
        container(ViewportPicker):
    Returns:

    """
    sel = cmds.ls(sl=True)
    vp = cmds.getPanel(withFocus=True)  # current viewport

    vp_widget = OpenMayaUI.MQtUtil.findControl(vp)
    vp_widget = shiboken2.wrapInstance(long(vp_widget), QtWidgets.QWidget)

    cursor_pos = QtGui.QCursor().pos()

    target_pos = vp_widget.mapFromGlobal(cursor_pos)

    if not container:
        container = get_current_container()
    else:
        container = vp.ViewportPicker(container)
    pickers = container.get_children_pickers() + [container]
    widget_height = vp_widget.height()

    container_pos = None
    if sel:
        for i in sel:
            node_obj = Node(i)
            if container_pos:
                break
            if hasattr(node_obj, 'get_children'):
                children = node_obj.get_children()
                for child in children:
                    if child.type_name == picker_type_name:
                        container_pos = child.get_picker_position()
                        break
    if not container_pos:
        container_pos = container.get_picker_position()
    delta = [(target_pos.x() - container_pos[0]) * direction[0],
             ((widget_height - target_pos.y()) - container_pos[1]) * direction[1]]
    for picker in pickers:
        pos = picker.get_picker_position()
        pos = (pos[0] + delta[0], pos[1] + delta[1])
        picker.set_picker_position(pos)
    sync_container_children_info(container)


@mutil.undoable
@mutil.repeatable
def scale_up_container():
    scale_container_and_children(factor=1.1)


@mutil.undoable
@mutil.repeatable
def scale_down_container():
    scale_container_and_children(factor=0.9)


def bounding_box(positions):
    """
    Get the bounding box of given 2d positions
    Args:
        positions(list): A list of positions in list or tuple of 2 elements

    Returns:
        list: [left_low_corner, right_top_corner]

    """
    x_coordinates, y_coordinates = zip(*positions)

    return [(min(x_coordinates), min(y_coordinates)), (max(x_coordinates), max(y_coordinates))]


def get_name_space_container_map():
    """

    Returns:

    """
    containers = vp.ViewportPicker.list_containers()

    container_map = {}
    for container in containers:
        ns = container.get_name_space() or ':'
        if ns not in container_map:
            container_map[ns] = []
        container_map[ns].append(container.name)
    return container_map
