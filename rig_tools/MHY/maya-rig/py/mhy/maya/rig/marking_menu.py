from maya import cmds

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.utils as mutil

import mhy.maya.rig.rig_global as rg
import mhy.maya.rig.constants as const
import mhy.maya.rig.marker_system as ms
import mhy.maya.rig.node.marker as _marker
from mhy.maya.startup.marking_menu import ActionItem

_IMP_THIS = 'import mhy.maya.rig.marking_menu as mm;'
_IMP_MS = 'import mhy.maya.rig.marker_system as ms;'
_IMP_ALIGN = 'import mhy.maya.align as align;'
_NOT_IMPLEMENTED_CMD = (
    'from maya import cmds;'
    'cmds.warning("feature not implemented yet.. :(");')


def create_marker_menu_items(obj):
    """Dynamically creates marker system marking menu items
    based on the input object.

    Args:
        obj (str): The input object to build the marking menu from.

    Returns:
        None
    """
    obj = Node(obj)

    global_root = Node(const.MARKER_ROOT)

    cmds.menuItem(
        label='Marker Root',
        image='kinReroot',
        radialPosition='N',
        command='{}mm._select("{}");'.format(_IMP_THIS, global_root))

    cmds.menuItem(
        label='Reset Hier Ctrls',
        image='CN_refresh',
        radialPosition='NW',
        command='{}ms._align_hier_ctrls();'.format(_IMP_MS))

    cmds.menuItem(
        label='Mirror Markers',
        image='HIKmirror',
        radialPosition='W',
        command='{}ms._mirror_markers();'.format(_IMP_MS))

    cmds.menuItem(
        label='Solo',
        image='visible',
        radialPosition='NE',
        command='{}ms._solo_marker_system("{}");'.format(_IMP_MS, obj))

    cmds.menuItem(
        label='Show All',
        image='QR_show',
        radialPosition='E',
        command='{}ms._show_all_marker_system();'.format(_IMP_MS))

    submenu = cmds.menuItem(
        label='Connection',
        image='out_geoConnectable',
        radialPosition='SW',
        subMenu=True)

    cmds.menuItem(
        parent=submenu,
        label='Connect',
        radialPosition='S',
        command=_IMP_MS + 'ms._connect_marker_system();')

    cmds.menuItem(
        parent=submenu,
        label='Disconnect',
        radialPosition='N',
        command=_IMP_MS + 'ms._disconnect_marker_system("{}");'.format(obj))

    sel = ms._get_selected_markers()
    if len(sel) == 2 and sel[0].is_leaf:
        cmds.menuItem(
            parent=submenu,
            label='Connect + Follow',
            radialPosition='E',
            command=_IMP_MS + 'ms._connect_marker_system(mode="follow");')

        cmds.menuItem(
            parent=submenu,
            label='Connect + Aim',
            radialPosition='W',
            command=_IMP_MS + 'ms._connect_marker_system(mode="aim");')

    cmds.setParent('..', menu=True)

    # marker toggles
    submenu = cmds.menuItem(
        label='Marker Toggles',
        image='advancedSettings',
        subMenu=True)

    checked = global_root.attr(_marker.ATTR_HIER_VIS).value
    cmds.menuItem(
        label='Toggle Hier Ctrls',
        checkBox=checked,
        parent=submenu,
        command='{}mm._toggle_hier_ctrls();'.format(_IMP_THIS))

    checked = global_root.attr(_marker.ATTR_AXIS_DISPLAY).value
    cmds.menuItem(
        label='Toggle Axis',
        checkBox=checked,
        parent=submenu,
        command='{}mm._toggle_marker_axis();'.format(_IMP_THIS))

    checked = ms._is_line_colored()
    cmds.menuItem(
        label='Toggle Line Color',
        checkBox=checked,
        parent=submenu,
        command=_IMP_MS + 'ms._toggle_line_colored();')

    cmds.setParent('..', menu=True)

    cmds.menuItem(divider=True)

    # alignment tools
    cmds.menuItem(
        label='Snap',
        image='pixelSnap',
        command=_IMP_ALIGN + 'align.snap("{}");'.format(obj))

    cmds.menuItem(
        label='Align Colinear',
        image='UVAlignMiddleU',
        command=_IMP_ALIGN + 'align.align_colinear();')

    cmds.menuItem(
        label='Space Evenly',
        image='alignTool',
        command=_IMP_ALIGN + 'align.align_colinear(even_space=True);')

    cmds.menuItem(
        label='Align Coplaner',
        image='align',
        command=_IMP_ALIGN + 'align.align_coplanar();')


def create_rig_menu_items(obj, dry_run=False):
    """Dynamically creates rig marking menu items
    based on an input object.

    Args:
        obj (str): The input object to build the marking menu from.

    Returns:
        list: Public ActionItem instances
        None
    """
    obj = Node(obj)
    rig = rg.RigGlobal(obj)
    limbs = rig.get_limbs()

    limb_root = None
    if obj.custom_type_name == 'MHYCtrl':
        limb_root = obj.limb_root

    public_item_array = list()

    # selection
    ActionItem(
        label='Select All Ctrls',
        image='character',
        radialPosition='N',
        command='{}mm._select_rig_ctrls("{}")'.format(_IMP_THIS, rig),
        dry_run=dry_run,
    )

    if limb_root:
        ActionItem(
            label='Select ' + limb_root.limb_name,
            radialPosition='NW',
            image='pickHierarchy',
            command='{}mm._select_limb_ctrls("{}")'.format(
                _IMP_THIS, limb_root),
            dry_run=dry_run,
            collection=public_item_array
        )

        ActionItem(
            label='Select {} + Children'.format(limb_root.limb_name),
            radialPosition='W',
            image='pickHierarchy',
            command=('{}mm._select_limb_ctrls("{}",'
                     'recursive=True)').format(_IMP_THIS, limb_root),
            dry_run=dry_run,
        )

    submenu = ActionItem(
        label='Select Limb',
        image='frameHierarchy',
        radialPosition='SW',
        subMenu=True,
        dry_run=dry_run,
        collection=public_item_array
    )

    for limb in limbs:
        ActionItem(
            parent=submenu,
            label=limb.limb_name,
            command='{}mm._select_limb_ctrls("{}")'.format(_IMP_THIS, limb),
            dry_run=dry_run,
        )

    cmds.setParent('..', menu=True)

    # reset rig
    submenu = ActionItem(
        label='Reset Pose',
        image='HIKCharacterToolFullBody',
        radialPosition='NE',
        subMenu=True,
        command='{}mm._reset_pose("{}")'.format(_IMP_THIS, rig),
        dry_run=dry_run,
    )

    ActionItem(
        parent=submenu,
        label='Reset Selected',
        radialPosition='E',
        command=('{}mm._reset_pose("{}",'
                 'selected=True, world_offset=True)').format(_IMP_THIS, rig),
        dry_run=dry_run,
        collection=public_item_array
    )

    ActionItem(
        parent=submenu,
        label='Reset Rig + World Offsets',
        radialPosition='N',
        command=('{}mm._reset_pose("{}",'
                 'selected=False, world_offset=True)').format(_IMP_THIS, rig),
        dry_run=dry_run,
    )

    ActionItem(
        parent=submenu,
        label='Reset Rig',
        radialPosition='S',
        command='{}mm._reset_pose("{}", selected=False)'.format(_IMP_THIS, rig),
        dry_run=dry_run,
    )

    cmds.setParent('..', menu=True)

    # mirorring
    if rig.has_mirror_data:
        submenu = ActionItem(
            label='Mirror Pose',
            image='kinMirrorJoint_S',
            radialPosition='E',
            subMenu=True,
            command='{}mm._mirror_pose("{}")'.format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        ActionItem(
            parent=submenu,
            label='Mirror Selected',
            radialPosition='E',
            command=('{}mm._mirror_pose("{}", selected=True,'
                     'world_offset=True)').format(_IMP_THIS, rig),
            dry_run=dry_run,
            collection=public_item_array
        )

        ActionItem(
            parent=submenu,
            label='Mirror Rig + World Offsets',
            radialPosition='N',
            command=('{}mm._mirror_pose("{}", selected=False,'
                     'world_offset=True)').format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        ActionItem(
            parent=submenu,
            label='Mirror Rig',
            radialPosition='S',
            command=('{}mm._mirror_pose("{}",'
                     'selected=False)').format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        cmds.setParent('..', menu=True)

        submenu = ActionItem(
            label='Flip Pose',
            image='kinMirrorJoint_S',
            radialPosition='SE',
            subMenu=True,
            command='{}mm._mirror_pose("{}", flip=True)'.format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        ActionItem(
            parent=submenu,
            label='Flip Selected',
            radialPosition='E',
            command=('{}mm._mirror_pose("{}", flip=True,' 'selected=True,'
                     'world_offset=True)').format(_IMP_THIS, rig),
            dry_run=dry_run,
            collection=public_item_array
        )

        ActionItem(
            parent=submenu,
            label='Flip Rig + World Offsets',
            radialPosition='N',
            command=('{}mm._mirror_pose("{}", flip=True, selected=False,'
                     'world_offset=True)').format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        ActionItem(
            parent=submenu,
            label='Flip Rig',
            radialPosition='S',
            command=('{}mm._mirror_pose("{}", flip=True,'
                     'selected=False)').format(_IMP_THIS, rig),
            dry_run=dry_run,
        )

        cmds.setParent('..', menu=True)
    else:
        ActionItem(
            label='Mirror/Flip Pose Not Avaiable',
            image='kinMirrorJoint_S',
            radialPosition='E'),

    ActionItem(
        label='Mirror Selection',
        image='selectCycle',
        radialPosition='S',
        command=_IMP_THIS + 'mm._mirror_ctrl_selection()',
        dry_run=dry_run,
    )

    # toggles
    submenu = ActionItem(
        label='Rig Toggles',
        image='advancedSettings',
        subMenu=True,
        dry_run=dry_run
    )

    for attr in rig.get_toggle_attrs():
        ActionItem(
            label=attr.name,
            checkBox=attr.value,
            parent=submenu,
            command='{}mm._toggle_rig_attr("{}")'.format(
                _IMP_THIS, attr.long_name),
            dry_run=dry_run
        )

        cmds.setParent('..', menu=True)

    ActionItem(divider=True, dry_run=dry_run)

    # other menu items
    ActionItem(
        label='Align World Offset Ctrls',
        image='polyAlignUVs',
        command='{}mm._align_world_offsets("{}")'.format(_IMP_THIS, rig),
        dry_run=dry_run,
    )

    if limb_root and not dry_run:
        ActionItem(divider=True, dry_run=dry_run)

        # fkik switch
        fkik_switch = obj.get_fkik_switch()
        if fkik_switch:
            ActionItem(
                label='[PH] FK/IK Switch',
                image='switchOn',
                command=_NOT_IMPLEMENTED_CMD,
                dry_run=dry_run
            )
            ActionItem(
                optionBox=True,
                command=_NOT_IMPLEMENTED_CMD,
                dry_run=dry_run
            )

            cmds.setParent('..', menu=True)

        # space switch
        space_switch = obj.get_space_switch()
        if space_switch:
            ActionItem(
                label='[PH] Space Switch',
                image='switchOn',
                command=_NOT_IMPLEMENTED_CMD,
                dry_run=dry_run
            )

    ActionItem(
        label='T=0',
        image='move_M',
        command='{}mm._reset_channels("t", "xyz")'.format(_IMP_THIS),
        dry_run=dry_run,
        collection=public_item_array
    )
    ActionItem(
        label='R=0',
        image='rotate_M',
        command='{}mm._reset_channels("r", "xyz")'.format(_IMP_THIS),
        dry_run=dry_run,
        collection=public_item_array
    )
    ActionItem(
        label='TR=0',
        image='srt_M',
        command='{}mm._reset_channels()'.format(_IMP_THIS),
        dry_run=dry_run,
        collection=public_item_array
    )


    return public_item_array

# --- marker callback functions


def _select(nodes):
    cmds.select(nodes, replace=True)


@mutil.undoable
def _toggle_marker_axis():
    attr = Node(const.MARKER_ROOT).attr(_marker.ATTR_AXIS_DISPLAY)
    attr.value = not attr.value
    sel = cmds.ls(selection=True, long=True)

    # select marker root to force draw axis
    cmds.select(const.MARKER_ROOT, replace=True)
    if sel:
        cmds.select(sel, replace=True)
    else:
        cmds.select(clear=True)


def _toggle_hier_ctrls():
    attr = Node(const.MARKER_ROOT).attr(_marker.ATTR_HIER_VIS)
    attr.value = not attr.value


# --- ctrl callback functions


@mutil.undoable
def _select_limb_ctrls(limb_root, recursive=False):
    """Select all ctrls in a limb."""
    limb_root = Node(limb_root)
    ctrls = limb_root.get_ctrls()
    if recursive:
        for c in limb_root.get_child_limbs(recursive=True):
            ctrls += c.get_ctrls()
    if not ctrls:
        cmds.warning('No ctrls found.')
        return
    cmds.select(ctrls, replace=True)


@mutil.undoable
def _select_rig_ctrls(rig):
    """Select all ctrls in a rig."""
    rig = rg.RigGlobal(rig)
    ctrls = rig.get_ctrls()
    if not ctrls:
        cmds.warning('{} has no ctrls.'.format(rig.name))
        return
    cmds.select(ctrls, replace=True)


@mutil.undoable
def _mirror_ctrl_selection():
    """Mirror selected ctrls."""
    ctrls = []
    for node in cmds.ls(selection=True, type='transform') or []:
        if ':' in node:
            ns = node.split(':', 1)[0] + ':'
        else:
            ns = ''

        mnode = ns + NodeName(node).flip()
        if cmds.objExists(mnode):
            mnode = Node(mnode)
            if mnode.custom_type_name == 'MHYCtrl':
                ctrls.append(mnode)
    if not ctrls:
        cmds.warning('No ctrls are selected.')
        return
    cmds.select(ctrls, replace=True)


def _get_selected_ctrls():
    ctrls = []
    for each in cmds.ls(selection=True, type='transform') or []:
        each = Node(each)
        if each.custom_type_name == 'MHYCtrl':
            ctrls.append(each)
    if not ctrls:
        cmds.warning('No ctrls selected.')
    return ctrls


@mutil.undoable
def _mirror_pose(rig, flip=False, selected=False, world_offset=False):
    rig = rg.RigGlobal(rig)
    ctrls = None
    if selected:
        ctrls = _get_selected_ctrls()
        if not ctrls:
            return
    rig.mirror_pose(ctrls=ctrls, flip=flip, world_offset=world_offset)


@mutil.undoable
def _reset_pose(rig, selected=False, world_offset=False):
    rig = rg.RigGlobal(rig)
    ctrls = None
    if selected:
        ctrls = _get_selected_ctrls()
        if not ctrls:
            return
    rig.reset_pose(ctrls=ctrls, world_offset=world_offset)


@mutil.undoable
def _reset_channels(attrs='tr', axis='xyz'):
    """
    Reset given transform attributes
    Args:
        attrs(str): A string representing attribute compounds. e.g. tr means translation and rotation
        axis(str): A string representing axis.


    """
    ctrls = _get_selected_ctrls()
    if not ctrls:
        return
    if not attrs or not axis:
        return

    attr_name_list = [attr + ax for attr in attrs for ax in axis]
    for ctrl in ctrls:
        for attr in attr_name_list:
            attr_inst = ctrl.attr(attr)
            if attr_inst.is_free_to_change:
                attr_inst.value = 0

@mutil.undoable
def _align_world_offsets(rig):
    rig = rg.RigGlobal(rig)
    rig.align_world_offsets()


def _toggle_rig_attr(attr):
    val = cmds.getAttr(attr)
    cmds.setAttr(attr, not val)
