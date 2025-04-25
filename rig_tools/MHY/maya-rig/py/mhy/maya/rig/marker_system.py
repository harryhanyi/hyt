"""
Rigging marker system API
"""

import random
from collections import OrderedDict

from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.utils as mutil
import mhy.maya.nodezoo.utils as nutil
import mhy.maya.maya_math as mmath

import mhy.maya.rig.utils as utils
import mhy.maya.rig.constants as const
import mhy.maya.rig.node.marker as _marker


__all__ = ['MarkerSystem']


AXIS_ENUMS = ('x', '-x', 'y', '-y', 'z', '-z')

ATTR_AIM = 'aim_axis'
ATTR_UP = 'up_axis'
DEFAULT_AIM_VALUE = 0
DEFAULT_UP_VALUE = 4
DEFAULT_COLOR_UP = (.7, .7, .7)

TAG_PARENT_MS = 'parent_marker_system'


class MarkerSystem(object):
    """A class interfacing rigging marker systems.

    A marker system contains a series of markers that allows
    the user to defined articulation points on a character.

    A marker system is constructed with a list of dict containing
    developer-defined marker chains. The top-level list can be
    skipped for single-chain markers.

    Here's a 2-chain marker system example:

    .. code-block:: json

        marker_data = [
                {
                    'aim_axis': 'x',
                    'up_axis': 'z',
                    'parent': None,
                    'markers': [
                        {
                            'name': 'markerA',
                            'position': (0, 0, 0),
                            'rotation': 'aim',
                            'up_type': 'ctrl'
                        },
                        {
                            'name': 'markerB',
                            'position': (1, 0, 0),
                            'rotation': None
                        },
                        {
                            'name': 'markerC',
                            'position': (2, 0, 0),
                            'rotation': 'parent',
                        }]
                },
                {
                    'parent': 'markerB',
                    'markers': [
                        {
                            'name': 'markerD',
                            'position': (3, 0, 0),
                            'rotation': 'parent',
                        }]
                }]

    Chain-level Settings:
        + aim_axis (str)
            Default aim axis for aim constraint markers.
            Valid values: "x", "y", "z", "-x", "-y", "-z".
        + up_axis (str)
            Default up axis for aim constraint markers.
            Valid values: "x", "y", "z", "-x", "-y", "-z".
        + up_ctrl_position (tuple)
            Position of the up ctrl shared by all markers in this chain.
            **ONLY** used when marker's "up_type" is "ctrl".
            Valid values: "x", "y", "z", "-x", "-y", "-z"
        + line_ids (tuple)
            2 indices defining a line in this chain. All markers
            inbetween will be constraint to the line.
            Default is (0, -1) - the first and last marekr in this chain.
        + plane_ids (tuple)
            2 indices defining the plane to constrain all markers with
            "aim" as rotation and "plane" as up_type.
            Default is (0, -1) - the first and last marekr in this chain.
        + parent (str)
            A parent marker to parent the root marker to.
        + markers (list)
            A list of dict defining each marker in this chain.

    Marker-level Settings:
        + name (str)
            Manatory marker name. The ext token **MUST** be const.EXT_MARKER.
        + position (tuple)
            The marker position. Default: (0, 0, 0)
        + rotation (tuple or str)
            The rotation value or rotation constraint method.

            + None (Default): No constraint. Rotate channels won't be locked.
            + (float, float, float): Rotation value in world space. Rotate
              attributes won't be locked after values are applied.
            + "aim": Aim constraint to the child marker.
            + "parent": orient constraint to the parent marker.
              usually used on leaf joints.
            + "NODE_NAME": orient constraint to a specific node.
        + up_type (str)
            The up axis's aim type (Only used if rotation is set to "aim").

            + None (Default): use aim constraint type "none", which interpolates
              up axis in parent space.
            + (float, float, float): A specific vector to align the up axis to.
            + "ctrl" - Makes a shared up vector ctrl and aim the up axis to it.
            + "plane" - Constraint the up axis to a plane defined by 2 markers
              and a up ctrl. The 2 markers are defined by the "plane_ids"
              in chain-level settings.
    """

    def __init__(self, root):
        """Initializes a marker system object from a root node.

        Args:
            root (str or Transform): A marker system root node.
        """
        if NodeName.is_valid(root):
            name = NodeName(root)
            if name.ext == const.EXT_MARKER_ROOT:
                self.__root = Node(root)
                return
        raise ValueError('{} is not a marker root node.'.format(root))

    def __repr__(self):
        return self.__root.name

    __str__ = __repr__

    # --- basic properties

    @property
    def root(self):
        """The root node of this marker system.

        :type: Transform
        """
        return self.__root

    # --- marker system creation

    @classmethod
    def marker_root_name(cls, part, side):
        """Given a part and a side token, returns a proper marker root name,

        Args:
            part (str): The limb's part token.
            side (str): The limb's side token.

        Returns:
           str: The marker root name.
        """
        return NodeName(
            part=part, desc=None, side=side, ext=const.EXT_MARKER_ROOT)

    @classmethod
    def create_marker_root(cls, part, side, force=False):
        """Creates the root node for this marker system.

        Args:
            part (str): The limb's part token.
            side (str): The limb's side token.
            force (bool): If True, existing marker system is deleted
                before creating a new one.

        Returns:
            Transform: The marker root node.

        Raises:
            RuntimeError: If a marker system already exists and force is False.
        """
        root_name = cls.marker_root_name(part, side)
        if cmds.objExists(root_name):
            if force:
                cmds.delete(root_name)
            else:
                raise RuntimeError(
                    'Marker system already exists: {}'.format(root_name))

        global_root = _marker._get_global_marker_root()
        root = Node.create('transform', name=root_name, parent=global_root)
        root.lock('trs')
        return root

    @classmethod
    def create(cls, part, side, marker_data, force=False):
        """Creates a marker system.

        Args:
            part (str): The limb's part token.
            side (str): The limb's side token.
            marker_data (dict): Marker data dict.
                see class docstring for details.
            parent_marker_system (MarkerSystem): The parent marker system to
                connect this marker system to.
            force (bool): If True, delete existing marker system before
                creating a new one.

        Returns:
            MarkerSystem: The created marker system object.
        """
        if not isinstance(marker_data, (list, tuple)):
            marker_data = [marker_data]

        # create marker root node
        ms = cls(cls.create_marker_root(part, side, force=force))

        marker_dict = {}
        for chain_id, chain_data in enumerate(marker_data):
            # get default chain attrs
            aim_axis = chain_data.get('aim_axis')
            up_axis = chain_data.get('up_axis')
            up_ctrl_pos = chain_data.get('up_ctrl_position')
            p_start, p_end = chain_data.get('plane_ids', (0, -1))
            line_ids = chain_data.get('line_ids')

            # find the chain parent
            chain_parent = chain_data.get('parent')
            if chain_parent:
                chain_parent = marker_dict.get(chain_parent)

            markers = []
            for marker_id, marker_data in enumerate(chain_data['markers']):
                name = NodeName(marker_data['name'], ext=const.EXT_MARKER)
                if cmds.objExists(name):
                    raise RuntimeError('Marker already exists: '.format(name))

                # get parent marker
                pmarker = None
                if marker_id > 0:
                    pmarker = markers[-1]
                elif chain_parent:
                    pmarker = chain_parent

                # create the marker joint
                marker = Node.create(
                    'MHYMarker',
                    name=name,
                    position=marker_data.get('position'),
                    marker_root=ms.root)

                # connect to parent marker
                marker.connect_marker_root(ms.root, chain_id, marker_id)
                # conenct parent marker
                if pmarker and pmarker != marker:
                    marker.connect_parent_marker(pmarker)

                markers.append(marker)
                marker_dict[name] = marker

            # constrain markers
            chain_up_ctrl = None
            chain_up_object = None
            plane_up_ctrl = None
            plane_rev_node = None
            for marker_id, marker in enumerate(markers):
                marker_data = chain_data['markers'][marker_id]

                # position constraint
                #
                pos_locked = False
                if line_ids:
                    start_marker = markers[line_ids[0]]
                    start_id = markers.index(start_marker)
                    end_marker = markers[line_ids[1]]
                    end_id = markers.index(end_marker)
                    if marker_id > start_id and marker_id < end_id:
                        _create_line_constraint(
                            marker, start_marker, end_marker)
                        pos_locked = True

                # rotation constraint
                #
                rotation = marker_data.get('rotation')
                up_type = marker_data.get('up_type')
                # if this is the last marker... aim is not gonna work.
                # switch to 'parent' rotation.
                if rotation == 'aim' and marker_id == len(markers) - 1:
                    rotation = 'parent'

                # embed marker data
                attr = marker.add_attr('string', name=_marker.ATTR_ROT_TYPE)
                if rotation:
                    attr.value = rotation
                attr = marker.add_attr(
                    'bool', name=_marker.ATTR_IS_LEAF, defaultValue=False)
                if not marker.child_markers:
                    attr.value = True

                # aim constraint
                if rotation == 'aim':
                    if len(markers) <= 1:
                        raise RuntimeError(
                            ('Cannot aim constraint marker {}. '
                             'It is the only marker '
                             'in the chain').format(marker))

                    driven = marker.get_parent() if pos_locked else None

                    # aim constraint with up vector locked to the pole vector
                    if up_type == 'plane':
                        if not plane_up_ctrl:
                            nodes = _create_marker_plane(
                                markers, p_start, p_end, aim_axis, up_axis)
                            plane_up_ctrl, plane_rev_node = nodes

                        if marker_id in (p_start, p_end):
                            _marker_aim_constrain(
                                marker, markers[marker_id + 1],
                                driven=driven,
                                up_object=plane_up_ctrl,
                                use_up_object_rot=False,
                                default_aim_axis=aim_axis,
                                default_up_axis=up_axis)
                        else:
                            marker.delete_hier_ctrl()
                            marker.set_parent(plane_rev_node)
                            _marker_aim_constrain(
                                marker, markers[marker_id + 1],
                                driven=driven,
                                default_aim_axis=aim_axis,
                                default_up_axis=up_axis)
                            _create_marker_plane_sdk(marker)
                        marker.add_tag(_marker.TAG_UP_CTRL, plane_up_ctrl)

                    # aim constraint with up vector locked to a up ctrl
                    elif up_type == 'ctrl':
                        if not chain_up_object:
                            nodes = _create_up_ctrl(
                                markers[0], up_ctrl_pos)
                            chain_up_ctrl, chain_up_object = nodes

                        _marker_aim_constrain(
                            marker, markers[marker_id + 1],
                            driven=driven,
                            up_object=chain_up_object,
                            use_up_object_rot=True,
                            default_aim_axis=aim_axis,
                            default_up_axis=up_axis)
                        marker.add_tag(_marker.TAG_UP_CTRL, chain_up_ctrl)

                    # aim constraint with no up vector
                    elif up_type is None:
                        _marker_aim_constrain(
                            marker, markers[marker_id + 1],
                            driven=driven,
                            default_aim_axis=aim_axis,
                            default_up_axis=up_axis)

                    # aim constraint with a specific up vector
                    elif isinstance(up_type, (list, tuple)):
                        _marker_aim_constrain(
                            marker, markers[marker_id + 1],
                            driven=driven,
                            up_vector=up_type,
                            default_aim_axis=aim_axis,
                            default_up_axis=up_axis)
                    else:
                        raise RuntimeError(
                            'Invalid up type {} - {}'.format(marker, up_type))

                    if pos_locked and rotation == 'aim' and up_type != 'plane':
                        _create_marker_line_sdk(marker)

                    marker.lock('r')

                # use user-specified rotation
                elif isinstance(rotation, (list, tuple)):
                    marker.set_rotation(rotation, space='world')

                # use parent's orientation
                elif rotation == 'parent':
                    parent = marker.parent_marker
                    if not parent:
                        raise RuntimeError(
                            'Marker {} has no parent.'.format(marker))
                    marker.constrain(
                        'orient', parent, maintainOffset=False)

                    # skip locking leaf marker's rotation,
                    # as it breaks marker connection undo...
                    if not marker.is_leaf:
                        marker.lock('r')

                # no orientation constraint
                elif not rotation:
                    pass

                # use a specific node's orientation
                elif cmds.objExists(rotation):
                    marker.constrain(
                        'orient', rotation, maintainOffset=False)
                    marker.lock('r')

                else:
                    raise RuntimeError(
                        'Invalid constraint type {} - {}'.format(
                            marker, rotation))

        _align_hier_ctrls(marker_system=ms)
        return ms

    def __get_chain_attrs(self):
        """Returns a list of chain attributes in this marker system."""
        return ['{}.{}'.format(self.root, x) for x in
                sorted(cmds.listAttr(self.root, userDefined=True) or [])
                if x.startswith(_marker.ATTR_MARKER_CHAIN)]

    @property
    def parent_marker_system(self):
        """The parent marker system or None if not set.

        :type: MarkerSystem or None
        """
        if self.root.has_attr(TAG_PARENT_MS):
            parent = self.root.get_tag(TAG_PARENT_MS)
            if parent:
                return MarkerSystem(parent)

    def get_marker(self, chain_id, marker_id):
        """Returns the marker at the given chain id and marker id.

        Args:
            chain_id (int): The marker chain id.
            marker_id (int): The marker id in the specified chain.

        Returns:
            MHYMarker: The marker node.

        Raises:
            ValueError: If the marker is not found.
        """
        chain_id = int(chain_id)
        marker_id = int(marker_id)

        try:
            attr = self.__get_chain_attrs()[chain_id]
            markers = cmds.listConnections(
                attr,
                source=True,
                destination=False,
                plugs=False)
            return Node(markers[marker_id])
        except BaseException:
            raise ValueError(
                'No marker found at given index: {} - {}'.format(
                    chain_id, marker_id))

    def get_marker_ids(self, marker):
        """Returns the chain id and marker id of a given marker.

        Args:
            marker (MHYMarker): The marker to check.

        Returns:
            (int, int): The marker's chain id and marker id.
            (-1, -1) is returned if the marker is not found.
        """
        marker = Node(marker)
        for i, attr in enumerate(self.__get_chain_attrs()):
            for j, m in enumerate(cmds.listConnections(
                    attr,
                    source=True,
                    destination=False,
                    plugs=False) or []):
                m = Node(m)
                if m == marker:
                    return i, j
        return -1, -1

    def get_parent_marker(self):
        """Returns the parent marker of this marker system.

        Returns:
            MHYMarker or None: The parent marker or None if not set.
        """
        return self.get_marker(0, 0).parent_marker

    def set_parent_marker(
            self, parent_marker, mode=const.MarkerConnectMode.none):
        """Sets the parent marker of this marker system.

        Args:
            parent_marker (MHYMarker or None): The parent marker to connect to.
                If None, disconnets from the current parent marker, if any.
            mode (MarkerConnectMode): The connection mode.

        Returns:
            bool: True if the connection was successful.
        """
        if parent_marker:
            parent_marker = Node(parent_marker)

        # get the parent marker system
        parent_ms = self.parent_marker_system
        if not parent_ms and parent_marker:
            parent_ms_root = parent_marker.marker_root
            self.root.add_tag(TAG_PARENT_MS, parent_ms_root)
            parent_ms = MarkerSystem(parent_ms_root)
            # cmds.warning('Marker system {} does not have a parent.')
            # return False

        # validate the parent marker
        if parent_marker:
            if parent_marker.custom_type_name != 'MHYMarker':
                cmds.warning('{} is not a marker node.'.format(parent_marker))
                return False

            if not parent_marker.is_child_of(parent_ms.root):
                cmds.warning('{} is not under parent marker system {}.'.format(
                    parent_marker, parent_ms))
                return False

        for attr in self.__get_chain_attrs():
            markers = cmds.listConnections(
                attr,
                source=True,
                destination=False,
                plugs=False)

            # only operate on the root markers that are not
            # parented to another marker in the same marker system.
            marker = Node(markers[0])
            parent = marker.parent_marker
            if parent and parent.is_child_of(self.root):
                continue

            # disconnect from the current parent marker
            cur_pm = marker.parent_marker
            marker.disconnect_parent_marker()
            if cur_pm:
                rot_free = False
                unhide_shape = False
                for cns in cur_pm.get_children(type_='constraint'):
                    if cns.type_name in (
                            'pointConstraint',
                            'aimConstraint',
                            'orientConstraint'):
                        target = cmds.listConnections(
                            '{}.target'.format(cns),
                            source=True, destination=False, plugs=False)
                        if target and target[0] == marker.name:
                            # if the parent marker is rotation constraint...
                            # now it get free rotation back.
                            if not rot_free and cns.type_name in (
                                    'aimConstraint',
                                    'orientConstraint'):
                                rot_free = True
                            # if the parent marker is position constraint...
                            # it means it was following this marker
                            if not unhide_shape and \
                               cns.type_name == 'pointConstraint':
                                unhide_shape = True
                            cns.delete()

                # re-create constraint so that the parent marker
                # follows its own parent
                if rot_free and cur_pm.rotation_type == 'parent':
                    driver = cur_pm.parent_marker
                    if driver:
                        cur_pm.constrain('orient', driver, maintainOffset=False)

                # display the parent marker shapes.
                if unhide_shape:
                    shape = cur_pm.get_shapes(exact_type='mhyController')[0]
                    shape.lodVisibility.value = True

            if parent_marker:
                # for non-leaf parent markers, only the default
                # connection is allowed.
                if not parent_marker.is_leaf and \
                   mode != const.MarkerConnectMode.none:
                    cmds.warning(
                        ('Non-leaf parent doesn\'t '
                         'support connection mode "{}"').format(mode))
                    mode = const.MarkerConnectMode.none

                marker.connect_parent_marker(parent_marker)

                # parent marker following this marker
                if mode == const.MarkerConnectMode.follow:
                    # create point constraint
                    cns = parent_marker.get_children(type_='pointConstraint')
                    if cns:
                        cns[0].delete()
                    parent_marker.constrain(
                        'point', marker, maintainOffset=False)

                    # create orient constraint
                    cns = parent_marker.get_children(type_='pointConstraint')
                    if parent_marker.rotation_type in ('parent', None):
                        for t in ('orientConstraint', 'aimConstraint'):
                            cns = parent_marker.get_children(type_=t)
                            if cns:
                                cns[0].delete()
                        parent_marker.constrain(
                            'orient', marker, maintainOffset=False)

                    # hide parent marker shapes
                    shape = parent_marker.get_shapes(
                        exact_type='mhyController')[0]
                    shape.lodVisibility.value = False
                    for shape in parent_marker.get_shapes(
                            exact_type='annotationShape'):
                        target = cmds.listConnections(
                            shape, source=True, destination=False, plugs=False)
                        if target and Node(target[0]).get_parent() == marker:
                            shape.lodVisibility.value = False

                # parent marker aim to this marker
                elif mode == const.MarkerConnectMode.aim:
                    if parent_marker.rotation_type in ('parent', None):
                        for t in ('orientConstraint', 'aimConstraint'):
                            cns = parent_marker.get_children(type_=t)
                            if cns:
                                cns[0].delete()

                        parent_marker.constrain(
                            'aim', marker,
                            aimVector=(1, 0, 0),
                            upVector=(0, 0, 1),
                            worldUpVector=(0, 0, 1),
                            worldUpType='objectrotation',
                            worldUpObject=marker,
                            maintainOffset=False)
                    else:
                        cmds.warning(
                            ('"aim" marker connection mode only works for '
                             'markers with "parent" or None rotation modes.'
                             '{}\'s rotation mode is {}').format(
                                 parent_marker, parent_marker.rotation_type))
                        return False

        return True

    def get_marker_connect_mode(self):
        """Returns the marker connection mode.

        Returns:
            MarkerConnectMode or None
        """
        markers = set(self.iter_markers())
        parent_marker = self.get_parent_marker()
        if parent_marker:
            for cns in parent_marker.get_children(type_='constraint'):
                target = cmds.listConnections(
                    '{}.target'.format(cns),
                    source=True, destination=False, plugs=False)
                if target:
                    target = Node(target[0])
                    if target in markers:
                        if cns.type_name == 'pointConstraint':
                            return const.MarkerConnectMode.follow
                        if cns.type_name == 'aimConstraint':
                            return const.MarkerConnectMode.aim
            return const.MarkerConnectMode.none

    def iter_markers(self, plane_marker_last=False):
        """Iterates through all markers and ctrls.

        Args:
            plane_marker_last (bool): If True, yield plane locked markers last.

        Yields:
            Transform: each marker transform node.
        """
        plane_markers = []
        for marker_attr in self.__get_chain_attrs():
            for each in cmds.listConnections(
                    marker_attr,
                    source=True,
                    destination=False,
                    plugs=False) or []:

                marker = Node(each)
                if plane_marker_last and marker.is_plane_locked:
                    plane_markers.append(marker)
                    continue

                yield marker

        for marker in plane_markers:
            yield marker

    def mirror(self, align_hier=True):
        """Mirrors this marker system across world x axis.

        Args:
            align_hier (bool): If True, align hierarchy ctrls after mirroring.

        Returns:
            None
        """
        # mirror aim axis
        m_root = NodeName(self.root).flip()
        if m_root.is_middle:
            return

        if cmds.objExists(m_root):
            m_marker_sys = MarkerSystem(m_root)
            for attr_name in (ATTR_AIM, ATTR_UP):
                if m_marker_sys.root.has_attr(attr_name):
                    axis = self.root.attr(attr_name).enum_value
                    attr = m_marker_sys.root.attr(attr_name)
                    # attr.locked = False
                    if len(axis) == 2:
                        attr.value = axis[-1]
                    else:
                        attr.value = '-' + axis
                    # attr.locked = True
        else:
            m_marker_sys = None

        # mirror markers
        up_ctrls = set()
        markers = list(self.iter_markers(plane_marker_last=True))
        for marker in markers:
            if marker.up_ctrl:
                up_ctrls.add(marker.up_ctrl)

        for node in markers + list(up_ctrls):
            tnode = NodeName(node).flip()
            if not cmds.objExists(tnode):
                continue
            tnode = Node(tnode)

            # mirror positions
            pos = list(node.get_translation(space='world'))
            pos[0] *= -1
            tnode.set_translation(pos, space='world')

            # mirror rotation
            if tnode.rx.is_free_to_change:
                # TODO dont use tmp joints
                tmp_root = Node.create('joint', clear_selection=True)
                tmp_joint = Node.create(
                    'joint', name='tmp_L_JNT', clear_selection=True)
                tmp_joint.set_parent(tmp_root)
                tmp_joint.set_matrix(node.get_matrix('world'))
                tmp_joint.make_identity(apply=True, rotate=True, scale=True)
                cmds.mirrorJoint(
                    tmp_joint,
                    mirrorBehavior=True,
                    mirrorYZ=True,
                    searchReplace=('_L_', '_R_'))

                rot = Node('tmp_R_JNT').get_rotation(space='world')
                tnode.set_rotation(rot, space='world')
                cmds.delete(tmp_root, tmp_joint)

            # mirror scale
            if tnode.sx.is_free_to_change:
                tnode.set_attr('s', node.get_attr('s'))

            # mirror other attr
            for attr in (_marker.ATTR_UP_OFF, _marker.ATTR_POLE_DIST):
                if node.has_attr(attr) and tnode.has_attr(attr):
                    tnode.attr(attr).value = node.attr(attr).value

        if m_marker_sys:
            # mirror parent
            parent_marker = self.get_parent_marker()
            if parent_marker:
                mode = self.get_marker_connect_mode()
                mp = NodeName(parent_marker).flip()
                if cmds.objExists(mp):
                    m_marker_sys.set_parent_marker(mp, mode=mode)
            else:
                m_marker_sys.set_parent_marker(None)

            # align hier ctrls
            if align_hier:
                _align_hier_ctrls(marker_system=m_marker_sys)

    def is_line_colored(self):
        """Checks if the annotation lines in this marker system are colored."""
        for ann in self.root.list_relatives(
                allDescendents=True, type='annotationShape') or []:
            return ann.overrideDisplayType.value == 0
        return False

    def set_line_colored(self, state):
        """Sets the colored state of the annotation lines."""
        for ann in self.root.list_relatives(
                allDescendents=True, type='annotationShape') or []:
            target_marker = cmds.listConnections(
                ann, source=True, destination=False, plugs=False)
            if target_marker:
                target_marker = Node(target_marker[0])
                if not target_marker.is_child_of(self.root):
                    continue

            ann.overrideEnabled.value = True
            if state:
                ann.overrideDisplayType.value = 0
                ann.overrideRGBColors.value = True
                name = NodeName(self.root)
                seed = name.part

                random.seed(seed)
                color = [0, 0, 0]
                for i in range(3):
                    random.seed(seed + str(i))
                    if random.randint(0, 1):
                        color[i] = .9
                ann.overrideColorRGB.value = color
            else:
                ann.overrideDisplayType.value = 2

    # --- output skeleton

    def build_skeleton(self, parent=None):
        """Generates a skeleton from this marker system.

        Args:
            parent (Transform): A transform to parent the skeleton to.
                Ignored if the marker already has a parent tag.

        Returns:
            list: A list of list containing joints in each marker chain.
            The order of this list matches the marker data used to
            create this marker.
        """
        joints = []
        root = _marker._get_global_marker_root()
        if root:
            rotate_order = root.attr(_marker.ATTR_ROT_ORDER).value
        else:
            rotate_order = None

        for marker in self.iter_markers():
            joint = NodeName(marker, ext=const.EXT_RIG_JOINT)
            if cmds.objExists(joint):
                raise RuntimeError(
                    'Joint {} already exists'.format(joint))

            joint = Node.create(
                'joint',
                name=NodeName(marker, ext=const.EXT_RIG_JOINT),
                clear_selection=True)
            if rotate_order is not None:
                joint.rotateOrder.value = rotate_order
            mtx = marker.target.get_matrix(space='world')
            joint.set_matrix(mtx, space='world')
            joint_parent = marker.parent_marker
            if not joint_parent:
                joint_parent = parent
            else:
                joint_parent = NodeName(
                    joint_parent, ext=const.EXT_RIG_JOINT)

            if joint_parent:
                joint.set_parent(joint_parent)
            joint.make_identity(apply=True, rotate=True, scale=True)

            chain_id, _ = marker.get_ids(self.root)
            if chain_id > len(joints) - 1:
                joints.append([])
            joints[chain_id].append(joint)

        return joints


# --- marker util functions


def _get_root_axis_attr(marker_root, attr_name, default=None, _create=True):
    """Returns the requested axis attribute on a marker root
    node. Optionally, creates the attribute if not found.

    Args:
        marker_root (str or Transform): The marker root node.
        attr_name (str): An axis attribute name.
        default (str): The default value.
            Valid values are "x", "y", "z", "-x", "-y", "-z".

    Returns:
        Attribute: The axis attr.
    """
    if not default:
        if attr_name == ATTR_AIM:
            default = DEFAULT_AIM_VALUE
        else:
            default = DEFAULT_UP_VALUE

    if not marker_root.has_attr(attr_name):
        if _create:
            attr = marker_root.add_attr(
                'enum', name=attr_name, enumName=':'.join(AXIS_ENUMS),
                keyable=False, defaultValue=default)
            # locking axis attrs breaks marker system mirroring undo
            # attr.locked = True
            attr.channelBox = True
            return attr
    else:
        return marker_root.attr(attr_name)


def _marker_aim_constrain(
        marker, driver, driven=None,
        up_object=None, use_up_object_rot=False, up_vector=None,
        default_aim_axis=None, default_up_axis=None):
    """Aim constrains a marker node.

    Args:
        marker (MHYMarker): A marker node to work with.
        driver (Transform): The driver transform node.
        driven (Transform): The driven transform node.
            If None, use the marker as driven.
        up_object (Transform): The up object used in the aim constraint.
        use_up_object_rot (bool): If True, use up object's rotation
            to aim.
        up_vector (list): If provided, use this upvector directly
            in the aim constraint.
        default_aim_axis (str): The default aim axis.
        default_up_axis (str): The default up axis.

    Returns:
        AimConstraint: The constraint node.
    """
    if not driven:
        driven = marker

    if not default_aim_axis:
        default_aim_axis = DEFAULT_AIM_VALUE
    if not default_up_axis:
        default_up_axis = DEFAULT_UP_VALUE

    marker_root = marker.marker_root
    aim_attr = _get_root_axis_attr(
        marker_root, ATTR_AIM, default=default_aim_axis)
    up_attr = _get_root_axis_attr(
        marker_root, ATTR_UP, default=default_up_axis)

    group = None
    if marker_root:
        group = NodeName(marker_root, ext='REFGRP')
        if not cmds.objExists(group):
            group = Node.create('transform', name=group, parent=marker_root)
            group.lock()

    # aim constraint with specific up vector
    if up_vector:
        cns = driven.constrain(
            'aim', driver,
            aimVector=(1, 0, 0),
            upVector=(0, 0, 1),
            worldUpType='vector',
            maintainOffset=False)
        cns.worldUpVector.value = up_vector

    # aim constraint with up axis pointing to the up object
    elif up_object and not use_up_object_rot:
        cns = driven.constrain(
            'aim', driver,
            aimVector=(1, 0, 0),
            upVector=(0, 0, 1),
            worldUpType='object',
            worldUpObject=up_object,
            maintainOffset=False)

    # aim constraint with up object
    elif up_object:
        cns = driven.constrain(
            'aim', driver,
            aimVector=(1, 0, 0),
            upVector=(0, 0, 1),
            worldUpType='objectrotation',
            worldUpObject=up_object,
            worldUpVector=(1, 0, 0),
            maintainOffset=False)
        # _create_up_offset_attr(driven, aim_attr)

    # aim constraint with no worldUpType
    else:
        cns = driven.constrain(
            'aim', driver,
            aimVector=(1, 0, 0),
            upVector=(0, 0, 1),
            worldUpType='none',
            maintainOffset=False)
        # _create_up_offset_attr(driven, aim_attr)

    # connect to aim axis attr and up axis attr
    for attr, cns_name in zip(
            (aim_attr, up_attr),
            ('aim', 'up')):
        for i, axis in enumerate(AXIS_ENUMS):
            vec = mmath.world_axis_to_vector(axis)
            for j, ax in enumerate('XYZ'):
                driven_attr = cns.attr('{}Vector{}'.format(cns_name, ax))
                utils.set_driven_keys(
                    attr,
                    driven_attr,
                    [[i, vec[j]]],
                    in_tangent_type='flat',
                    out_tangent_type='flat')

    return cns


def _create_up_ctrl(marker, up_ctrl_pos=None):
    """Creates an up ctrl and and up object for a given marker.

    Args:
        marker (MHYMarker): A marker node to work with.
        up_ctrl_pos (tuple): The position of the up ctrl.
            If None, move the up ctrl for 5 units in Z.

    Returns:
        tuple: (up_ctrl, up_object)
    """
    ref_group = marker._get_sub_root('REFGRP')

    name = NodeName(marker.name)
    up_ctrl = Node.create(
        'MHYCtrl', shape='sphere', group_exts=['PLC'],
        name=NodeName(name, num=None, ext=const.EXT_MARKER_UP_CTRL))
    plc = up_ctrl.plc_node
    plc.parent_align(marker)
    plc.set_parent(marker.get_parent())
    plc.constrain('parent', marker.hier_ctrl, maintainOffset=False)

    up_ctrl.shape.shape_color = DEFAULT_COLOR_UP
    root = _marker._get_global_marker_root()
    scale_attr = root.attr(_marker.ATTR_MARKER_SCALE)
    for ax in 'XYZ':
        scale_attr >> up_ctrl.shape.attr('localScale' + ax)
    plc.lock()
    up_ctrl.lock('rsv')
    up_ctrl.add_annotation(marker, text='^', display_type='reference')

    if up_ctrl_pos:
        up_ctrl.set_translation(up_ctrl_pos, space='world')
    else:
        up_ctrl.tz.value = 5

    up_object = Node.create(
        'transform', name=NodeName(up_ctrl, ext='UP'), parent=ref_group)
    up_object.constrain('point', marker, maintainOffset=False)
    up_object.constrain(
        'aim', up_ctrl, aimVector=(1, 0, 0), upVector=(0, 0, 1),
        worldUpType='none', maintainOffset=False)

    up_ctrl.add_marking_menu(const.MARKER_MM_NAME, replace=True)
    return up_ctrl, up_object


def _create_marker_plane(
        markers, start_id, end_id,
        default_aim_axis=None, default_up_axis=None):
    """Creates a plane setup from a list of markers,
    the plane is defined by the start marker, end marker,
    and the center point of all the inbetween markers.

    Args:
        markers (list): A list of markers to create the plane from.
        start_id (int): Index fo the plane start marker.
        end_id (int): Index fo the plane end marker.
        default_aim_axis (str): The default aim axis.
            Used to constrain the revolve node.
        default_up_axis (str): The default up axis.
            Used to constrain the revolve node.

    Returns:
        tuple: (up_ctrl, revolve_node)
    """
    # validate start and end ids
    if end_id < 0:
        end_id = len(markers) + end_id
    elif end_id > len(markers) - 1:
        end_id = len(markers) - 1

    if start_id < 0:
        start_id = 0
    if end_id < 0:
        end_id = 0

    if end_id in (start_id, start_id + 1):
        raise ValueError('Can\'t build marker plane from id {} to id {}'.format(start_id, end_id))

    # get start and end marker
    start_marker = markers[start_id]
    end_marker = markers[end_id]

    # compute the up ctrl position
    mid_pos = mmath.get_position_center(
        markers[start_id + 1: end_id], as_tuple=False)
    pa = start_marker.get_translation(space='world', as_tuple=False)
    va = (mid_pos - pa).normal()
    pb = end_marker.get_translation(space='world', as_tuple=False)
    vb = (mid_pos - pb).normal()
    length = (pa - pb).length() * .3
    ctrl_pos = ((pa + pb) * .5) + ((va + vb) * .5).normal() * length

    # create the up ctrl
    up_ctrl = Node.create(
        'MHYCtrl', shape='sphere', group_exts=['PLC'],
        name=NodeName(start_marker, num=None, ext=const.EXT_MARKER_UP_CTRL))
    plc = up_ctrl.plc_node
    plc.parent_align(start_marker)
    up_ctrl.set_translation(ctrl_pos, space='world')
    plc.set_parent(start_marker.get_parent())
    plc.constrain('parent', start_marker.hier_ctrl, maintainOffset=False)

    up_ctrl.shape.shape_color = DEFAULT_COLOR_UP
    root = _marker._get_global_marker_root()
    scale_attr = root.attr(_marker.ATTR_MARKER_SCALE)
    for ax in 'XYZ':
        scale_attr >> up_ctrl.shape.attr('localScale' + ax)
    up_ctrl.lock('rsv')
    up_ctrl.add_annotation(start_marker, display_type='reference')
    up_ctrl.add_annotation(end_marker, display_type='reference')

    # create a node that revolves around the line between start and end markers
    rev_node = Node.create(
        'transform', name=NodeName(start_marker, ext='REV'),
        parent=start_marker.get_parent().get_parent())
    rev_node.constrain('point', start_marker, end_marker, maintainOffset=False)

    # aim constrain the revolve node to look at the up ctrl
    if not default_aim_axis:
        default_aim_axis = DEFAULT_AIM_VALUE
    if not default_up_axis:
        default_up_axis = DEFAULT_UP_VALUE
    _marker_aim_constrain(
        start_marker, end_marker,
        driven=rev_node,
        up_object=up_ctrl,
        use_up_object_rot=False,
        default_aim_axis=default_aim_axis,
        default_up_axis=default_up_axis)

    up_ctrl.add_marking_menu(const.MARKER_MM_NAME, replace=True)
    return up_ctrl, rev_node


def _create_marker_plane_sdk(marker):
    """Creates a set driven key setup for a given marker,
    So that the marker is locked to a plane.
    """
    # connect to aim axis attr and up axis attr
    root = marker.marker_root
    aim_attr = _get_root_axis_attr(root, ATTR_AIM, _create=False)
    up_attr = _get_root_axis_attr(root, ATTR_UP, _create=False)
    node = aim_attr.node

    # a network to get the third axis (other than aim and up)
    ta_choice = NodeName(node, ext='THIRDAXIS')
    if cmds.objExists(ta_choice):
        ta_choice = Node(ta_choice)
    else:
        # convert aim attr to (0, 1, 2) (X, Y, Z)
        aim_choice = Node.create(
            'choice', name=NodeName(node, ext='AIMAXIS'))
        aim_choice.input[0].value = 0
        aim_choice.input[1].value = 0
        aim_choice.input[2].value = 1
        aim_choice.input[3].value = 1
        aim_choice.input[4].value = 2
        aim_choice.input[5].value = 2
        aim_attr >> aim_choice.selector

        # convert up attr to (0, 1, 2) (X, Y, Z)
        up_choice = Node.create(
            'choice', name=NodeName(node, ext='UPAXIS'))
        up_choice.input[0].value = 0
        up_choice.input[1].value = 0
        up_choice.input[2].value = 1
        up_choice.input[3].value = 1
        up_choice.input[4].value = 2
        up_choice.input[5].value = 2
        up_attr >> up_choice.selector

        mdl = Node.create(
            'multDoubleLinear', name=NodeName(node, ext='TAMDL'))
        aim_choice.output >> mdl.input1
        up_choice.output >> mdl.input2

        pma = Node.create(
            'plusMinusAverage', name=NodeName(node, ext='TAPMA'))
        aim_choice.output >> pma.input1D[0]
        up_choice.output >> pma.input1D[1]
        mdl.output >> pma.input1D[2]

        # the final third axis output
        ta_choice = Node.create(
            'choice', name=NodeName(node, ext='THIRDAXIS'))
        # (0, 0) = (aimX, upX) = Y
        ta_choice.input[0].value = 1
        # (0, 1) = (aimX, upY) = Z
        ta_choice.input[1].value = 2
        # (0, 2) = (aimX, upZ) = Y
        ta_choice.input[2].value = 1
        # (1, 1) = (aimY, upY) = X
        ta_choice.input[3].value = 0
        # (1, 2) = (aimY, upZ) = X
        ta_choice.input[5].value = 0
        # (2, 2) = (aimZ, upZ) = X
        ta_choice.input[8].value = 0
        pma.output1D >> ta_choice.selector

    for attr in ('minTransLimit', 'maxTransLimit'):
        marker.attr(attr).value = (0, 0, 0)

    for attr in ('minTransLimitEnable', 'maxTransLimitEnable'):
        tokens = list(attr.split('Limit'))
        tokens[1] = 'Limit' + tokens[1]

        for axis in 'XYZ':
            driven_attr = tokens[0] + axis + tokens[1]
            driven_attr = marker.attr(driven_attr)

            for driver_val in range(3):
                ax = 'XYZ'[driver_val]
                driven_val = True if axis == ax else False
                cmds.setDrivenKeyframe(
                    driven_attr,
                    currentDriver=ta_choice.output,
                    driverValue=driver_val,
                    value=driven_val,
                    inTangentType='flat',
                    outTangentType='flat',
                    insertBlend=True)


def _create_marker_line_sdk(marker):
    """Creates a set driven key setup for a given marker,
    So that the marker is locked to a line.
    """
    # connect to aim axis attr and up axis attr
    root = marker.marker_root
    aim_attr = _get_root_axis_attr(root, ATTR_AIM, _create=False)
    node = aim_attr.node

    # a network to get the third axis (other than aim and up)
    aim_choice = NodeName(node, ext='AIMAXIS')
    if cmds.objExists(aim_choice):
        aim_choice = Node(aim_choice)
    else:
        # convert aim attr to (0, 1, 2) (X, Y, Z)
        aim_choice = Node.create(
            'choice', name=NodeName(node, ext='AIMAXIS'))
        aim_choice.input[0].value = 0
        aim_choice.input[1].value = 0
        aim_choice.input[2].value = 1
        aim_choice.input[3].value = 1
        aim_choice.input[4].value = 2
        aim_choice.input[5].value = 2
        aim_attr >> aim_choice.selector

    for attr in ('minTransLimit', 'maxTransLimit'):
        marker.attr(attr).value = (0, 0, 0)

    for attr in ('minTransLimitEnable', 'maxTransLimitEnable'):
        tokens = list(attr.split('Limit'))
        tokens[1] = 'Limit' + tokens[1]

        for axis in 'XYZ':
            driven_attr = tokens[0] + axis + tokens[1]
            driven_attr = marker.attr(driven_attr)

            for driver_val in range(3):
                ax = 'XYZ'[driver_val]
                driven_val = False if axis == ax else True
                cmds.setDrivenKeyframe(
                    driven_attr,
                    currentDriver=aim_choice.output,
                    driverValue=driver_val,
                    value=driven_val,
                    inTangentType='flat',
                    outTangentType='flat',
                    insertBlend=True)


def _create_line_constraint(marker, start_marker, end_marker):
    """Creates a plane setup from a list of markers,
    the plane is defined by the start marker, end marker,
    and the center point of all the inbetween markers.

    Args:
        marker (MHYMarker): The marker to constraint.
        start_marker (MHYMarker): The line start marker.
        end_marker (MHYMarker): The line end marker.

    Returns:
        tuple: (up_ctrl, revolve_node)
    """
    # create a node that is constraint to the line from
    # start marker to end marker.
    proj_point = mmath.project_point(marker, start_marker, end_marker)
    dist_start = mmath.distance(proj_point, start_marker)
    dist_end = mmath.distance(proj_point, end_marker)

    cns_node = Node.create(
        'transform', name=NodeName(marker, ext='CNS'),
        parent=marker.get_parent().get_parent())
    cns_node.align(marker)
    cns = cns_node.constrain(
        'point', start_marker, end_marker, maintainOffset=False)
    attrs = cmds.pointConstraint(cns, query=True, weightAliasList=True)
    cns.attr(attrs[0]).value = dist_end / (dist_start + dist_end)
    cns.attr(attrs[1]).value = dist_start / (dist_start + dist_end)
    marker.delete_hier_ctrl()
    marker.set_parent(cns_node)
    marker.reset('t')
    return cns_node


# --- global util functions


def _get_selected_markers():
    markers = []
    for each in nutil.ls(selection=True, type='transform'):
        if each.custom_type_name == 'MHYMarker':
            markers.append(each)
    return markers


@mutil.undoable
@mutil.restore_selection
def _connect_marker_system(mode=const.MarkerConnectMode.none):
    sel = _get_selected_markers()
    if len(sel) != 2:
        cmds.warning('must select a marker and a parent marker in order.')
        return
    parent_marker, marker = sel

    root = marker.marker_root
    marker_sys = MarkerSystem(root)
    if marker_sys.set_parent_marker(parent_marker, mode=mode):
        OpenMaya.MGlobal.displayInfo(
            'Connected marker system {} -> {}'.format(root, parent_marker))


@mutil.undoable
@mutil.restore_selection
def _disconnect_marker_system(marker):
    if not marker:
        markers = _get_selected_markers()
    else:
        marker = Node(marker)
        if marker.custom_type_name != 'MHYMarker':
            cmds.warning('{} is not a marker.'.format(marker))
            return
        markers = [marker]
    if not markers:
        cmds.warning('No marker selected or under cursor.')

    roots = set()
    for marker in markers:
        root = marker.marker_root
        if root in roots:
            continue
        marker_sys = MarkerSystem(root)
        marker_sys.set_parent_marker(None)
        roots.add(root)
        OpenMaya.MGlobal.displayInfo(
            'Disconnected marker system {}'.format(root))


@mutil.undoable
def _solo_marker_system(node):
    if not cmds.objExists(const.MARKER_ROOT):
        return
    root = Node(const.MARKER_ROOT)

    markers = _get_selected_markers()
    if not markers:
        markers = [Node(node)]

    for c in root.get_children(type_='transform'):
        if c.name.startswith(const.MARKER_ROOT):
            continue
        found = False
        for marker in markers:
            if marker.is_child_of(c):
                c.v.value = True
                found = True
                break
        if not found:
            c.v.value = False


@mutil.undoable
def _show_all_marker_system():
    if not cmds.objExists(const.MARKER_ROOT):
        return

    root = Node(const.MARKER_ROOT)
    for c in root.get_children(type_='transform'):
        if not c.name.startswith(const.MARKER_ROOT):
            c.v.value = True


def _is_line_colored():
    for marker_sys in cmds.ls(
            '*_{}'.format(const.EXT_MARKER_ROOT)) or []:
        marker_sys = MarkerSystem(marker_sys)
        return marker_sys.is_line_colored()


@mutil.undoable
def _toggle_line_colored():
    state = None
    for marker_sys in cmds.ls(
            '*_{}'.format(const.EXT_MARKER_ROOT)) or []:
        marker_sys = MarkerSystem(marker_sys)
        if state is None:
            state = not marker_sys.is_line_colored()
        marker_sys.set_line_colored(state)


@mutil.undoable
def _align_hier_ctrls(marker_system=None):
    """Aligns each hierarchy ctrl in the scene to its associated marker."""
    # gather markers and hier ctrls
    markers = []
    if not marker_system:
        for ms in cmds.ls('*_{}'.format(const.EXT_MARKER_ROOT)) or []:
            for marker in MarkerSystem(ms).iter_markers(plane_marker_last=True):
                markers.append(marker)
        hier_ctrls = cmds.ls(
            '*_{}'.format(const.EXT_MARKER_HIER_CTRL), long=True) or []
        hier_ctrls.sort()
    else:
        for marker in marker_system.iter_markers(plane_marker_last=True):
            markers.append(marker)
        hier_ctrls = []
        for marker in marker_system.iter_markers():
            if marker.hier_ctrl:
                hier_ctrls.append(marker.hier_ctrl)

    # cache marker matrices
    matrices = OrderedDict()
    for marker in markers:
        matrices[marker] = marker.get_matrix(space='world')
        up_ctrl = marker.up_ctrl
        if up_ctrl and up_ctrl not in matrices:
            matrices[up_ctrl] = up_ctrl.get_matrix(space='world')

    # cache hier ctrl mapping
    hier_ctrl_dict = OrderedDict()
    for hier_ctrl in hier_ctrls:
        marker = None
        for each in cmds.listConnections(
                '{}.message'.format(hier_ctrl),
                source=False, destination=True, plugs=False) or []:
            if each.endswith(const.EXT_MARKER):
                marker = Node(each)
        if not marker:
            continue

        hier_ctrl_dict[Node(hier_ctrl)] = marker

    # align hierarchy ctrl to markers
    root = const.MARKER_ROOT
    if cmds.objExists(root):
        Node(root).reset()
    for hier_ctrl, marker in hier_ctrl_dict.items():
        hier_ctrl.set_matrix(matrices[marker], space='world')
        hier_ctrl.reset('s')

    # restore markers
    for marker, matrix in matrices.items():
        marker.set_matrix(matrix, space='world')

    # update hier ctrl size
    for marker in hier_ctrl_dict.values():
        marker.update_hier_ctrl_shape()


@mutil.undoable
def _mirror_markers():
    """Mirrors all markers along -x axis."""
    for root in cmds.ls('*_{}'.format(const.EXT_MARKER_ROOT)) or []:
        if not NodeName(root).is_right:
            MarkerSystem(root).mirror(align_hier=False)
    _align_hier_ctrls()
