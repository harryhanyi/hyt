import re

from maya import cmds, OpenMaya

import mhy.protostar.core.parameter as pa

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
import mhy.maya.maya_math as mmath
import mhy.maya.rig.constants as const
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.utils as util


EXT_POSE_CTRL = 'POSECTRL'
EXT_JOINT_CTRL = 'FKCTRL'


class GameFace(bl.BaseLimb):
    """
    A joint-based ingame face rig.

    :limb type: game_face
    """

    _LIMB_TYPE = 'game_face'
    _CTRL_VIS_ATTR = 'face_ctrl'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'face'

    # -- input parameters

    @pa.str_param(default='Face')
    def face_mesh(self):
        """A face mesh used as a reference to place the aim ctrls."""

    # --- end of parameter definition

    def marker_data(self):
        """Skip marker data as this limb depends on a pre-existing
        joint hierarchy."""
        return

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        The bind skeleton consists of all joints under face root.
        """
        self.tag_bind_hierarchy(self.rig_skeleton[0][0])

    def run(self):
        """Builds the limb ctrl rig."""
        self._ctrl_scale = (.1, .1, .1)
        self._main_ctrl_scale = [x * 2 for x in self._ctrl_scale]
        self._main_ctrl_shape = 'square'
        self._pose_ctrl_scale = [x * 2 for x in self._ctrl_scale]
        self._pose_ctrl_shape = 'sphere'
        self._face_mesh = None
        mesh = self.face_mesh.value
        if mesh and cmds.objExists(mesh):
            self._face_mesh = Node(mesh).get_shapes(exact_type='mesh')
            self._face_mesh = self._face_mesh[0] if self._face_mesh else None

        # build joint ctrls (with hierarchy)
        exclude_joints = set(self._find_joints(part='eye'))
        self.build_joint_ctrls(exclude_joints)

        # find the jaw ctrl
        jaw_joint = self._find_joints(part='jaw', side='M')
        if jaw_joint:
            jaw_ctrl = self._ctrl_dict[jaw_joint[0]]
        else:
            jaw_ctrl = None

        # build extra setups
        self.build_jaw_extra(jaw_ctrl)
        self.build_mouth_extra(jaw_ctrl)
        self.build_brow_extra()
        self.build_eyelid_extra()
        self.build_cheek_extra()
        self.create_pose_node()

    def _find_joints(self, part='face', desc=None, side=None):
        """Returns a list of joints under the face root joint.

        Args:
            part (str): The joint part token.
            desc (str): The joint decriptor token.
            side (str): The joint side token. If None, include all sides.

        Returns:
            list: A list of ctrls found (sorted by name).
        """
        if not side:
            side = '*'
        if not desc:
            string = '{}_*_{}_RIGJNT'.format(part, side)
        else:
            string = '{}_{}_*_{}_RIGJNT'.format(part, desc, side)
        root_joint = self.rig_skeleton[0][0]
        pat = '.*{}.*'.format(root_joint.name)
        joints = cmds.ls(string, type='joint', long=True)
        joints.sort()
        return [Node(j) for j in joints if re.match(pat, j)]

    def build_joint_ctrls(self, exclude_joints):
        """Build a fk ctrl for each joint under the face root joint.

        Args:
            exclude_joints (list): A list of joints to exclude.

        Returns:
            None
        """
        self._ctrl_dict = {}
        root_joint = self.rig_skeleton[0][0]
        for joint in root_joint.get_hierarchy():
            if joint == root_joint or joint in exclude_joints:
                continue

            ctrl = self.add_ctrl(
                xform=joint,
                ext=EXT_JOINT_CTRL,
                shape='cube',
                scale=self._ctrl_scale,
                group_exts=('PLC', 'SDK', 'OFFSET', 'POSE'))
            self._ctrl_dict[joint] = ctrl
            util.add_influence_tag_attribute(ctrl)

            self.add_constraint('parent', ctrl, joint, maintainOffset=True)
            self.add_constraint('scale', ctrl, joint, maintainOffset=True)

            parent = joint.get_parent()
            while True:
                if not parent or parent.type_name == 'joint':
                    break
                parent = parent.get_parent()

            if parent:
                parent_ctrl = NodeName(parent, ext=EXT_JOINT_CTRL)
                if cmds.objExists(parent_ctrl):
                    ctrl.plc_node.set_parent(parent_ctrl)

    def snap_to_mesh(self, ctrl, offset=1):
        """Snaps a ctrl to the face mesh (if provided).

        The ctrl's z axis will be fixed to the mesh normal.
        The ctrl's y axis will try to align to scene up.

        Args:
            ctrl (MHYCtrl): A ctrl to snap.
            offset (float): The amount of ctrl shape local offset
                along the mesh normal.

        Returns:
            None
        """
        if not self._face_mesh:
            return

        pos = ctrl.get_translation(space='world')
        mesh_pos = self._face_mesh.closest_point(pos, as_tuple=False)
        mesh_normal = self._face_mesh.closest_normal(pos, as_tuple=False)
        aim_pos = mesh_pos + mesh_normal * 2

        tmp = Node.create('transform', name='tmp')
        tmp.set_translation(aim_pos)
        ctrl.plc_node.set_translation(mesh_pos, space='world')
        cns = ctrl.plc_node.constrain(
            'aim', tmp,
            aimVector=(0, 0, 1), upVector=(0, 1, 0),
            worldUpType='scene', maintainOffset=False)
        cmds.delete(cns, tmp)

        ctrl.plc_node.set_translation(mesh_pos, space='world')
        ctrl.shape.local_position = (0, 0, offset)

    def snap_to_mesh_yup(self, ctrl, offset=1):
        """Snaps a ctrl to the face mesh (if provided).

        The ctrl's y axis will be fixed to scene up.
        The ctrl's z axis will try to align to the mesh normal.

        Args:
            ctrl (MHYCtrl): A ctrl to snap.
            offset (float): The amount of ctrl shape local offset
                along the mesh normal.

        Returns:
            None
        """
        if not self._face_mesh:
            return

        pos = ctrl.plc_node.get_translation(space='world')
        matrix = ctrl.plc_node.get_matrix(
            space='world', as_tuple=False, as_transform=True)
        mesh_pos = self._face_mesh.closest_point(pos, as_tuple=False)
        mesh_normal = self._face_mesh.closest_normal(pos, as_tuple=False)

        fwd_vec = mmath.axis_to_vector(ctrl.plc_node, 'z', as_tuple=False)
        quat = OpenMaya.MQuaternion(fwd_vec, mesh_normal)
        matrix.rotateBy(quat, OpenMaya.MSpace.kWorld)
        ctrl.plc_node.set_matrix(matrix, space='world')
        y_vec = mmath.axis_to_vector(ctrl.plc_node, 'y', as_tuple=False)
        quat = OpenMaya.MQuaternion(y_vec, OpenMaya.MVector(0, 1, 0))
        matrix.rotateBy(quat, OpenMaya.MSpace.kWorld)
        ctrl.plc_node.set_matrix(matrix, space='world')

        ctrl.plc_node.set_translation(mesh_pos, space='world')
        ctrl.shape.local_position = (0, 0, offset)

    def _build_main_ctrl(
            self, joints, snap_to_mesh=False,
            shape_type=None, desc=None, side=None, pos=None):
        """Builds a main/region ctrl that moves a list of joint ctrls.

        Args:
            joints (list): A list of joints to drive.
            snap_to_mesh (bool): If True, snap the main ctrl to the mesh.
            shape_type (str): Main ctrl shape type.
                If None, use self._main_ctrl_shape.
            desc (str): Main ctrl name descriptor token.
                If None, use the descriptor token of the first joint.
            side (str): Main ctrl name side token.
                If None, use the side token of the first joint.
            pos (tuple): Main ctrl position.
                If None, use the center position of all input joints.

        Returns:
            MHYCtrl: The main ctrl.
        """
        ctrls = [self._ctrl_dict[j] for j in joints]
        if not ctrls:
            return

        name = NodeName(ctrls[0])
        if not desc:
            desc = name.desc
        if not side:
            side = name.side
        if not shape_type:
            shape_type = self._main_ctrl_shape
        name = NodeName(ctrls[0], desc=desc, side=side, num=None, ext=EXT_POSE_CTRL)
        main_ctrl = self.add_ctrl(
            name=name, shape=shape_type,
            scale=self._main_ctrl_scale,
            parent=ctrls[0].plc_node.get_parent())
        if not pos:
            pos = mmath.get_position_center(joints)
        main_ctrl.plc_node.set_translation(pos, space='world')
        if snap_to_mesh:
            self.snap_to_mesh_yup(main_ctrl)

        # resize and position the main ctrl
        size = mmath.get_object_size(ctrls)
        main_ctrl.shape.local_rotate = (90, 0, 0)
        if shape_type == 'circle':
            main_ctrl.shape.local_scale = (size[1] * .6, 1, size[1] * .6)
        else:
            main_ctrl.shape.local_scale = (size[0], 1, size[1] * .6)
        main_ctrl.shape.local_position = (0, 0, 1)

        main_ctrl.set_transform_limits(
            translationX=(-1, 1),
            translationY=(-1, 1),
            translationZ=(-1, 1),
            enableTranslationX=(True, True),
            enableTranslationY=(True, True),
            enableTranslationZ=(True, True))

        # parent ctrls under the main ctrl
        for ctrl in ctrls:
            ctrl.plc_node.set_parent(main_ctrl)

        return main_ctrl

    def build_jaw_extra(self, jaw_ctrl):
        """Builds jaw extra setups:

            + Jaw pose ctrl.

        Args:
            jaw_ctrl (MHYCtrl): The jaw ctrl.

        Returns:
            None
        """
        if not jaw_ctrl:
            return

        name = NodeName(jaw_ctrl, num=None, ext=EXT_POSE_CTRL)
        pose_ctrl = self.add_ctrl(
            name=name, shape=self._pose_ctrl_shape, scale=self._pose_ctrl_scale)
        pose_ctrl.plc_node.align(jaw_ctrl)
        if self._face_mesh:
            size = mmath.get_object_size(self._face_mesh)
            pose_ctrl.shape.local_position = (0, 0, size[2] * .5)
        pose_ctrl.lock('rsv')
        pose_ctrl.set_transform_limits(
            translationX=(-1, 1),
            translationY=(-1, 1),
            translationZ=(0, 1),
            enableTranslationX=(True, True),
            enableTranslationY=(True, True),
            enableTranslationZ=(True, True))
        pose_ctrl.add_separator_attr('pose')
        pose_ctrl.add_attr(
            'double', name='Ooo', keyable=True,
            defaultValue=0, minValue=0, maxValue=1)
        pose_ctrl.add_attr(
            'double', name='M', keyable=True,
            defaultValue=0, minValue=0, maxValue=1)

    def build_mouth_extra(self, jaw_ctrl):
        """Builds mouth extra setups:

            + Mounth corner follow jaw.
            + Mounth corner pose ctrls.
            + Upper and lower lip main ctrls.
            + lip pose attrs.

        Args:
            jaw_ctrl (MHYCtrl): The jaw ctrl.

        Returns:
            None
        """
        mouth_cnr_joints = self._find_joints(desc='mouthCrnr')

        # mouth corner follow jaw
        if jaw_ctrl and mouth_cnr_joints:
            for each in mouth_cnr_joints:
                ctrl = self._ctrl_dict[each]

                ctrl.add_attr(
                    'double', name='corner_follow', keyable=True,
                    minValue=0, maxValue=1, defaultValue=.5)

                rev = Node.create('reverse', name=NodeName(jaw_ctrl, ext='CFREV'))
                ctrl.corner_follow >> rev.inputX

                ctrl.plc_node.set_parent(jaw_ctrl.plc_node.get_parent())
                ref_jaw = Node.create(
                    'transform', name=NodeName(each, ext='JAWREF'),
                    parent=jaw_ctrl)
                ref_jaw.align(ctrl)
                ref_joint = Node.create(
                    'transform', name=NodeName(each, ext='JNTREF'),
                    parent=ctrl.plc_node.get_parent())
                ref_joint.align(ctrl)

                cns = ctrl.plc_node.constrain(
                    'parent', (ref_jaw, ref_joint), maintainOffset=False)
                cns.interpType.value = 0
                ctrl.corner_follow >> cns.attr(ref_jaw.name + 'W0')
                rev.outputX >> cns.attr(ref_joint.name + 'W1')

        # mout corner pose ctrls
        if mouth_cnr_joints:
            for each in mouth_cnr_joints:
                ctrl = self._ctrl_dict[each]
                name = NodeName(ctrl, num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name, shape=self._pose_ctrl_shape, scale=self._pose_ctrl_scale)
                pose_ctrl.plc_node.align(ctrl)
                self.snap_to_mesh_yup(pose_ctrl)
                pose_ctrl.lock('tzrsv')
                pose_ctrl.set_transform_limits(
                    translationX=(-1, 1),
                    translationY=(-1, 1),
                    enableTranslationX=(True, True),
                    enableTranslationY=(True, True))

        # lip pose ctrls
        for desc in ('mouthUpper', 'mouthLower'):
            for side in ('L', 'R'):
                joints = self._find_joints(desc=desc, side=side)

                if len(joints) > 1:
                    position = mmath.get_position_center(joints)
                else:
                    position = joints[0].get_translation(space='world')
                ctrl = self._ctrl_dict[joints[0]]
                name = NodeName(ctrl, num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name, shape=self._pose_ctrl_shape, scale=self._pose_ctrl_scale)
                pose_ctrl.plc_node.set_translation(position)
                self.snap_to_mesh_yup(pose_ctrl)
                pose_ctrl.lock('txtzrsv')
                if desc == 'mouthUpper':
                    limit = (0, 1)
                else:
                    limit = (-1, 0)
                pose_ctrl.set_transform_limits(
                    translationY=limit,
                    enableTranslationY=(True, True))

            m_joint = self._find_joints(desc=desc, side='M')[0]
            ctrl = self._ctrl_dict[m_joint]
            name = NodeName(ctrl, num=None, ext=EXT_POSE_CTRL)
            pose_ctrl = self.add_ctrl(
                name=name, shape=self._pose_ctrl_shape, scale=self._pose_ctrl_scale)
            pose_ctrl.plc_node.align(ctrl)
            pose_ctrl.lock('txrsv')
            pose_ctrl.set_transform_limits(
                translationY=(-1, 1),
                translationZ=(-1, 1),
                enableTranslationY=(True, True),
                enableTranslationZ=(True, True))

    def build_brow_extra(self):
        """Builds brow extra setups:

            + Brow corner pose ctrls.
            + Brow mid pose ctrls.

        Returns:
            None
        """
        for side in 'LR':
            joints = self._find_joints(desc='brow', side=side)
            if not joints:
                continue

            ctrls = [self._ctrl_dict[j] for j in joints]
            position = mmath.get_position_center(ctrls)
            name = NodeName(
                ctrls[0], desc='browMid', num=None, ext=EXT_POSE_CTRL)
            m_pose_ctrl = self.add_ctrl(
                name=name, shape=self._pose_ctrl_shape, scale=self._pose_ctrl_scale)
            m_pose_ctrl.plc_node.set_translation(position)
            self.snap_to_mesh_yup(m_pose_ctrl)
            m_pose_ctrl.lock('txtzrsv')
            m_pose_ctrl.set_transform_limits(
                translationY=(-1, 1),
                enableTranslationY=(True, True))

            # build corner pose ctrls
            for token, ctrl in zip(('In', 'Out'), (ctrls[0], ctrls[-1])):
                name = NodeName(ctrl)
                name = NodeName(
                    ctrl, desc=name.desc + token, num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name,
                    shape=self._pose_ctrl_shape,
                    scale=self._pose_ctrl_scale)
                pose_ctrl.plc_node.align(ctrl)
                self.snap_to_mesh_yup(pose_ctrl)
                pose_ctrl.lock('tzrsv')
                pose_ctrl.set_transform_limits(
                    translationX=(-1, 1),
                    translationY=(-1, 1),
                    enableTranslationX=(True, True),
                    enableTranslationY=(True, True))

    def build_eyelid_extra(self):
        """Builds eyelid extra setups:

            + eyelid main ctrls.
            + eyelid pose attrs.

        Returns:
            None
        """
        for side in 'LR':
            joints = []
            for desc in (
                    'eyelidLower',
                    'eyelidUpper',
                    'eyelidCrnrIn',
                    'eyelidCrnrOut'):
                joints += self._find_joints(desc=desc, side=side)

            if not joints:
                continue

            eye_joint = self._find_joints(part='eye', side=side)
            if eye_joint:
                eye_joint = eye_joint[0]

            if eye_joint:
                pos = eye_joint.get_translation(space='world')
            else:
                pos = mmath.get_position_center(joints)
            main_ctrl = self._build_main_ctrl(
                joints, shape_type='circle', desc='eyelid', pos=pos)

            # constraint eye joint
            if eye_joint:
                eye_joint.constrain('point', main_ctrl, maintainOffset=False)
                eye_joint.constrain('scale', main_ctrl, maintainOffset=False)

            # add pose attrs
            main_ctrl.add_separator_attr('pose')
            main_ctrl.add_attr(
                'double', name='blink', keyable=True,
                defaultValue=0, minValue=0, maxValue=1)

            # add pose ctrls
            for desc in (
                    'eyelidLower',
                    'eyelidUpper'):
                joints = self._find_joints(desc=desc, side=side)
                ctrls = [self._ctrl_dict[j] for j in joints]
                pose = mmath.get_object_center(ctrls)
                name = NodeName(ctrls[0], num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name,
                    shape=self._pose_ctrl_shape,
                    scale=self._pose_ctrl_scale)
                pose_ctrl.plc_node.set_translation(pose)
                pose_ctrl.lock('txtzrsv')
                pose_ctrl.set_transform_limits(
                    translationY=(-1, 1),
                    enableTranslationY=(True, True))

    def build_cheek_extra(self):
        """Builds cheek extra setups:

            + Cheek pose ctrls.

        Returns:
            None
        """
        for side in 'LR':
            joints = self._find_joints(desc='cheek', side=side)

            # cheek pose ctrls
            if joints:
                ctrls = [self._ctrl_dict[j] for j in joints]

                name = NodeName(ctrls[0], num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name,
                    shape=self._pose_ctrl_shape,
                    scale=self._pose_ctrl_scale)
                pos = mmath.get_object_center(ctrls)
                pose_ctrl.plc_node.set_translation(pos)
                self.snap_to_mesh(pose_ctrl)
                pose_ctrl.lock('txrsv')
                pose_ctrl.set_transform_limits(
                    translationY=(0, 1),
                    translationZ=(0, 1),
                    enableTranslationY=(True, True),
                    enableTranslationZ=(True, True))

            joint = self._find_joints(desc='nostril', side=side)[0]

            # nose pose ctrls
            if joint:
                ctrl = self._ctrl_dict[joint]

                name = NodeName(ctrl, num=None, ext=EXT_POSE_CTRL)
                pose_ctrl = self.add_ctrl(
                    name=name,
                    shape=self._pose_ctrl_shape,
                    scale=self._pose_ctrl_scale)
                pose_ctrl.plc_node.align(ctrl)
                pose_ctrl.lock('txtzrsv')
                pose_ctrl.set_transform_limits(
                    translationY=(0, 1),
                    enableTranslationY=(True, True))

    def create_pose_node(self):
        """
        Create pose node and setup blendshape for pose workflow.
        """
        pose_node = Node.create(
            'MHYCtrl',
            name=NodeName(self.rig_skeleton[0][0], ext='PoseWeightAttributes'),
            group_exts=[])

        pose_node.set_parent(self.ws_root)
        pose_node.shape.shape_type = 4
        pose_node.v.value = False
        pose_node.lock()
        shape_node = pose_node.get_shapes()[0]
        shape_node.controllerType.value = 1
        shape_node.add_attr('message', name=const.POSE_MESH_MSG_ATTR)
        base_mesh_name = self.face_mesh.value
        if not base_mesh_name:
            self.error(
                ('Base Mesh is not defined.'
                 'This will result in post process error'))
            return
        base_mesh = Node(base_mesh_name)
        base_mesh.add_attr('message', name=const.POSE_MESH_MSG_ATTR)
        shape_node.attr(const.POSE_MESH_MSG_ATTR) >> base_mesh.attr(const.POSE_MESH_MSG_ATTR)
        Node.create('blendShape',
                    base_mesh_name,
                    name=shape_node.name + '_TARGET_BLENDSHAPE',
                    frontOfChain=True)
