"""
Node class for joints
"""
from maya import cmds
import maya.OpenMayaAnim as OpenMayaAnim

import mhy.maya.maya_math as mmath
from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node, Transform


class Joint(Transform):
    """
    Joint node class.
    """

    __NODETYPE__ = 'joint'
    __FNCLS__ = OpenMayaAnim.MFnIkJoint

    @classmethod
    def create(cls, clear_selection=False, *args, **kwargs):
        if clear_selection:
            cmds.select(clear=True)
        return cls(cmds.joint(*args, **kwargs))

    @property
    def long_axis(self):
        """Returns the long axis name as 'X', 'Y', 'Z', '-X', '-Y', '-Z'."""
        return self.get_long_axis()

    def get_long_axis(self, aim_target=None):
        """Returns the long axis name as 'X', 'Y', 'Z', '-X', '-Y', '-Z'.

        Args:
            aim_target (str or None):
                A node that the long axis of this joint should aim to.
                If None, use the children or parent of this joint.
        """
        if aim_target:
            targets = [Node(aim_target)]
        else:
            targets = self.get_children(type_='joint')
            if not targets:
                targets = [self.get_parent()]
            if not targets:
                raise RuntimeError(
                    '{} does not have a parent or child joint.'.format(self.name))

        for target in targets:
            if not target or target.type_name != 'joint':
                continue
            src_pos = self.get_translation(space='world', as_tuple=False)
            tar_pos = target.get_translation(space='world', as_tuple=False)
            vec = tar_pos - src_pos
            vec.normalize()
            for ax in ('x', 'y', 'z', '-x', '-y', '-z'):
                ax_vec = mmath.axis_to_vector(self, ax)
                if ax_vec.isEquivalent(vec, 0.05):
                    return ax.upper()

    def orient_chain(self, **kwargs):
        """Orients the joint chain starting from this joint.

        Args:
            kwargs: Keyword arguments accepted by cmds.joint().

        Defaults:
            zeroScaleOrient: True
            orientJoint: xyz
            secondaryAxisOrient: yup
            children: True

        Returns: None
        """
        for keys, default in (
                (('zeroScaleOrient', 'zso'), True),
                (('orientJoint', 'oj'), 'xyz'),
                (('secondaryAxisOrient', 'sao'), 'yup'),
                (('children', 'c'), True)):
            if keys[1] in kwargs:
                kwargs[keys[0]] = kwargs.pop(keys[1])
            elif keys[0] not in kwargs:
                kwargs[keys[0]] = default

        cmds.joint(self.long_name, edit=True, **kwargs)
        if kwargs.get('children', kwargs.get('ch', True)):
            self.orient_end_joints()

    def get_leaf_joints(self):
        """Returns a list of leaf joints under this joint."""
        leafs = []
        for joint in cmds.listRelatives(
                self.long_name, type='joint',
                fullPath=True, allDescendents=True) or []:
            if not cmds.listRelatives(joint, children=True, shapes=False):
                leafs.append(Node(joint))
        return leafs

    def orient_end_joints(self):
        """Orients the end joints under this joint.
        Returns: None
        """
        for leaf in self.get_leaf_joints():
            leaf.jointOrient.value = (0, 0, 0)

    def duplicate(self, radius=None, **kwargs):
        """Duplicates this joint node.

        Args:
            radius (float): A radius to apply to the duplicated joint.
                If None, use this joint's radius.
            kwargs: Keyword argument accepted by cmds.duplicate().

        Returns:
            Node: The duplicated joint.
        """
        nodes = super(Joint, self).duplicate(**kwargs)
        if radius is None:
            radius = self.get_attr('radius')
        for each in nodes[0].get_hierarchy(skip_self=False):
            each.set_attr('radius', radius)
        return nodes

    def get_hierarchy(self, skip_self=False, end=None):
        """Returns all joints under this joint.

        Args:
            skip_self (bool): If True, exclude this joint in the return list.
            end (Joint or None): If not None, skips joints under it.
            flat (bool): If not True, returns a flat list.
                otherwise returns a nested list with each list reflects the
                depth of each joint chain.
            use_depth_joint (bool): This argument is **ONLY** used when
                "flat" is False.
                If True, fill the list with DepthJoint objects.
                Otherwise fill with Joint objects.

        Returns:
            list: A list of children joints.
        """
        # get the optional end joint
        if end:
            end = Node(end).long_name
            if end == self.long_name:
                return [self] if not skip_self else []

        # get joint chain
        joints = cmds.listRelatives(
            self.long_name, fullPath=True, allDescendents=True, type='joint') or []
        joints = [Node(j) for j in joints[::-1]]
        if end:
            joints = [j for j in joints
                      if end == j.long_name or end not in j.long_name]
        if not skip_self:
            joints = [self] + joints

        return joints

    def get_chain(self, end_joint):
        """Returns a list of joints that starts from this joint and ends at
        a given end joint."""
        end_joint = Node(end_joint)
        if end_joint == self:
            return [self]
        if end_joint.type_name != 'joint':
            raise ValueError('{} is not a joint'.format(end_joint))
        if not end_joint.is_child_of(self):
            raise ValueError('{} is not a child of {}'.format(end_joint, self))

        joints = []
        parent = end_joint
        while True:
            if parent.type_name == 'joint':
                joints.append(parent)
            parent = parent.get_parent()
            if not parent or parent == self:
                break

        joints.append(self)
        joints.reverse()
        return joints

    def set_segment_scale_compensate(self, value, hierarchy=True):
        """Sets the segment scale compensate value for this joint.

        Args:
            value (bool): The compensate value to apply.
            hierarchy (bool): If True, apply segment scale compensat for
                all children joints.

        Returns: None
        """
        if hierarchy:
            joints = self.get_hierarchy(skip_self=False)
        else:
            joints = [self]
        for joint in joints:
            joint.set_attr('segmentScaleCompensate', value)

    def get_length(self):
        """Returns the distance from this joint to its parent."""
        parent = self.get_parent()
        if parent and parent.type_name == 'joint':
            pos = self.get_translation(space='world', as_tuple=False)
            ppos = parent.get_translation(space='world', as_tuple=False)
            return (pos - ppos).length()
        return 0

    def get_chain_length(self, end=None, _start_length=0):
        """Returns the joint chain lenght starting from this joint.

        If multiple branches exists, this method only operate on the first one.

        Returns:
            end (Joint or None): If not None, stop the recursion when this
                end joint is reached.
            float: The joint chain length.
        """
        joints = self.get_children(type_='joint')
        if end:
            end = Node(end)
        if not joints or joints[0] == end:
            return _start_length
        pos = self.get_translation(space='world', as_tuple=False)
        cpos = joints[0].get_translation(space='world', as_tuple=False)
        length = (pos - cpos).length() + _start_length
        return joints[0].get_chain_length(_start_length=length)

    def add_inbetween_joints(
            self, end_joint, desc_suffix, num=1, mode='start'):
        """Creates a list of joints between a start joint and an end joint.

        Args:
            end_joint (str or Node): the end joint.
            desc_suffix (str): A suffix to append to the start joint's
                descriptor token. Used to name the inbetween joints.
            num (int): Number of twist joints to build.
            mode (str): Method used to distribute the output joints.
                + "start": First joint at start of the ribbon,
                    no joint at the end.
                + "end": Last output joint at end of the ribbon,
                    no joint at the start.
                + "start_end": Create joints at both ends.
                + "mid": No joint on the ends.

        Returns:
            list: A list of twist joints created.
        """
        end_joint = Node(end_joint)
        base_name = NodeName(self)

        joints = []

        for i, pos in enumerate(mmath.get_inbetween_positions(
                self, end_joint, num, mode)):

            name = NodeName(base_name, desc=base_name.desc + desc_suffix, num=i)
            if cmds.objExists(name):
                raise RuntimeError(
                    'twistJoint:{} is already existed'.format(name))
            joint = self.duplicate(
                name=name, inputConnections=False, parentOnly=True)[0]
            joint.unlock()
            joint.set_parent(self)
            joint.set_translation(pos, space='world')
            joints.append(joint)

        return joints
