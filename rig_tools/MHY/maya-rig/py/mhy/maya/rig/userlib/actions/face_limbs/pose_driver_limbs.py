"""
Limbs for poses build
"""
import maya.cmds as cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const
import mhy.maya.rig.utils as utils
import mhy.maya.rig.face.weighted_transform_system as wts


PIN_EXCLUDE = (
    'poseDriver_blinkline_00_L_FKCTRL',
    'poseDriver_blinkline_00_R_FKCTRL')


class WTSPoseDriver(bl.BaseLimb):
    """
    TODO doc

    :limb type: wts_pose_driver
    """

    _LIMB_TYPE = 'wts_pose_driver'

    _CTRL_VIS_ATTR = 'pose_ctrl'

    # -- input parameters

    @pa.str_param()
    def start_joint(self):
        """TODO doc"""

    @pa.str_param(default='CTRL')
    def ctrl_ext(self):
        """TODO doc."""

    @pa.vector3_param(default=(0, 0, .35))
    def ctrl_default_pos(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def create_pose_node(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def point_on_poly_consstraint(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def weighted_transform(self):
        """TODO doc."""

    @pa.str_param()
    def base_mesh(self):
        """TODO doc."""

    # --- output parameters

    @pa.str_param(output=True)
    def wts_pose_driver_null(self):
        """TODO doc."""

    @pa.str_param(output=True)
    def wts_pose_driver_mesh(self):
        """TODO doc."""

    # --- end of parameter definition

    def marker_data(self):
        """Returns the marker data dict.
        See marker_system.py to for details on the data format.

        TODO skipped for now and let the user input face root joint
        as the start_joint.
        """
        return

    def run(self):
        """Core execution method."""
        start_joint = self.start_joint.value
        if not start_joint or not cmds.objExists(start_joint):
            raise exp.ActionError(
                'Start joint empty or not found: {}'.format(start_joint))
        start_joint = Node(start_joint)

        # get input parameters
        ctrl_ext = self.ctrl_ext.value
        ctrl_scale = (1, 1, 1)
        ctrl_default_pos = self.ctrl_default_pos.value
        base_mesh = self.base_mesh.value
        if base_mesh:
            base_mesh = Node(base_mesh)

        # get face joints from start_joint,
        # face root joint should not be in bnd joint SET
        pose_driver_joints = start_joint.get_hierarchy(skip_self=True)

        # find joints who have child joints
        child_parent_joint_dict = {}
        for jnt in pose_driver_joints:
            for child in jnt.get_children(type_='joint'):
                child_parent_joint_dict[child] = jnt

        # create fk ctrl
        child_joint_ctrl_dict = {}
        for jnt in pose_driver_joints:
            pos = ctrl_default_pos[:]
            if NodeName(jnt).is_right:
                pos[2] *= -1

            ctrl = self.addCtrl(
                xform=jnt,
                ext=ctrl_ext,
                shape='circle',
                scale=ctrl_scale,
                pos=pos,
                group_exts=('PLC', 'INVERSE'))

            ctrl.lock('trsv')

            # set ctrl transform limits
            ctrl.set_limit(
                translationX=(0, 0),
                translationY=(0, 0),
                translationZ=(0, 0),
                enableTranslationX=(True, True),
                enableTranslationY=(True, True),
                enableTranslationZ=(True, True))

            # set pin excluded ctrls shape attrs
            if ctrl.name in PIN_EXCLUDE:
                local_rotate = (90.0, 0.0, 90.0)
                if 'blink' in ctrl.name:
                    local_rotate = (90.0, 0.0, 0.0)
                ctrl.shape.local_rotate = local_rotate
                ctrl.shape.local_scale = (1.0, .5, .5)
                ctrl.shape.shape_color = (0, 1, 1)
                ctrl.shape.shape_type = 'triangle'

            # get orig parent and child
            if jnt in child_parent_joint_dict.keys():
                child_joint_ctrl_dict[jnt] = ctrl

        # re-parent child ctrls to their real parents
        if child_joint_ctrl_dict:
            for jnt, ctrl in child_joint_ctrl_dict.items():
                parent = child_parent_joint_dict[jnt].ctrl
                cmds.parent(ctrl.plc_node, parent)

        # setup inverse and cleanup
        for ctrl in self.get_ctrls():
            utils.attr_connect(ctrl, ctrl.inverse_node, inverse=True)

        # tag closest point index
        if base_mesh:
            closest_point_index_tag(self.get_ctrls(), base_mesh)

        # add deformableTransform system
        if self.weighted_transform.value:
            pin_ctrls = [c for c in self.get_ctrls()
                         if c.name not in PIN_EXCLUDE]
            WTS = wts.WeightedTransformSystem(
                pin_ctrls,
                ctrl_ext=ctrl_ext,
                ws_node=self.ws_root,
                wts_grp_node='poseDriverCtrlSystem',
                type_='WTSPoseDriver',
                add_chew=False)
            wts_pose_driver_null, wts_pose_driver_mesh = WTS.create()
            self.wts_pose_driver_null.value = wts_pose_driver_null
            self.wts_pose_driver_mesh.value = wts_pose_driver_mesh

        # add pointOnPoly cns
        if self.point_on_poly.value:
            for ctrl in self.get_ctrls():
                if ctrl.name in PIN_EXCLUDE:
                    continue
                plc = ctrl.plc_node
                index = ctrl.get_tag('closestPointIndex')
                mesh = ctrl.get_tag('baseMesh')
                cp = '{}.vtx[{}]'.format(mesh, index)
                cmds.select(cp, plc, replace=True)
                cns = Node(cmds.pointOnPolyConstraint(maintainOffset=True)[0])
                for ax in 'XYZ':
                    cns.attr('constraintRotate' + ax).disconnect(
                        plc.attr('rotate' + ax))
            cmds.select(clear=True)

        # add pose node
        if self.create_pose_node.value:
            pose_node = Node.create(
                'MHYCtrl',
                name=NodeName(start_joint, ext='PoseWeightAttributes'),
                parent=self.ws_root,
                shape='circle',
                group_exts=[])
            pose_node.shape.shape_type = 1
            pose_node.v.value = False
            pose_node.lock()


class PoseDriver(bl.BaseLimb):
    """
    TODO doc
    """

    _LIMB_TYPE = 'pose_driver'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint
    _CTRL_VIS_ATTR = 'pose_ctrl'

    # -- input parameters

    @pa.bool_param(default=True)
    def create_pose_node(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def enable_scale(self):
        """TODO doc."""

    @pa.vector3_param(default=(0, 0, .35))
    def ctrl_default_pos(self):
        """TODO doc."""

    @pa.str_param()
    def base_mesh(self):
        """TODO doc."""
        
    @pa.bool_param(default=True)
    def delete_joints(self):
        """TODO doc."""

    def marker_data(self):
        """Returns the marker data dict.
        See marker_system.py to for details on the data format.

        TODO skipped for now and let the user input joints directly.
        """
        return

    def run(self):
        parent_joint = self.rig_skeleton[0][0]
        joint_list = parent_joint.get_hierarchy(skip_self=True)

        ctrl_scale = (0.15, 0.15, 0.15)
        ctrl_default_pos = self.ctrl_default_pos.value

        # add root pose driver ctrl
        root_ctrl = self.add_ctrl(
            xform=parent_joint,
            ext='FKCTRL',
            shape='sphere',
            pos=ctrl_default_pos,
            scale=ctrl_scale,
            group_exts=('PLC', 'OFFSET'))
        root_ctrl.shape.v.value = False
        root_ctrl.lock()

        self.add_constraint(
            'parent', root_ctrl, parent_joint, maintainOffset=True)
        if self.enable_scale.value:
            self.add_constraint(
                'scale', root_ctrl, parent_joint, maintainOffset=True)

        # add pose driver ctrl
        for jnt in joint_list:
            pos = ctrl_default_pos
            if NodeName(jnt).is_right:
                pos = (pos[0], pos[1], -pos[2])
            

            ctrl = self.add_ctrl(
                xform=jnt,
                ext='FKCTRL',
                parent=root_ctrl,
                shape='sphere',
                pos=pos,
                scale=ctrl_scale,
                color=(0, 1, 0),
                group_exts=('PLC', 'OFFSET'))

            self.add_constraint(
                'parent', ctrl, jnt, maintainOffset=True)
            if self.enable_scale.value:
                self.add_constraint(
                    'scale', ctrl, jnt, maintainOffset=True)

        # add pose node
        if self.create_pose_node.value:
            pose_node = Node.create(
                'MHYCtrl',
                name=NodeName(parent_joint, ext='PoseWeightAttributes'),
                group_exts=[])

            pose_node.set_parent(self.ws_root)
            pose_node.shape.shape_type = 4
            pose_node.v.value = False
            pose_node.lock()
            shape_node = pose_node.get_shapes()[0]
            shape_node.controllerType.value = 1
            shape_node.add_attr('message', name=const.POSE_MESH_MSG_ATTR)
            base_mesh_name = self.base_mesh.value
            if not base_mesh_name:
                self.error("Base Mesh is not defined. This will result in post process error")
                return
            base_mesh = Node(base_mesh_name)
            base_mesh.add_attr('message', name=const.POSE_MESH_MSG_ATTR)
            shape_node.attr(const.POSE_MESH_MSG_ATTR) >> base_mesh.attr(const.POSE_MESH_MSG_ATTR)
        '''
        # remove build joints    
        if self.delete_joints:
            cmds.delete(self.input_skeleton)
        '''


def closest_point_index_tag(tag_nodes, base_mesh, use_uv=False):
    """TODO doc"""
    base_mesh = Node(base_mesh).get_shapes()[0]

    cpom = Node.create('closestPointOnMesh')
    base_mesh.worldMesh >> cpom.inMesh

    for node in tag_nodes:
        node = Node(node)
        node.add_tag('baseMesh', base_mesh, force=True)

        # get closest point on base mesh
        pos = node.get_translation(space='world')
        cpom.set_attr('inPosition', pos)
        index = cpom.closestVertexIndex.value
        node.add_tag('closestPointIndex', index, force=True)

        if use_uv:
            for uv in 'uv':
                node.add_attr('double', name=uv)

            # get uv point
            u = cpom.parameterU.value
            v = cpom.parameterV.value
            node.parameterU.value = u
            node.parameterU.locked = True
            node.parameterV.value = v
            node.parameterV.locked = True

    cmds.delete(cpom)
