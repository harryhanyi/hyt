"""
Marker node class
"""

from maya import cmds

from mhy.maya.nodezoo.node import Node, Joint
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath

import mhy.maya.rig.constants as const


ATTR_MARKER_CHAIN = 'marker_chain'
ATTR_AXIS_DISPLAY = 'display_axis'
ATTR_MARKER_SCALE = 'marker_scale'
ATTR_MARKER_VIS = 'marker_vis'
ATTR_HIER_VIS = 'hier_ctrl_vis'
ATTR_UP_OFF = 'up_axis_offset'
ATTR_COLOR_M = 'color_m'
ATTR_COLOR_L = 'color_l'
ATTR_COLOR_R = 'color_r'
ATTR_POLE_DIST = 'pole_distance'
ATTR_ROT_ORDER = 'skel_rotate_order'

ATTR_ROT_TYPE = 'rotation_type'
ATTR_IS_LEAF = 'is_leaf'

DEFAULT_AXIS_DISPLAY = False
DEFAULT_MARKER_SCALE = .5
DEFAULT_MARKER_VIS = True
DEFAULT_HIER_VIS = False
DEFAULT_COLOR_L = (.6, 0, .07)
DEFAULT_COLOR_R = (0, .07, .6)
DEFAULT_COLOR_M = (.8, .6, 0)
DEFAULT_POLE_DIST = 10

HIER_CTRL_SIZE_MULT = 2

TAG_PARENT_MARKER = 'parent_marker'
TAG_HIER_CTRL = 'hier_ctrl'
TAG_UP_CTRL = 'up_ctrl'

# Nodes marked with this tag will be deleted specifically
# when deleting the entire marker
TAG_DELETE = 'marker_delete'


class MHYMarker(Joint):
    """
    A class interfacing marker nodes used in the MHY rigging system.
    """

    __CUSTOMTYPE__ = 'MHYMarker'

    @classmethod
    def create(
            cls, name=None, position=None, marker_root=None):
        """Creates a marker node.

        Args:
            name (str): The marker name.
            position (tuple): The marker positon.
            marker_root (Node): A marker root node to link this marker to.

        Returns:
            MHYMarker: The marker object.
        """
        # get the marker global root
        global_root = _get_global_marker_root()

        # create marker joint
        marker_offset = Node.create('transform', name=NodeName(name, ext='MOFF'))
        marker = cmds.createNode('joint', name=name)
        marker = cls.make_custom_node(marker)
        marker.set_parent(marker_offset)
        marker.drawStyle.value = 2
        marker.radius.channelBox = False

        # create the target transform
        target = marker.add_child(name=name.replace_ext('TGT'))
        for at in ('t', 'tx', 'ty', 'tz', 'r', 'rx', 'ry', 'rz'):
            marker.attr(at).keyable = False
            marker.attr(at).channelBox = True
        global_root.attr(ATTR_AXIS_DISPLAY) >> target.dla

        if name.is_left:
            color_attr = global_root.attr(ATTR_COLOR_L)
        elif name.is_right:
            color_attr = global_root.attr(ATTR_COLOR_R)
        else:
            color_attr = global_root.attr(ATTR_COLOR_M)

        # create marker shape
        name = NodeName(marker)
        xform = Node.create(
            'MHYCtrl', xform=marker, ext='CTRL', shape='sphere', group_exts=None)
        shape = xform.get_shapes()[0]
        scale_attr = global_root.attr(ATTR_MARKER_SCALE)
        for ax in 'XYZ':
            scale_attr >> shape.attr('localScale' + ax)
        global_root.attr(ATTR_MARKER_VIS) >> shape.v
        color_attr >> shape.color

        shape.set_parent(marker)
        xform.delete()
        marker.sync_shape_name()

        # parent to marker root
        if marker_root:
            group = NodeName(marker_root, ext='MGRP')
            if not cmds.objExists(group):
                group = Node.create('transform', name=group, parent=marker_root)
                group.lock()
            marker_offset.set_parent(group)

        # create hierarchy ctrl
        hier_ctrl = Node.create(
            'transform', name=NodeName(name, ext=const.EXT_MARKER_HIER_CTRL))
        xform = Node.create(
            'MHYCtrl', xform=hier_ctrl, ext='CTRL', shape='cube',
            group_exts=None)
        shape = xform.get_shapes()[0]
        global_root.attr(ATTR_HIER_VIS) >> shape.v
        color_attr >> shape.color

        shape.set_parent(hier_ctrl)
        xform.delete()
        hier_ctrl.sync_shape_name()

        group = NodeName(part=global_root, ext='HGRP')
        if not cmds.objExists(group):
            group = Node.create('transform', name=group, parent=global_root)
            group.lock()
        hier_ctrl.set_parent(group)

        # move marker and hier ctrl to position
        if position:
            hier_ctrl.set_translation(position, space='world')
        marker_offset.constrain('parent', hier_ctrl, maintainOffset=False)
        marker_offset.lock()
        marker.add_tag(TAG_HIER_CTRL, hier_ctrl)

        # tag for marking menu support
        marker.add_marking_menu(const.MARKER_MM_NAME, replace=True)
        hier_ctrl.add_marking_menu(const.MARKER_MM_NAME, replace=True)

        marker.lock('sv')
        return marker

    # --- basic properties

    @property
    def aim_axis(self):
        """Returns the aim axis of this marker, if it's aim constraint.

        :type: str or None
        """
        cns = self.get_children(type_='aimConstraint')
        if cns:
            return mmath.vector_to_world_axis(cns[0].get_attr('aimVector'))

    @property
    def up_axis(self):
        """Returns the up axis of this marker, if it's aim constraint.

        :type: str or None
        """
        cns = self.get_children(type_='aimConstraint')
        if cns:
            return mmath.vector_to_world_axis(cns[0].get_attr('upVector'))

    @property
    def target(self):
        """The target transform node to generate the output joint from.

        :type: Transform
        """
        return self.get_children()[0]

    @property
    def is_plane_locked(self):
        """Returns True if this marker is locked to a plane.

        :type: bool
        """
        if NodeName(self.get_parent()).ext != 'MOFF':
            return True
        return False

    @property
    def rotation_type(self):
        """Returns the rotation type of this marker.

        :type: str
        """
        if self.has_attr(ATTR_ROT_TYPE):
            val = self.attr(ATTR_ROT_TYPE).value
            if not val:
                val = None
            return val

    @property
    def is_leaf(self):
        """Returns True if this is a leaf marker in its associated limb.

        :type: bool
        """
        if self.has_attr(ATTR_IS_LEAF):
            return self.attr(ATTR_IS_LEAF).value
        return False

    @property
    def parent_marker(self):
        """The parent marker, or None if not assigned.

        :type: MHYMarker or None
        """
        return self.get_tag(TAG_PARENT_MARKER)

    @property
    def child_markers(self):
        """The child markers.

        :type: [MHYMarker]
        """
        children = []
        for dst in cmds.listConnections(
                '{}.message'.format(self),
                source=False, destination=True, plugs=True) or []:
            if dst.endswith(TAG_PARENT_MARKER):
                children.append(Node(dst.split('.', 1)[0]))
        return children

    @property
    def up_ctrl(self):
        """The up ctrl associated with this marker, or None if not any.

        :type: Transform or None
        """
        return self.get_tag(TAG_UP_CTRL)

    @property
    def hier_ctrl(self):
        """The hierarchy ctrl associated with this marker, or None if not found.

        :type: Transform or None
        """
        if self.has_attr(TAG_HIER_CTRL):
            return self.get_tag(TAG_HIER_CTRL)

    @property
    def marker_root(self):
        """The marker root node, or None if not assigned.

        :type: Transform or None
        """
        roots = []
        for each in cmds.listConnections(
                self.name, source=False, destination=True, plugs=False) or []:
            if each.endswith(const.EXT_MARKER_ROOT):
                if each in self.long_name:
                    return Node(each)
                roots.append(each)

        if roots:
            return Node(roots[0])

    # --- methods

    def _get_sub_root(self, sub_root_ext):
        """Returns a sub-root node for under the marker root,
        creates a new one if not found.

        Args:
            sub_root_ext (str): The sub-root node extension.

        Returns:
            Node: The sub-root node.
        """
        marker_root = self.marker_root
        if not marker_root:
            return

        name = NodeName(marker_root, ext=sub_root_ext)
        if cmds.objExists(name):
            return Node(name)
        sub_root = Node.create('transform', name=name, parent=marker_root)
        sub_root.lock()
        return sub_root

    def get_ids(self, marker_root):
        """Returns this marker's indices (chain index and marker index)
        in a given marker system, or None if not assigned.

        Args:
            marker_root (str): A marker system root node.

        Returns:
            (int, int) or None: The chain index and marker index.
        """
        for each in cmds.listConnections(
                self.name, source=False, destination=True, plugs=True) or []:
            n, attr = each.split('.', 1)
            if n == str(marker_root):
                chain_id, marker_id = attr.split('[', 1)
                chain_id = int(chain_id[-1])
                marker_id = int(marker_id[:-1])
                return chain_id, marker_id

    def connect_parent_marker(self, parent_marker):
        """Connects this marker to a given parent marker.
        The connection is formed via a parent tag.
        A line annotaion is also drawn between them.

        Args:
            parent_marker (MHYMarker): The parent marker.

        Returns:
            None
        """
        if parent_marker != self.parent_marker:
            if self.parent_marker is not None:
                self.disconnect_parent_marker()

            display_type = 'reference'
            if not parent_marker.is_child_of(self.marker_root):
                display_type = 'template'
            parent_marker.add_annotation(self, display_type=display_type)
            if self.has_attr(TAG_PARENT_MARKER):
                self.delete_attr(TAG_PARENT_MARKER)
            self.add_tag(TAG_PARENT_MARKER, parent_marker)
            self.hier_ctrl.set_parent(parent_marker.hier_ctrl)

    def disconnect_parent_marker(self):
        """Disconnects this marker to from the current parent marker.

        Returns:
            None
        """
        parent_marker = self.parent_marker
        if not parent_marker:
            return

        # delete parent annotation shape
        for ann in parent_marker.get_shapes(exact_type='annotationShape'):
            loc = cmds.listConnections(
                ann, source=True, destination=False, plugs=False,
                type='locator')
            if loc and loc[0] == self.name:
                cmds.delete(ann)

        if self.has_attr(TAG_PARENT_MARKER):
            self.delete_attr(TAG_PARENT_MARKER)
        group = self._get_sub_root('HGRP')
        if group:
            self.hier_ctrl.set_parent(group)

    def connect_marker_root(self, marker_root, chain_id, marker_id):
        """Connects ths marker to a given marker root.

        Args:
            marker_root (Transform): The marker root to connect to.
            chain_id (int): The chain id.
            markrer_id (int): The marker id in the specified chain.

        Returns:
            None
        """
        marker_attr = ATTR_MARKER_CHAIN + str(chain_id)
        if not marker_root.has_attr(marker_attr):
            marker_root.add_attr('message', name=marker_attr, multi=True)
        cmds.connectAttr(
            '{}.message'.format(self),
            '{}.{}[{}]'.format(marker_root, marker_attr, marker_id))
        # self.message >> marker_attr[marker_id]

    def delete_hier_ctrl(self):
        """Removes the hier ctrl associated with this marker.

        Returns:
            None
        """
        hier_ctrl = self.hier_ctrl
        if not hier_ctrl:
            return
        parent = hier_ctrl.get_parent()
        for c in hier_ctrl.get_children(type_='transform'):
            c.set_parent(parent)
        off = self.get_parent()
        self.set_parent(off.get_parent())
        hier_ctrl.delete()
        self.delete_attr(TAG_HIER_CTRL)

    def update_hier_ctrl_shape(self):
        """Updates the hierarchy ctrl shape."""
        hier_ctrl = self.hier_ctrl
        if not hier_ctrl:
            return

        global_root = _get_global_marker_root()
        marker_scale = global_root.attr(ATTR_MARKER_SCALE).value
        marker_scale *= HIER_CTRL_SIZE_MULT
        if marker_scale < .2:
            marker_scale = .2

        aim_axis = self.aim_axis
        children = self.child_markers
        shape = hier_ctrl.get_shapes(type_='mhyController')[0]
        shape.localPosition.value = (0, 0, 0)
        if aim_axis and children:
            aa = aim_axis[-1].upper()
            other_axis = 'XYZ'.replace(aa, '')
            pos = mmath.get_position_center(children, as_tuple=False)
            dist = mmath.distance(self, pos) / 2 * .9
            shape.attr('localPosition' + aa).value = -dist \
                if aim_axis.startswith('-') else dist
            shape.attr('localScale' + aa).value = dist
            for ax in other_axis:
                shape.attr('localScale' + ax).value = marker_scale
        else:
            for ax in 'XYZ':
                shape.attr('localScale' + ax).value = marker_scale


def _get_global_marker_root():
    """Returns the global marker system root node,
    create a new one if not exist.

    Returns:
        Transform: The global marker root node.
    """
    if cmds.objExists(const.MARKER_ROOT):
        return Node(const.MARKER_ROOT)

    marker_root = Node.create('transform', name=const.MARKER_ROOT)

    # add setting attrs
    marker_root.add_separator_attr(name='settings')
    attr = marker_root.add_attr(
        'float', name=ATTR_MARKER_SCALE,
        defaultValue=DEFAULT_MARKER_SCALE, minValue=0, maxValue=10)
    attr.channelBox = True

    enums = const.ROT_ORDERS
    attr = marker_root.add_attr(
        'enum', name=ATTR_ROT_ORDER, enumName=':'.join(enums))
    attr.channelBox = True

    # add vis attrs
    marker_root.add_separator_attr(name='vis')
    for name, dv in zip(
            (ATTR_AXIS_DISPLAY, ATTR_MARKER_VIS, ATTR_HIER_VIS),
            (DEFAULT_AXIS_DISPLAY, DEFAULT_MARKER_VIS, DEFAULT_HIER_VIS)):
        attr = marker_root.add_attr('bool', name=name, defaultValue=dv)
        attr.channelBox = True

    # add color attrs
    for name, dv in zip(
            (ATTR_COLOR_M, ATTR_COLOR_L, ATTR_COLOR_R),
            (DEFAULT_COLOR_M, DEFAULT_COLOR_L, DEFAULT_COLOR_R)):
        attr = marker_root.add_color_attr(name=name, defaultValue=dv)
        attr.channelBox = True

    # create shape
    ctrl = Node.create(
        'MHYCtrl', name='tmp_CTRL', shape='cube', group_exts=None)
    marker_root.attr(ATTR_COLOR_M) >> ctrl.shape.color
    ctrl.shape.set_parent(marker_root)
    ctrl.delete()

    marker_root.add_marking_menu(const.MARKER_MM_NAME, replace=True)
    return marker_root


'''
def _create_up_offset_attr(marker, aim_attr):
    """Creates an up offset attribute on a given marker.

    Args:
        marker (Joint): A marker joint node.
        aim_attr (Attribute): A aim attribute to switch driven rotation
            axis.

    Returns:
        None
    """
    if not marker.has_attr(ATTR_UP_OFF):
        up_off_attr = marker.add_attr('doubleAngle', name=ATTR_UP_OFF)
        up_off_attr.channelBox = True
    else:
        up_off_attr = marker.attr(ATTR_UP_OFF)

    # connect to offset attr
    offset = marker.get_children(type_='transform')[0]
    for ax, ids in zip('xyz', ((0, 1), (2, 3), (4, 5))):
        choice = Node.create('choice', name=NodeName(offset, ext='CH' + ax))
        aim_attr >> choice.selector
        for i in range(6):
            if i in ids:
                up_off_attr >> choice.input[i]
            else:
                choice.set_attr('input[{}]'.format(i), 0)
        choice.output >> offset.attr('r' + ax)
'''
