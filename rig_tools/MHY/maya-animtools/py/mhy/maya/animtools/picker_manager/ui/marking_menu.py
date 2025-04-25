import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node
import mhy.maya.animtools.picker_manager.node.viewport_picker as vp
import mhy.maya.animtools.picker_manager.api.pickers as picker_api
import mhy.maya.animtools.picker_manager.api.sel_set as sel_set_api


_CMD_IMP_API = 'import mhy.maya.animtools.picker_manager.api.pickers as api;'
_CMD_IMP_SEL_SET_API = 'import mhy.maya.animtools.picker_manager.api.sel_set as api;'


active_name_space = None


def create_picker_menu_items(obj):
    """Dynamically creates viewport picker marking menu items
    based on an input object.

    Args:
        obj (str): The input object to build the marking menu from.

    Returns:
        None
    """
    obj = Node(obj)
    if not obj.custom_type_name == 'MHYCtrl':
        return
    is_picker = False
    picker = None
    for child in obj.get_children():
        if child.type_name == 'mhyViewportPicker':
            picker = child
            is_picker = True
    if not is_picker:
        return

    cmds.menuItem(
        label='Scale Pickers',
        radialPosition='NE',
        subMenu=True)

    cmds.menuItem(
        label="Scale Up Pickers",
        command=_CMD_IMP_API + "api.scale_up_container()")

    cmds.menuItem(
        label="Scale Down Pickers",
        command=_CMD_IMP_API + "api.scale_down_container()")

    cmds.setParent('..', menu=True)

    cmds.menuItem(
        label="Move Up Pickers",
        image='arrowUp',
        radialPosition='N',
        command=_CMD_IMP_API + "api.move_all_container(direction=[0,1])")

    cmds.menuItem(
        label="Move Down Pickers",
        image='arrowDown',
        radialPosition='S',
        command=_CMD_IMP_API + "api.move_all_container(direction=[0,1])")

    cmds.menuItem(
        label="Move Pickers To Right",
        image='arrowRight',
        radialPosition='E',
        command=_CMD_IMP_API + "api.move_all_container(direction=[1,0])")

    cmds.menuItem(
        label="Move Pickers To Left",
        image='arrowLeft',
        radialPosition='W',
        command=_CMD_IMP_API + "api.move_all_container(direction=[1,0])")

    containers = vp.ViewportPicker.list_containers()

    if containers:
        global active_name_space
        current_container = picker_api.get_current_container()

        if current_container:
            if ':' in current_container.name:
                active_name_space, _ = current_container.name.split(':')
            else:
                active_name_space = ""

        container_map = picker_api.get_name_space_container_map()

        name_space_options = [i for i in container_map.keys()]
        name_space_options = sorted(name_space_options)
        cmds.menuItem(
            label="Set Active Namespace",
            radialPosition='SW',
            subMenu=True)

        cmds.radioMenuItemCollection()

        for name_space in name_space_options:
            active_container = container_map.get(name_space, [])
            if active_container:
                active_container = active_container[0]
            if name_space == ':':
                name_space = ''
            if name_space == active_name_space:
                state = True
            else:
                state = False
            cmds.menuItem(
                label=name_space,
                command="from mhy.maya.animtools.picker_manager.ui.marking_menu import set_active_name_space;"
                        "set_active_name_space('{}', '{}')".format(name_space, active_container),
                radioButton=state
            )

        cmds.setParent('..', menu=True)

        cmds.menuItem(
            label='Switch Picker Container',
            image='pickCompByType',
            radialPosition='SE',
            subMenu=True)

        if not active_name_space:
            container_list = container_map.get(':', [])
        else:
            container_list = container_map.get(active_name_space, [])

        cmds.radioMenuItemCollection()
        for container in container_list:
            state = False
            if current_container and container == current_container.name:
                state = True
            cmds.menuItem(
                label=container,
                command=_CMD_IMP_API + "api.switch_container_to('{}')".format(container),
                radioButton=state
            )

        cmds.setParent('..', menu=True)

    if picker.visibility.value:
        cmds.menuItem(
            label='Hide Pickers',
            image='switchOn',
            radialPosition='NW',
            command=_CMD_IMP_API + "api.switch_all_picker_node_mode(False)")
    else:
        cmds.menuItem(
            label='Show Pickers',
            image='switchOn',
            radialPosition='NW',
            command=_CMD_IMP_API + "api.switch_all_picker_node_mode(True)")

    sel = cmds.ls(sl=True)
    sel_sets = list()
    for i in sel:
        sets = sel_set_api.find_related_selection_set(i)
        sel_sets.extend(sets)
    sel_sets = list(set(sel_sets))

    for sel_set in sel_sets:
        name = sel_set_api.simplfy_set_name(sel_set.name)
        cmds.menuItem(
            label=name,
            image='objectSet',
            command=_CMD_IMP_SEL_SET_API + "api.select_set('{}')".format(sel_set.name)
        )


def set_active_name_space(name_space, active_container=None):
    global active_name_space
    active_name_space = name_space
    if active_container:
        picker_api.switch_container_to(active_container)
