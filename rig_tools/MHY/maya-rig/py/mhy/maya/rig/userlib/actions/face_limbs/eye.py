import maya.cmds as cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const


_COLOR = 0
_DEFAULT_EYE_JOINTS = ('face_eye_00_L_RIGJNT', 'face_eye_00_R_RIGJNT')


class EyeWithAim(bl.BaseLimb):
    """
    A simple eye rig with aim ctrls.

    :limb type: eye
    """

    _LIMB_TYPE = 'eye'
    _CTRL_VIS_ATTR = 'eye_ctrl'

    _UI_ICON = 'eye'

    # -- input parameters

    @pa.str_param(default='Face')
    def face_mesh(self):
        """A face mesh used as a reference to place the aim ctrls."""

    @pa.str_param(default='CTRL')
    def ctrl_ext(self):
        """The ctrl name extension."""

    # @pa.bool_param(default=False)
    # def enable_scale(self):
    #     """If True, enable scale constraint."""

    # --- end of parameter definition

    def __init__(self, *args, **kwargs):
        """Initializes a new limb object."""
        super(EyeWithAim, self).__init__(*args, **kwargs)
        # lock and hide a few unused parameters
        for name, val in zip(('side', 'mirror'), ('M', False)):
            self.param(name).value = val
            self.param(name).ui_visible = False
            self.param(name).editable = False

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        name = NodeName(part=part, num=None, ext=const.EXT_MARKER)

        return [
            {'markers': [
                {'name': name.replace_side('L'),
                 'position': (1, 5, 0),
                 'rotation': None}]
             },
            {'markers': [
                {'name': name.replace_side('R'),
                 'position': (-1, 5, 0),
                 'rotation': None}]
             }]

    def resolve_input_skeleton(self):
        """Re-implemeneted to update self.rig_skeleton with 2 input eye joints.
        """
        val = self.input_skeleton.value
        if not val:
            val = _DEFAULT_EYE_JOINTS
            for each in val:
                if not cmds.objExists(each):
                    raise exp.ActionError('eye joint {} not found.'.format(each))
        if not len(val) == 2:
            raise exp.ActionError('Must provide 2 eye joints.')
        self._set_rig_skeleton([[Node(val[0])], [Node(val[1])]])

    def run(self):
        """Builds the limb ctrl rig."""
        # get face mesh
        face_mesh = self.face_mesh.value
        if face_mesh and cmds.objExists(face_mesh):
            face_mesh = Node(face_mesh)
        else:
            face_mesh = None

        # get eye joints
        eye_joints = (self.rig_skeleton[0][0], self.rig_skeleton[1][0])

        # other parameter values
        ctrl_ext = self.ctrl_ext.value

        # build a start joint
        name = NodeName(eye_joints[0], desc='aim', side='M')
        start_joint = Node(cmds.spaceLocator(name=name)[0])

        if face_mesh:
            bb_min_z = face_mesh.boundingBoxMinZ.value
            bb_max_z = face_mesh.boundingBoxMaxZ.value
            bb_min_x = face_mesh.boundingBoxMinX.value
            bb_max_x = face_mesh.boundingBoxMaxX.value
            ctrl_tz = bb_max_z + abs(bb_max_z - bb_min_z)
            ctrl_rad = ((bb_max_x - bb_min_x) / 2) * 0.333
            ctrl_scale = [ctrl_rad] * 3
        else:
            ctrl_scale = [1] * 3
            ctrl_tz = 10

        z_aim = (0, 0, 1)
        y_up = (0, 1, 0)

        aim_ctrls = []
        for eye_jnt in eye_joints:
            # add aim ctrl
            name = NodeName(eye_jnt, desc='aim', ext=ctrl_ext)
            aim_ctrl = self.add_ctrl(
                name=name,
                xform=eye_jnt,
                shape='circle',
                scale=ctrl_scale,
                rot=(90, 0, 0),
                color=_COLOR)

            # add rotate ctrl
            name = name.replace_desc('rotate')
            rot_ctrl = self.add_ctrl(
                name=name,
                xform=eye_jnt,
                shape='cube',
                scale=ctrl_scale,
                color=_COLOR)
            rot_ctrl.align(eye_jnt)

            # setup aim - assume scene is Y-Up, aim axis is Z
            self.add_constraint(
                'aim', aim_ctrl, rot_ctrl.sdk_node,
                maintainOffset=True,
                aimVector=z_aim,
                upVector=y_up,
                worldUpType='none')

            aim_ctrls.append(aim_ctrl)

        # create grand parent ctrl
        name = NodeName(start_joint, desc='aimMain', ext=ctrl_ext)
        aim_main_ctrl = self.add_ctrl(
            name=name,
            xform=start_joint,
            shape='circle',
            scale=ctrl_scale,
            rot=(90, 0, 0),
            color=_COLOR)

        aim_main_ctrl.plc_node.align(aim_ctrls, skipRotate=True)
        aim_main_ctrl.plc_node.align(aim_ctrls, skipTranslate=True, skipRotate='yz')

        # build hierarchy
        for ctrl in aim_ctrls:
            ctrl.plc_node.set_parent(aim_main_ctrl)
        aim_main_ctrl.plc_node.tz.value = ctrl_tz

        for eye_jnt in eye_joints:
            name = NodeName(eye_jnt, desc='rotation', ext='LOC')
            side = name.side
            rot_ctrl_name = NodeName(rot_ctrl)
            rot_ctrl_name = rot_ctrl_name.replace_side(side)
            eye_loc = Node.create('transform', name=name, parent=rot_ctrl_name)
            eye_loc.align(eye_jnt)
            self.add_constraint('parent', eye_loc, eye_jnt, maintainOffset=True)

        # cleanup
        sys_grp = Node.create(
            'transform', name='EyesWithAimGrp', parent=self.ws_root)
        start_joint.set_parent(sys_grp)
