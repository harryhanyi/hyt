from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.attribute import Attribute
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath

import mhy.maya.rig.constants as const


ATTR_MIRROR_T = 't_mirror_axis'
ATTR_MIRROR_R = 'r_mirror_axis'
ATTR_HAS_MIRROR_DATA = 'has_mirror_data'


class RigGlobal(object):
    """
    A class used to query data from finished rig products.
    """

    def __init__(self, node_or_namespace=None):
        """Initializes a rig object.

        Args:
            node_or_namespace (str): A rig node or a rig namepsace.
        """
        root = None
        if not node_or_namespace:
            root = const.RIG_ROOT
        elif cmds.objExists(node_or_namespace):
            node = cmds.ls(node_or_namespace, long=True)[0]
            names = node.split('|')
            for i, name in enumerate(names):
                if name and name.split(':')[-1] == const.RIG_ROOT:
                    if i == len(names) - 1:
                        root = node
                    else:
                        root = '|'.join(names[0:i + 1])
                    break
        else:
            root = '{}:{}'.format(node_or_namespace, const.RIG_ROOT)

        if not root or not cmds.objExists(root):
            raise RuntimeError(
                'Failed locating rig from {}.'.format(node_or_namespace))

        self.__root = Node(root)

    @classmethod
    def get_rigs(cls):
        """Returns a list of rigs in the current scene.

        Returns:
            list: A list of RigGlobal objects.
        """
        rigs = []
        for each in cmds.ls('*:{}'.format(const.RIG_ROOT)) + cmds.ls(const.RIG_ROOT):
            try:
                rigs.append(RigGlobal(each))
            except BaseException:
                continue
        return rigs

    def __repr__(self):
        return self.__root.name

    __str__ = __repr__

    def __eq__(self, other):
        return isinstance(other, RigGlobal) and other.root == self.root

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__root.long_name)

    # --- basic properties

    @property
    def root(self):
        """The rig root node."""
        return self.__root

    @property
    def rig_skel_root(self):
        """The rig skeleton root node."""
        skel_root = const.RIG_SKEL_ROOT
        if self.namespace:
            skel_root = '{}:{}'.format(self.namespace, skel_root)
        if cmds.objExists(skel_root):
            return Node(skel_root)

    @property
    def namespace(self):
        """The namespace of this rig."""
        if ':' in self.__root.name:
            return self.__root.name.split(':', 1)[0]

    @property
    def project_name(self):
        """The project name."""
        if self.__root.has_attr('project_name'):
            return self.__root.attr('project_name').value

    @property
    def char_name(self):
        """The character name."""
        if self.__root.has_attr('char_name'):
            return self.__root.attr('char_name').value

    @property
    def rig_type(self):
        """The rig type string."""
        if self.__root.has_attr('rig_type'):
            return self.__root.attr('rig_type').value

    @property
    def has_mirror_data(self):
        """Checks if mirror data is embedded on this rig."""
        if not self.root.has_attr(ATTR_HAS_MIRROR_DATA) or \
           not self.root.attr(ATTR_HAS_MIRROR_DATA).value:
            return False
        return True

    # --- query rig data

    def root_attr(self, attr_name):
        """Returns a root attribute."""
        if self.root.has_attr(attr_name):
            return self.root.attr(attr_name)

    def get_limbs(self):
        """Returns a list of limb root nodes in hierarchical order.

        Returns:
            list: limb root nodes.
        """
        limbs = []
        limb_set = set()
        for each in cmds.listRelatives(
                self.root, allDescendents=True,
                type='transform', fullPath=True) or []:
            limb_root = Node(each)
            if limb_root.custom_type_name == 'MHYLimbRoot' and \
               limb_root not in limb_set:
                for each in limb_root.get_parent_limbs(recursive=True):
                    if each not in limb_set:
                        limbs.append(each)
                        limb_set.add(each)
                limbs.append(limb_root)
                limb_set.add(limb_root)
        return limbs

    def get_ctrls(self, world_offset=True, body=True, face=True):
        """Returns a list of ctrls in this rig.

        Args:
            world_offset (bool): Include world offset ctrls?
            body (bool): Include body ctrls?
            face (bool): Include face ctrls?

        Returns:
            list: A list of MHYCtrl objects.
        """
        ctrls = []
        for limb_root in self.get_limbs():
            is_face = 'face' in limb_root.limb_name.lower()
            if not world_offset and limb_root.limb_type == 'world_offset':
                continue
            if (not body and not is_face) or (not face and is_face):
                continue
            ctrls.extend(limb_root.get_ctrls())
        return ctrls

    def get_rig_joints(self, body=True, face=True):
        """Returns a list of rig joints in this rig.

        Args:
            body (bool): Include body rig joints?
            face (bool): Include face rig joints?

        Returns:
            list: A list of Joint objects.
        """
        joints = []

        skel_root = self.rig_skel_root
        if not skel_root:
            return joints

        for joint in skel_root.list_relatives(
                allDescendents=True, type='joint'):
            is_face = 'face' in joint.name.lower()
            if (not body and not is_face) or (not face and is_face):
                continue
            joints.append(joint)

        return joints

    def get_toggle_attrs(self):
        """Returns a list of bool typed rig toggle attributes.

        Returns:
            list: A list of Attribute objects.
        """
        attrs = []
        for attr in cmds.listAttr(self.__root, userDefined=True) or []:
            attr = '{}.{}'.format(self.__root, attr)
            try:
                typ = cmds.addAttr(attr, query=True, attributeType=True)
            except BaseException:
                typ = ''
            if typ == 'bool':
                attr = Attribute(attr)
                if attr.is_free_to_change:
                    attrs.append(attr)
        return attrs

    # --- rig validation

    def _validate(self):
        """Validates this rig by checking the following:
            + Marker system is removed.
            + Mirror data is embeded.
            + Each ctrl linked to a single limb root.
            + World offset libm exists
            + Each limb root has a parent limb
            + All rig joints parented under the root joint.

        Returns:
            bool: The valiation status.
        """
        warnings = []
        status = True
        skel_root = self.rig_skel_root

        # check if marker system is removed.
        if cmds.objExists(const.MARKER_ROOT):
            status = False
            warnings.append('Marker system not removed.')

        # check if mirror data is embedded
        if not self.has_mirror_data:
            status = False
            warnings.append('Mirror axis not embeded.')

        # check if world offset limb exists
        if not cmds.objExists(const.ROOT_JOINT):
            status = False
            warnings.append('World offset limb not found.')

        for node in self.root.list_relatives(
                allDescendents=True, type='transform'):
            typ = node.custom_type_name

            # check if ctrl has a proper link to a limb root
            if typ == 'MHYCtrl':
                count = 0
                for n in cmds.listConnections(
                        '{}.message'.format(node),
                        source=False, destination=True, plugs=False) or []:
                    n = Node(n)
                    if n.custom_type_name == 'MHYLimbRoot':
                        count += 1

                if count == 0:
                    status = False
                    warnings.append(
                        'Ctrl not linked to limb root: ' + node.name)
                elif count > 1:
                    status = False
                    warnings.append(
                        'Ctrl linked to multiple limb root: ' + node.name)

            # check if limb root has a proper parent limb
            elif typ == 'MHYLimbRoot' and not node.get_parent_limbs():
                status = False
                warnings.append('Limb {} has no parent.'.format(node.name))

            # checks if joints are under the skeleton root
            elif NodeName.is_valid(node) and \
                    NodeName(node).ext == const.EXT_RIG_JOINT:
                if not skel_root or not node.is_child_of(skel_root):
                    status = False
                    warnings.append(
                        'Rig joint not under {}: {}'.format(
                            const.RIG_SKEL_ROOT, node.name))

        # print warnings
        for warning in warnings:
            cmds.warning(warning)

        return status

    # --- rig manipulation

    def align_world_offsets(self):
        """Aligns the world offset ctrls to the bottom of the rig
        while maintaining the current rig pose.
        """

        # get world offset ctrls and the hip ctrl
        world_offsets = []
        hip_ctrl = None
        for limb_root in self.get_limbs():
            if limb_root.limb_type == 'world_offset':
                world_offsets = limb_root.get_ctrls()
            elif limb_root.limb_type == 'hip':
                hip_ctrl = limb_root.get_ctrls()[0]
            if world_offsets and hip_ctrl:
                break

        if not world_offsets:
            cmds.warning('No world offset ctrls found in {}'.format(self.root))
            return
        if not hip_ctrl:
            cmds.warning('No hip ctrl found in {}'.format(self.root))
            return

        # get all other ctrls, cache their matrices
        ctrls = self.get_ctrls(world_offset=False)
        matrices = {}
        for ctrl in ctrls:
            matrices[ctrl] = ctrl.get_matrix(space='world')

        # align world offset position
        pos = list(hip_ctrl.get_translation(space='world'))
        pos[1] = 0
        for ctrl in world_offsets:
            ctrl.set_translation(pos, space='world')
            ctrl.set_rotation((0, 0, 0), space='world')

        # restore ctrl matrices
        for ctrl in ctrls:
            ctrl.set_matrix(matrices[ctrl], space='world')

    def embed_ctrl_mirror_axis(self, tol=0.01):
        """Embeds mirror axis onto each ctrl in this rig. Embedded data is
        used in mirror_pose() to figure out what axis to mirror.

        This method can **ONLY** be ran on a unreferenced rig at bind pose.

        Args:
            tol (float): Tolerance used to check if an axis is symetrical.

        Returns:
            None
        """
        if self.namespace:
            cmds.warning('Rig is referenced, can\'t embed data.')
            return

        for ctrl in self.get_ctrls():
            if NodeName(ctrl).is_right:
                continue

            data = measure_ctrl_mirror_axis(ctrl, skip_locked=True, tol=tol)
            if not data:
                continue

            # embed translate mirror axis
            if data[0]:
                if not ctrl.has_attr(ATTR_MIRROR_T):
                    ctrl.add_attr('string', name=ATTR_MIRROR_T)
                attr = ctrl.attr(ATTR_MIRROR_T)
                attr.locked = False
                attr.value = data[0]
                attr.locked = True

            # embed rotate mirror axis
            if data[1]:
                if not ctrl.has_attr(ATTR_MIRROR_R):
                    ctrl.add_attr('string', name=ATTR_MIRROR_R)
                attr = ctrl.attr(ATTR_MIRROR_R)
                attr.locked = False
                attr.value = data
                attr.locked = True

        # mark this rig as mirror axis embedded
        if not self.root.has_attr(ATTR_HAS_MIRROR_DATA):
            attr = self.root.add_attr(
                'bool', name=ATTR_HAS_MIRROR_DATA, keyable=False)
        else:
            attr = self.root.attr(ATTR_HAS_MIRROR_DATA)
        attr.locked = False
        attr.value = True
        attr.locked = True

        OpenMaya.MGlobal.displayInfo(
            ('Successfully embedded mirror data. '
             'See script editor for potential warnings.'))

    def get_ctrl_mirror_axis(self, ctrl):
        """Returns the ctrl mirror axis data embeded on a given ctrl.

        Args:
            ctrl (MHYCtrl): A ctrl in this rig

        Returns:
            list or None
        """
        if not self.has_mirror_data:
            return

        ctrl = Node(ctrl)

        ctrl_name = NodeName(ctrl)
        ns = self.namespace
        m_ctrl = ctrl_name.flip()
        if ns:
            m_ctrl = ns + ':' + m_ctrl
        if cmds.objExists(m_ctrl):
            m_ctrl = Node(m_ctrl)
        else:
            m_ctrl = None

        axis_ctrl = ctrl if (not ctrl_name.is_right or not m_ctrl) else m_ctrl
        data = []
        for mirror_attr in (ATTR_MIRROR_T, ATTR_MIRROR_R):
            mirror_axis = ''
            if axis_ctrl.has_attr(mirror_attr):
                mirror_axis = axis_ctrl.attr(mirror_attr).value
            data.append(mirror_axis)
        return data

    def mirror_pose(self, ctrls=None, world_offset=False, flip=False):
        """Mirrors this rig's current pose.

        Args:
            ctrls (list): If not None, mirror these ctrls only.
                Otherwise mirror all ctrls in this rig.
            world_offset (bool): If True, mirror world offset ctrls as well.
                Otherwise skips world offsets and mirror the pose in rig space.
            flip (bool): If True, flips the pose.

        Returns:
            None
        """
        if not self.has_mirror_data:
            cmds.warning('{} has no embedded mirror data.'.format(self.root))
            return

        if not ctrls:
            ctrls = [x for x in self.get_ctrls() if not NodeName(x).is_right]

        for ctrl in ctrls:
            if ctrl.custom_type_name != 'MHYCtrl' or \
               not world_offset and ctrl.limb_root.limb_type == 'world_offset':
                continue
            do_flip = flip and not NodeName(ctrl).is_middle

            # get mirrored ctrl
            namespace = ''
            if ':' in ctrl.name:
                namespace = ctrl.name.split(':', 1)[0] + ':'
            m_ctrl = namespace + NodeName(ctrl).flip()
            if not cmds.objExists(m_ctrl):
                continue
            m_ctrl = Node(m_ctrl)

            # mirror translate, rotate, and scale
            axis_ctrl = ctrl if not NodeName(ctrl).is_right else m_ctrl
            for mirror_attr, attr in zip((ATTR_MIRROR_T, ATTR_MIRROR_R), 'tr'):
                mirror_axis = ''
                if axis_ctrl.has_attr(mirror_attr):
                    mirror_axis = axis_ctrl.attr(mirror_attr).value

                for ax in 'xyz':
                    attr_obj = ctrl.attr(attr + ax)
                    m_attr_obj = m_ctrl.attr(attr + ax)
                    if not m_attr_obj.keyable or \
                       not m_attr_obj.is_free_to_change:
                        continue

                    if do_flip:
                        val = m_attr_obj.value
                    m_val = attr_obj.value
                    if ax in mirror_axis:
                        m_val *= -1
                        if do_flip:
                            val *= -1

                    m_attr_obj.value = m_val
                    if do_flip:
                        attr_obj.value = val

            # mirror custom attrs + scale attrs
            # assuming all of them have the mirrored behavior
            attrs = ctrl.list_attr(userDefined=True)
            attrs += [ctrl.sx, ctrl.sy, ctrl.sz]
            for attr in attrs:
                if not attr.keyable or \
                   not attr.is_free_to_change or \
                   not m_ctrl.has_attr(attr.name):
                    continue

                m_attr = m_ctrl.attr(attr.name)
                if not m_attr.keyable or \
                   not m_attr.is_free_to_change:
                    continue

                m_attr.value = attr.value

    def reset_pose(self, ctrls=None, world_offset=False):
        """Resets this rig to the bind pose.

        Args:
            ctrls (list): If not None, reset these ctrls only.
                Otherwise reset all ctrls in this rig.
            world_offset (bool): If True, reset world offset ctrls as well.

        Returns:
            None
        """
        ctrls = ctrls if ctrls else self.get_ctrls()
        for ctrl in ctrls:
            if ctrl.custom_type_name != 'MHYCtrl' or \
               not world_offset and ctrl.limb_root.limb_type == 'world_offset':
                continue

            for attr in ctrl.list_attr(keyable=True):
                if not attr.is_free_to_change:
                    continue
                default = attr.default
                if default is not None:
                    attr.value = default


def measure_ctrl_mirror_axis(ctrl, skip_locked=True, tol=0.01):
    """Measure a given ctrl and returns the mirror axis data.

    This method can **ONLY** be ran on a unreferenced rig at bind pose.

    Args:
        ctrl (MHYCtrl or str): A ctrl to operate on.
        skip_locked (bool): If True, skipped locked axis.
        tol (float): Tolerance used to check if an axis is symetrical.

    Returns:
        list
    """
    name = NodeName(ctrl)
    mirror_axis = ''
    if skip_locked:
        t_open_axis = ''
        r_open_axis = ''
    else:
        t_open_axis = 'xyz'
        r_open_axis = 'xyz'
    final_tol = tol

    if not cmds.objExists(name):
        return

    ctrl = Node(ctrl)

    # skip right ctrls
    if name.is_right:
        return measure_ctrl_mirror_axis(
            name.flip(), skip_locked=skip_locked, tol=tol)

    # find the mirrored ctrl
    m_ctrl = name.flip()
    if m_ctrl == ctrl.name:
        m_ctrl = ctrl
        final_tol = 0.1
    elif cmds.objExists(m_ctrl):
        m_ctrl = Node(m_ctrl)
    else:
        return

    for ax in 'xyz':
        l_vec = mmath.axis_to_vector(ctrl, ax)
        r_vec = mmath.axis_to_vector(m_ctrl, ax)
        r_vec[0] *= -1

        # if vectors not the same -> add to mirror axis
        if not l_vec.isEquivalent(r_vec, final_tol):
            mirror_axis += ax

        # get translate & rotate open axis
        if skip_locked:
            attr = ctrl.attr('t' + ax)
            if attr.keyable and attr.is_free_to_change:
                t_open_axis += ax
            attr = ctrl.attr('r' + ax)
            if attr.keyable and attr.is_free_to_change:
                r_open_axis += ax

    # embed translate mirror axis
    data = []
    if t_open_axis:
        t_mirror_axis = set(t_open_axis) & set(mirror_axis)
        t_mirror_axis = sorted(list(t_mirror_axis))
        value = ''
        for each in t_mirror_axis:
            value += each
        data.append(value)
    else:
        data.append('')

    # embed rotate mirror axis
    if r_open_axis:
        if mirror_axis in ('xyz', ''):
            value = ''
        elif mirror_axis in ('x', 'y', 'z'):
            r_mirror_axis = sorted(list(set('xyz') - set(mirror_axis)))
            r_mirror_axis = sorted(
                list(set(r_open_axis) & set(r_mirror_axis)))
            value = ''
            for each in r_mirror_axis:
                value += each
        else:
            value = mirror_axis
            cmds.warning(
                '{} : {}. This is not heavily tested yet.'.format(
                    ctrl, mirror_axis))

        data.append(value)
    else:
        data.append('')

    return data
