import math

import maya.cmds as cmds

import mhy.protostar.core.parameter as pa


from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath

import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.utils as utils
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.constants as const



class BaseIKFKChain(bl.BaseLimb):
    """
    IKFK chain base class containing shared class
    variables, parameters, and method implementations.
    """

    _LIMB_TYPE = None
    _DEFAULT_SIDE = 'L'
    _END_CTRL_NAME = 'end'

    # --- input parameters

    @pa.int_param(default=3, min_value=0)
    def upper_twist_joints(self):
        """The number of twist joints of upper limb."""

    @pa.int_param(default=3, min_value=0)
    def lower_twist_joints(self):
        """The number of twist joints of lower limb."""

    @pa.list_param()
    def end_space_names(self):
        """TODO doc"""

    @pa.list_param()
    def pole_vec_space_names(self):
        """TODO doc"""

    @pa.list_param()
    def end_space_targets(self):
        """TODO doc"""

    @pa.list_param()
    def pole_vec_space_targets(self):
        """TODO doc"""

    @pa.bool_param(default=False)
    def free_end_marker(self):
        """This parameter will free the rotation of the ending 
        marker of the limb. """

    # --- output parameters

    @pa.pyobject_param(output=True)
    def ik_end_ctrl(self):
        """The end IK ctrl."""

    @pa.pyobject_param(output=True)
    def fk_end_ctrl(self):
        """The end FK ctrl."""

    @pa.pyobject_param(output=True)
    def ik_end_joint(self):
        """The end IK joint."""

    @pa.pyobject_param(output=True)
    def ikfk_blend_attr(self):
        """The IKFK blend attribute."""

    # --- end of parameter definition

    def connect_marker_system(self, parent_limb):
        """Connects this marker system to the parent marker system.
        Use "follow" connection mode if the parent is a clavicle
        (to avoid overlapping markers).
        """
        parent_ms = parent_limb.marker_system
        if parent_ms:
            pmarker = parent_ms.get_marker(0, -1)
            mode = const.MarkerConnectMode.none
            if parent_limb.limb_type == 'clavicle':
                mode = const.MarkerConnectMode.follow
            self.marker_system.set_parent_marker(pmarker, mode=mode)


class IKFKChain(BaseIKFKChain):
    """
    IKFK chain rig with a single mid joint.
    """

    def run(self):
        """Builds the limb ctrl rig."""
        limb_root = self.limb_root.value
        start_joint = self.rig_skeleton[0][0]
        mid_joint = self.rig_skeleton[0][1]
        end_joint = self.rig_skeleton[0][-1]
        try:
            up_pos = self.get_marker(0, 1).up_ctrl.get_translation(space='world')
        except BaseException:
            up_pos = jutil.JointChain(start_joint, end_joint).get_pole_vector()

        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)
        long_axis = joint_chain.long_axis

        ctrl_scale = (1, 1, 1)
        end_space_names = self.end_space_names.value
        end_space_targets = self.end_space_targets.value
        end_spaces = zip(end_space_names, end_space_targets)

        pole_vec_space_names = self.pole_vec_space_names.value
        pole_vec_space_targets = self.pole_vec_space_targets.value
        pole_vec_spaces = zip(pole_vec_space_names, pole_vec_space_targets)

        end_name = self._END_CTRL_NAME

        name = NodeName(limb_root, desc='ScaleRoot', ext='GRP')
        scale_root = Node.create('transform', name=name, parent=limb_root)
        scale_root.parent_align(start_joint)

        # FK root
        name = name.replace_desc('FKRoot')
        fk_root = Node.create('transform', name=name, parent=scale_root)
        fk_root.align(start_joint)

        # IK root
        name = name.replace_desc('IKRoot')
        ik_root = Node.create('transform', name=name, parent=scale_root)
        ik_root.align(start_joint)

        # IK Chain
        name = NodeName(start_joint)
        name = name.replace_part(name.part + 'IK')
        start_ik_jnt = start_joint.duplicate(name=name, parentOnly=True)[0]

        name = NodeName(mid_joint)
        name = name.replace_part(name.part + 'IK')
        mid_ik_jnt = mid_joint.duplicate(name=name, parentOnly=True)[0]

        name = NodeName(end_joint)
        name = name.replace_part(name.part + 'IK')
        end_ik_jnt = end_joint.duplicate(name=name, parentOnly=True)[0]

        end_ik_jnt.set_parent(mid_ik_jnt)
        mid_ik_jnt.set_parent(start_ik_jnt)
        start_ik_jnt.set_parent(ik_root)
        start_ik_jnt.v.value = False
        self.add_constraint('parent', ik_root, start_ik_jnt, maintainOffset=True)

        # setup FK controls
        upper_limb_fk_ctrl = self.add_ctrl(
            name=NodeName(start_joint, ext='FKCTRL'),
            parent=fk_root,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        upper_limb_fk_ctrl.plc_node.align(start_joint)
        start_cns = self.add_constraint(
            'parent', upper_limb_fk_ctrl, start_ik_jnt,
            start_joint, maintainOffset=True)

        mid_fk_ctrl = self.add_ctrl(
            name=NodeName(mid_joint, ext='FKCTRL'),
            parent=upper_limb_fk_ctrl,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        mid_fk_ctrl.plc_node.align(mid_joint)
        mid_cns = self.add_constraint(
            'parent', mid_fk_ctrl, mid_ik_jnt, mid_joint, maintainOffset=True)

        end_fk_ctrl = self.add_ctrl(
            name=NodeName(end_joint, ext='FKCTRL'),
            parent=mid_fk_ctrl,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        end_fk_ctrl.plc_node.align(end_joint)
        # create end_ik_loc
        name = NodeName(end_ik_jnt, ext='LOC')
        end_ik_loc = Node.create('transform', name=name)
        end_ik_loc.parent_align(end_ik_jnt, keep_new_parent=True)
        end_cns = self.add_constraint(
            'parent', end_fk_ctrl, end_ik_loc, end_joint, maintainOffset=True)

        # create IK Handle, pole Vector
        handle, vector = self.create_ik_chain(
            parent=ik_root,
            start_joint=start_ik_jnt,
            end_joint=end_ik_jnt)
        vector.set_translation(up_pos, space='world')
        # create twist node
        name = NodeName(start_joint, ext='TWGRP')
        up_twist_grp = Node.create('transform', name=name, parent=ik_root)
        up_twist_grp.align(start_joint)
        up_twist_start_loc = Node.create('transform', name=name.replace_ext('STLOC'))
        up_twist_start_loc.align(up_twist_grp)
        up_twist_start_loc.set_parent(up_twist_grp)
        up_twist_driven_loc = Node.create('transform', name=name.replace_ext('DNLOC'))
        up_twist_driven_loc.align(up_twist_start_loc)
        up_twist_driven_loc.set_parent(up_twist_start_loc)
        up_twist_end_loc = Node.create('transform', name=name.replace_ext('ENDLOC'))
        up_twist_end_loc.align(up_twist_start_loc)
        up_twist_end_loc.set_parent(up_twist_start_loc)
        self.add_constraint('parent', start_joint, up_twist_start_loc, maintainOffset=True)
        long_axis_num = {'X':0, 'Y':1, 'Z':2, '-X':0, '-Y':1, '-Z':2}
        twist_node = self.add_twist_node(
            driver=up_twist_start_loc,
            driven=up_twist_driven_loc,
            twist=-1,
            swing=0,
            twistAxis=long_axis_num[long_axis])
        self.add_twist_node(
            driver=up_twist_start_loc,
            driven=up_twist_end_loc,
            twist=0,
            swing=0,
            twistAxis=long_axis_num[long_axis])

        up_auto_twist = self.add_limb_attr('float', name='up_auto_twist', defaultValue=1, 
            maxValue=1, minValue=0, keyable=True)       
        name = NodeName(start_joint, ext='TWMUL')
        up_twist_mul = Node.create('multiplyDivide', name=name)
        up_twist_mul.input1X.value=-1
        up_auto_twist >> up_twist_mul.input2X
        up_twist_mul.outputX >> twist_node.twist

        # add aditional twist amount
        up_twist = self.add_limb_attr('float', defaultValue=0, keyable=True, name='up_twist')
        up_twist >> up_twist_driven_loc.rx

        # create end ctrl with world orient and pole vector ctrl
        name = NodeName(end_joint, ext='IKCTRL')
        ik_end_ctrl = self.add_ctrl(
            name=name,
            parent=ik_root,
            shape='cube',
            rot=(0, 0, 90),
            scale=ctrl_scale)
        ik_end_ctrl.plc_node.align(end_joint, skipRotate=True)
        name = name.replace_desc(end_name)
        ik_end_local_ctrl = self.add_ctrl(
            xform=end_joint,
            name=name,
            parent=ik_end_ctrl,
            shape='circle',
            rot=(0, 0, 90),
            scale=ctrl_scale)
        local_scale = [i * 0.8 for i in ctrl_scale]
        name = name.replace_desc('gimble')
        gimble_ctrl = self.add_ctrl(
            name=name,
            xform=end_joint,
            parent=ik_end_local_ctrl,
            shape='sphereCurve',
            scale=local_scale)
        gimble_ctrl.lock(attrs='ts')

        name = NodeName(end_joint, desc='handleLoc', ext='LOC')
        handle_loc = ik_end_local_ctrl.add_child(name=name, insert=False)
        self.add_constraint(
            'point', handle_loc, handle, maintainOffset=True)

        # create end twist node
        name = NodeName(end_joint, ext='TWGRP')
        end_twist_grp = Node.create('transform', name=name, parent=ik_root)
        end_twist_grp.align(mid_joint)
        end_twist_start_loc = Node.create('transform', name=name.replace_ext('STLOC'), parent=end_twist_grp)
        end_twist_start_loc.align(end_twist_grp)
        end_twist_loc = Node.create('transform', name=name.replace_ext('TWLOC'), parent=end_twist_start_loc)
        end_twist_loc.align(end_joint, skipRotate=True)
        end_twist_loc.align(mid_joint, skipTranslate=True)
        end_twist_end_loc = Node.create('transform', name=name.replace_ext('ENDLOC'), 
            parent=end_twist_start_loc)
        end_twist_end_loc.align(end_joint, skipRotate=True)
        end_twist_end_loc.align(mid_joint, skipTranslate=True)
        self.add_constraint(
            'parent', mid_joint, end_twist_start_loc, maintainOffset=True)
        self.add_constraint(
            'parent', end_joint, end_twist_end_loc, maintainOffset=True)
        end_twist_node = self.add_twist_node(driver=end_twist_end_loc, driven=end_twist_loc,
            twist=1, swing=0, twistAxis=long_axis_num[long_axis])
        end_twist = self.add_limb_attr('float', name='low_auto_twist', defaultValue=1, 
            minValue=0, maxValue=1, keyable=True)
        end_twist >> end_twist_node.twist

        local_scale = [i * 0.4 for i in ctrl_scale]
        self._ik_pole_vec_ctrl = self.add_ctrl(
            name=NodeName(mid_joint, ext='IKCTRL'),
            parent=ik_root,
            scale=local_scale,
            shape='sphereCurve')
        self._ik_pole_vec_ctrl.plc_node.set_translation(up_pos, space='world')

        # setup twisting
        upper_twist_joints = self.upper_twist_joints.value
        lower_twist_joints = self.lower_twist_joints.value
        self._up_twist_joints = jutil.add_twist_joints(
            start_joint, mid_joint, amount=upper_twist_joints)
        self._lo_twist_joints = jutil.add_twist_joints(
            mid_joint, end_joint, amount=lower_twist_joints)

        # create ribbons
        data = self.create_ribbon(
            start=start_joint, end=mid_joint,
            attach_amount=upper_twist_joints, mode='start')
        up_rbn_root, up_rbn_off, up_start_off, up_mid_ctl, up_end_off, up_flcs = data

        data = self.create_ribbon(
            start=mid_joint, end=end_joint,
            attach_amount=lower_twist_joints, mode='end', avoid_overlap=True)
        lo_rbn_root, lo_rbn_off,  lo_start_off, lo_mid_ctl, lo_end_off, lo_flcs = data

        self.add_constraint(
            'parent', up_twist_driven_loc, up_start_off, maintainOffset=True)
        self.add_constraint(
            'orient', up_twist_end_loc, up_end_off, maintainOffset=True)
        self.add_constraint(
            'orient', mid_joint, lo_start_off, maintainOffset=True)
        self.add_constraint(
            'point', end_joint, lo_end_off, maintainOffset=True)
        self.add_constraint(
            'orient', end_twist_loc, lo_end_off, maintainOffset=True)
        self.add_constraint('parent', scale_root, up_rbn_off, maintainOffset=True)
        self.add_constraint('parent', scale_root, lo_rbn_off, maintainOffset=True)
        cmds.parent(
            up_mid_ctl.plc_node, lo_mid_ctl.plc_node, self.ctrl_root)
        ws_root = self.ws_root
        if ws_root:
            cmds.parent(up_rbn_root, lo_rbn_root, ws_root)

        # connect twist joints to follicle
        # could add ctrl for each joint in the future
        for i in range(upper_twist_joints):
            self._up_twist_joints[i].align(up_flcs[i], skipRotate=True)
            self.add_constraint(
                'parent', up_flcs[i], self._up_twist_joints[i],
                maintainOffset=True)
        for i in range(lower_twist_joints):
            self._lo_twist_joints[i].align(lo_flcs[i], skipRotate=True)
            self.add_constraint(
                'parent', lo_flcs[i], self._lo_twist_joints[i],
                maintainOffset=True)

        # setup mid bend ctrl
        local_scale = [i * 0.6 for i in ctrl_scale]
        name = NodeName(mid_joint, desc='bend', ext='IKCTRL')
        limb_mid_ctrl = self.add_ctrl(
            name=name,
            xform=mid_joint,
            parent=ik_root,
            scale=local_scale,
            color=(1, 1, 0),
            shape='sphereCurve')

        self.add_constraint(
            'point', mid_joint, limb_mid_ctrl.sdk_node, maintainOffset=False)

        # limb mid ctrl will rotate half as mid joint does
        name = NodeName(start_joint, ext='LOC')
        start_loc = Node.create('transform', name=name, parent=ik_root)
        start_loc.align(mid_joint)
        self.add_constraint('parent', start_joint, start_loc, maintainOffset=True)
        limb_mid_cns = self.add_constraint(
            'orient', start_loc, mid_joint,
            limb_mid_ctrl.sdk_node, maintainOffset=True)

        # create limb mid joint
        name = NodeName(mid_joint, desc='mid', ext=const.EXT_RIG_JOINT)
        self._mid_joint = mid_joint.duplicate(name=name, parentOnly=True)[0]
        self._mid_joint.set_parent(mid_joint)

        # setup limb mid joint orient constraints
        name = NodeName(start_joint, ext='BLENDLOC')
        blend_loc = Node.create('transform', name=name, parent=limb_mid_ctrl)
        blend_loc.parent_align(mid_joint)

        self.add_constraint(
            'parent', blend_loc, self._mid_joint, maintainOffset=True)
        self.add_constraint(
            'point', limb_mid_ctrl, up_end_off, maintainOffset=True)
        self.add_constraint(
            'point', limb_mid_ctrl, lo_start_off, maintainOffset=True)

        # lock attributes on controls
        ik_end_ctrl.lock(attrs='s')
        self._ik_pole_vec_ctrl.lock(attrs='sr')
        upper_limb_fk_ctrl.lock(attrs='ts')
        mid_fk_ctrl.lock(attrs='ts')
        end_fk_ctrl.lock(attrs='ts')
        up_mid_ctl.lock(attrs='s')
        lo_mid_ctl.lock(attrs='s')
        limb_mid_ctrl.lock(attrs='s')

        # set attributes on Limb shape
        ik_fk_blend = self.add_limb_attr(
            'float', name='IKFKBlend',
            keyable=True, defaultValue=1, minValue=0, maxValue=1)
        stretch_max = self.add_limb_attr(
            'float', name='stretchMax',
            keyable=True, defaultValue=1, minValue=1, maxValue=10)
        soft_mid = self.add_limb_attr(
            'float', name='softMid',
            keyable=True, defaultValue=0, minValue=0, maxValue=1)
        gimble_vis = self.add_limb_attr(
            'bool', name=end_name + 'GimbleCtrlVisi', keyable=True, defaultValue=False)
        limb_mid_vis = self.add_limb_attr(
            'bool', name='midCtrlVisi', keyable=True, defaultValue=True)
        limb_bendy_vis = self.add_limb_attr(
            'bool', name='BendyCtrlVisi', keyable=True, defaultValue=False)

        # setup IK ctrls space switch
        if list(pole_vec_spaces) == []:
            pole_vec_spaces = ['world', 'local', [self._END_CTRL_NAME, ik_end_local_ctrl] ]
        ik_end_ctrl.create_space_switch(spaces=end_spaces, default=1)
        self._ik_pole_vec_ctrl.create_scale_space_switch(spaces=pole_vec_spaces, default=0)
        upper_limb_fk_ctrl.create_space_switch(mode='rot', default=0)

        self.add_constraint(
            'orient', gimble_ctrl, end_ik_jnt, maintainOffset=True)
        self.add_constraint(
            'point', self._ik_pole_vec_ctrl, vector, maintainOffset=True)

        # setup limb stretch
        # setup limb stretch start and end locs
        name = NodeName(start_ik_jnt, desc='stretchStart', ext='LOC')
        stretch_start_loc = Node.create(
            'transform', name=name, parent=scale_root)
        name = name.replace_desc('stretchEnd')
        stretch_end_loc = Node.create(
            'transform', name=name, parent=scale_root)

        self.add_constraint(
            'point', scale_root, stretch_start_loc, maintainOffset=False)
        self.add_constraint(
            'point', gimble_ctrl, stretch_end_loc, maintainOffset=False)

        # get chain length
        length_upper = mmath.distance(start_ik_jnt, mid_ik_jnt)
        length_lower = mmath.distance(mid_ik_jnt, end_ik_jnt)
        length = length_upper + length_lower
        if not self.is_aim_down():
            length_upper *= -1
            length_lower *= -1

        # create utility nodes
        name = NodeName(
            part=self.part.value, desc='stretchMultiply', ext='MDNODE')
        stretch_mult_node = Node.create('multiplyDivide', name=name)
        stretch_mult_node.operation.value = 1

        name = name.replace_desc('stretchDivide')
        stretch_divide_node = Node.create('multiplyDivide', name=name)
        stretch_divide_node.operation.value = 2

        name = NodeName(name, desc='stretchDist', ext='DISTNODE')
        stretch_dist_node = Node.create('distanceBetween', name=name)

        stretch_start_loc.t >> stretch_dist_node.point1
        stretch_end_loc.t >> stretch_dist_node.point2
        stretch_dist_node.distance >> stretch_divide_node.input1X
        stretch_divide_node.input2X.value = length

        stretch_cdn01 = utils.create_condition(
            stretch_divide_node.outputX, 1, 1, stretch_divide_node.outputX, 4)
        stretch_cdn02 = utils.create_condition(
            stretch_cdn01, stretch_max,
            stretch_cdn01, stretch_max, 4)
        stretch_cdn02 >> stretch_mult_node.input1X
        stretch_cdn02 >> stretch_mult_node.input1Y

        stretch_mult_node.input2X.value = length_upper
        stretch_mult_node.input2Y.value = length_lower

        stretch_mult_node.outputX >> mid_ik_jnt.tx
        stretch_mult_node.outputY >> end_ik_jnt.tx

        # connect IKFKBlend attribute
        name = NodeName(name, desc='IKFKBlend', ext='PMANODE')
        ik_fk_pma = Node.create('plusMinusAverage', name=name)
        ik_fk_pma.input1D[0].value = 1.0
        ik_fk_pma.operation.value = 2
        ik_fk_blend >> ik_fk_pma.input1D[1]

        upper_limb_fk_ctrl.unlock(attrs='v')
        mid_fk_ctrl.unlock(attrs='v')
        end_fk_ctrl.unlock(attrs='v')
        ik_fk_pma.output1D >> upper_limb_fk_ctrl.v
        ik_fk_pma.output1D >> mid_fk_ctrl.v
        ik_fk_pma.output1D >> end_fk_ctrl.v
        ik_fk_pma.output1D >> start_cns.attr(upper_limb_fk_ctrl.name + 'W0')
        ik_fk_pma.output1D >> mid_cns.attr(mid_fk_ctrl.name + 'W0')
        ik_fk_pma.output1D >> end_cns.attr(end_fk_ctrl.name + 'W0')

        ik_end_ctrl.unlock(attrs='v')
        ik_fk_blend >> ik_end_ctrl.v
        self._ik_pole_vec_ctrl.unlock(attrs='v')
        ik_fk_blend >> self._ik_pole_vec_ctrl.v
        ik_fk_blend >> start_cns.attr(start_ik_jnt.name + 'W1')
        ik_fk_blend >> mid_cns.attr(mid_ik_jnt.name + 'W1')
        ik_fk_blend >> end_cns.attr(end_ik_loc.name + 'W1')

        # visibility attributes
        limb_mid_ctrl.unlock(attrs='v')
        up_mid_ctl.unlock(attrs='v')
        lo_mid_ctl.unlock(attrs='v')
        gimble_ctrl.unlock(attrs='v')
        limb_mid_vis >> limb_mid_ctrl.v
        limb_bendy_vis >> up_mid_ctl.v
        limb_bendy_vis >> lo_mid_ctl.v
        gimble_vis >> gimble_ctrl.v

        # setup soft limb mid
        name = NodeName(mid_joint, desc='softBlend', ext='PMANODE')
        soft_mid_pma = Node.create('plusMinusAverage', name=name)
        name = NodeName(mid_joint, desc='softBlend', ext='RMP')
        soft_mid_rmp = Node.create('remapValue', name=name)
        soft_mid_pma.input1D[0].value = 1.0
        soft_mid_pma.operation.value = 2
        soft_mid_rmp.outputMax.value = 0.5
        soft_mid_rmp.outputMin.value = 1.0
        soft_mid >> soft_mid_rmp.inputValue
        soft_mid_rmp.outValue >> soft_mid_pma.input1D[1]
        soft_mid_pma.output1D >> limb_mid_cns.attr(start_loc.name + 'W0')
        soft_mid_rmp.outValue >> limb_mid_cns.attr(mid_joint.name + 'W1')

        # setup scale
        for node in [start_joint, mid_joint, end_joint, self._mid_joint]:
            self.add_constraint('scale', scale_root, node)
        for node in self._up_twist_joints + self._lo_twist_joints:
            self.add_constraint('scale', scale_root, node)

        # setup leaf
        self.ctrl_leaf_parent = scale_root

        # set up output parameters for foot limb
        self.ik_end_ctrl.value = ik_end_local_ctrl
        self.ik_end_joint.value = end_ik_jnt
        self.fk_end_ctrl.value = end_fk_ctrl
        self.ikfk_blend_attr.value = ik_fk_blend

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        Bind skeleton = all the twist joints combined + the end joint.
        """
        # the main chain
        main_chain = (
            self._up_twist_joints[0],
            self._mid_joint,
            self.rig_skeleton[0][-1])
        for i, joint in enumerate(main_chain):
            parent = None
            if i > 0:
                parent = main_chain[i - 1]
            self.tag_bind_joint(joint, parent=parent)

        # twist joints
        for joint in self._up_twist_joints[1:]:
            self.tag_bind_joint(joint, parent=main_chain[0])
        for joint in self._lo_twist_joints:
            self.tag_bind_joint(joint, parent=main_chain[1])


class DJIKFKChain(BaseIKFKChain):
    """
    IKFK chain rig with 2 mid joints.
    """

    def run(self):
        """Builds the limb ctrl rig."""
        limb_root = self.limb_root.value
        start_joint, mid00_joint, mid01_joint, end_joint = self.rig_skeleton[0]
        try:
            up_pos = self.get_marker(0, 1).up_ctrl.get_translation(space='world')
        except BaseException:
            up_pos = jutil.JointChain(start_joint, end_joint).get_pole_vector()

        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)
        long_axis = joint_chain.long_axis

        ctrl_scale = (1, 1, 1)
        end_space_names = self.end_space_names.value
        end_space_targets = self.end_space_targets.value
        end_spaces = zip(end_space_names, end_space_targets)

        pole_vec_space_names = self.pole_vec_space_names.value
        pole_vec_space_targets = self.pole_vec_space_targets.value
        pole_vec_spaces = zip(pole_vec_space_names, pole_vec_space_targets)

        name = NodeName(limb_root, desc='ScaleRoot', ext='GRP')
        scale_root = Node.create('transform', name=name, parent=limb_root)
        scale_root.parent_align(start_joint)

        end_name = self._END_CTRL_NAME
        # FK root
        name = name.replace_desc('FKRoot')
        fk_root = Node.create('transform', name=name, parent=scale_root)
        fk_root.align(start_joint)

        # IK root
        name = name.replace_desc('IKRoot')
        ik_root = Node.create('transform', name=name, parent=scale_root)
        ik_root.align(start_joint)

        # IK Chain
        tx = self.driver_chain_length(self.rig_skeleton[0])
        if not self.is_aim_down():
            tx *= -1
        name = NodeName(start_joint)
        name = name.replace_part(name.part + 'IK')
        start_ik_jnt = start_joint.duplicate(name=name, parentOnly=True)[0]

        name = NodeName(mid00_joint)
        name = name.replace_part(name.part + 'IK')
        mid_ik_jnt = mid00_joint.duplicate(name=name, parentOnly=True)[0]
        mid_ik_jnt.tx.value = tx

        name = NodeName(end_joint)
        name = name.replace_part(name.part + 'IK')
        end_ik_jnt = end_joint.duplicate(name=name, parentOnly=True)[0]

        end_ik_jnt.set_parent(mid_ik_jnt)
        mid_ik_jnt.set_parent(start_ik_jnt)
        start_ik_jnt.set_parent(ik_root)
        start_ik_jnt.v.value = False
        mid_ik_jnt.orient_chain()

        # setup sub ik chain
        name = NodeName(start_joint, ext='SUBJNT')
        start_sub_jnt = start_joint.duplicate(name=name, parentOnly=True)[0]
        name = NodeName(mid00_joint, ext='SUBJNT')
        mid00_sub_jnt = mid00_joint.duplicate(name=name, parentOnly=True)[0]
        name = NodeName(mid01_joint, ext='SUBJNT')
        mid01_sub_jnt = mid01_joint.duplicate(name=name, parentOnly=True)[0]
        name = NodeName(end_joint, ext='SUBJNT')
        end_sub_jnt = end_joint.duplicate(name=name, parentOnly=True)[0]

        start_sub_jnt.v.value = False
        start_sub_jnt.set_parent(ik_root)
        mid00_sub_jnt.set_parent(start_sub_jnt)
        mid01_sub_jnt.set_parent(mid00_sub_jnt)
        end_sub_jnt.set_parent(mid01_sub_jnt)
        self.add_constraint('parent', start_ik_jnt, start_sub_jnt, maintainOffset=True)
        sub_handle, _ = self.create_ik_chain(
            parent=mid_ik_jnt,
            start_joint=mid00_sub_jnt,
            end_joint=end_sub_jnt)
        self.add_constraint('point', end_ik_jnt, sub_handle, maintainOffset=True)

        # setup FK controls
        upper_limb_fk_ctrl = self.add_ctrl(
            name=NodeName(start_ik_jnt, ext='FKCTRL'),
            parent=fk_root,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        upper_limb_fk_ctrl.plc_node.align(start_ik_jnt)
        start_cns = self.add_constraint(
            'orient', upper_limb_fk_ctrl, start_ik_jnt, maintainOffset=True)

        mid_fk_ctrl = self.add_ctrl(
            name=NodeName(mid_ik_jnt, ext='FKCTRL'),
            parent=upper_limb_fk_ctrl,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        mid_fk_ctrl.plc_node.align(mid_ik_jnt)
        mid_cns = self.add_constraint(
            'orient', mid_fk_ctrl, mid_ik_jnt, maintainOffset=True)

        end_fk_ctrl = self.add_ctrl(
            name=NodeName(end_ik_jnt, ext='FKCTRL'),
            parent=mid_fk_ctrl,
            scale=ctrl_scale,
            rot=(0, 0, 90),
            shape='circle')
        end_fk_ctrl.plc_node.align(end_ik_jnt)

        # create end_ik_loc
        name = NodeName(end_ik_jnt, ext='LOC')
        end_ik_loc = Node.create('transform', name=name)
        end_ik_loc.parent_align(end_ik_jnt, keep_new_parent=True)
        end_cns = self.add_constraint(
            'orient', end_fk_ctrl, end_ik_loc, end_sub_jnt, maintainOffset=True)

        # create IK Handle, pole Vector
        handle, vector = self.create_ik_chain(
            parent=ik_root,
            start_joint=start_ik_jnt,
            end_joint=end_ik_jnt)
        vector.set_translation(up_pos, space='world')
        # create twist node
         # create twist node
        name = NodeName(start_joint, ext='TWGRP')
        up_twist_grp = Node.create('transform', name=name, parent=ik_root)
        up_twist_grp.align(start_joint)
        up_twist_start_loc = Node.create('transform', name=name.replace_ext('STLOC'))
        up_twist_start_loc.align(up_twist_grp)
        up_twist_start_loc.set_parent(up_twist_grp)
        up_twist_driven_loc = Node.create('transform', name=name.replace_ext('DNLOC'))
        up_twist_driven_loc.align(up_twist_start_loc)
        up_twist_driven_loc.set_parent(up_twist_start_loc)
        up_twist_end_loc = Node.create('transform', name=name.replace_ext('ENDLOC'))
        up_twist_end_loc.align(up_twist_start_loc)
        up_twist_end_loc.set_parent(up_twist_start_loc)
        self.add_constraint('parent', start_joint, up_twist_start_loc, maintainOffset=True)
        long_axis_num = {'X':0, 'Y':1, 'Z':2, '-X':0, '-Y':1, '-Z':2}
        twist_node = self.add_twist_node(
            driver=up_twist_start_loc,
            driven=up_twist_driven_loc,
            twist=-1,
            swing=0,
            twistAxis=long_axis_num[long_axis])
        self.add_twist_node(
            driver=up_twist_start_loc,
            driven=up_twist_end_loc,
            twist=0,
            swing=0,
            twistAxis=long_axis_num[long_axis])

        up_auto_twist = self.add_limb_attr('float', name='up_auto_twist', defaultValue=1, 
            maxValue=1, minValue=0, keyable=True)       
        name = NodeName(start_joint, ext='TWMUL')
        up_twist_mul = Node.create('multiplyDivide', name=name)
        up_twist_mul.input1X.value=-1
        up_auto_twist >> up_twist_mul.input2X
        up_twist_mul.outputX >> twist_node.twist
        # add aditional twist amount
        up_twist = self.add_limb_attr('float', defaultValue=0, keyable=True, name='up_twist')
        up_twist >> up_twist_driven_loc.rx


        # create end ctrl and pole vector ctrl
        name = NodeName(end_joint, ext='IKCTRL')
        ik_end_ctrl = self.add_ctrl(
            name=name,
            parent=ik_root,
            shape='cube',
            rot=(0, 0, 90),
            scale=ctrl_scale)
        ik_end_ctrl.plc_node.align(end_joint, skipRotate=True)
        name = name.replace_desc(end_name)
        ik_end_local_ctrl = self.add_ctrl(
            xform=end_joint,
            name=name,
            parent=ik_end_ctrl,
            shape='circle',
            rot=(0, 0, 90),
            scale=ctrl_scale)
        local_scale = [i * 0.8 for i in ctrl_scale]
        name = name.replace_desc('gimble')
        gimble_ctrl = self.add_ctrl(
            name=name,
            xform=end_joint,
            parent=ik_end_local_ctrl,
            shape='sphereCurve',
            scale=local_scale)

        gimble_ctrl.lock(attrs='ts')

        name = NodeName(end_joint, desc='handleLoc', ext='LOC')
        handle_loc = ik_end_local_ctrl.add_child(name=name, insert=False)
        self.add_constraint('point', handle_loc, handle, maintainOffset=True)

        # create end twist node
        name = NodeName(end_joint, desc='twist', ext='GRP')
        end_tb = Node.create('transform', name=name, parent=ik_root)
        name = name.replace_ext('VEC')
        end_tv = Node.create('transform', name=name, parent=end_tb)
        name = name.replace_ext('DRC')
        end_drc = Node.create('transform', name=name, parent=end_tb)
        end_tv.tz.value = 1
        self.add_constraint(
            'parent', end_joint, end_tb, maintainOffset=False)

        aim_axis = (-1, 0, 0)
        if not self.is_aim_down():
            aim_axis = (1, 0, 0)

        self.add_constraint(
            'aim', mid01_joint, end_drc, aimVector=aim_axis,
            worldUpType='object', worldUpObject=end_tv,
            upVector=[0, 0, 1], maintainOffset=True)

        local_scale = [i * 0.4 for i in ctrl_scale]
        self._ik_pole_vec_ctrl = self.add_ctrl(
            name=NodeName(mid00_joint, ext='IKCTRL'),
            parent=ik_root,
            scale=local_scale,
            shape='sphereCurve')
        self._ik_pole_vec_ctrl.plc_node.set_translation(up_pos, space='world')

        # create end twist node
        name = NodeName(end_joint, ext='TWGRP')
        end_twist_grp = Node.create('transform', name=name, parent=ik_root)
        end_twist_grp.align(mid01_joint)
        end_twist_start_loc = Node.create('transform', name=name.replace_ext('STLOC'), parent=end_twist_grp)
        end_twist_start_loc.align(end_twist_grp)
        end_twist_loc = Node.create('transform', name=name.replace_ext('TWLOC'), parent=end_twist_start_loc)
        end_twist_loc.align(end_joint, skipRotate=True)
        end_twist_loc.align(mid01_joint, skipTranslate=True)
        end_twist_end_loc = Node.create('transform', name=name.replace_ext('ENDLOC'), 
            parent=end_twist_start_loc)
        end_twist_end_loc.align(end_joint)
        self.add_constraint(
            'parent', mid01_joint, end_twist_start_loc, maintainOffset=True)
        self.add_constraint(
            'parent', end_joint, end_twist_end_loc, maintainOffset=True)
        end_twist_node = self.add_twist_node(driver=end_twist_end_loc, driven=end_twist_loc,
            twist=1, swing=0, twistAxis=long_axis_num[long_axis])
        end_twist = self.add_limb_attr('float', name='low_auto_twist', defaultValue=1, 
            minValue=0, maxValue=1, keyable=True)
        end_twist >> end_twist_node.twist

        # setup twisting
        upper_twist_joints = self.upper_twist_joints.value
        lower_twist_joints = self.lower_twist_joints.value
        self._up_twist_joints = jutil.add_twist_joints(
            start_joint, mid00_joint, amount=upper_twist_joints)
        self._lo_twist_joints = jutil.add_twist_joints(
            mid01_joint, end_joint, amount=lower_twist_joints)

        # create ribbons
        data = self.create_ribbon(
            start=start_joint, end=mid00_joint,
            attach_amount=upper_twist_joints, mode='start')
        up_rbn_root, up_rbn_off, up_start_off, up_mid_ctl, up_end_off, up_flcs = data

        data = self.create_ribbon(
            start=mid01_joint, end=end_joint,
            attach_amount=lower_twist_joints, mode='end', avoid_overlap=True)
        lo_rbn_root, lo_rbn_off, lo_start_off, lo_mid_ctl, lo_end_off, lo_flcs = data

        self.add_constraint(
            'parent', up_twist_driven_loc, up_start_off, maintainOffset=True)
        self.add_constraint(
            'orient', up_twist_end_loc, up_end_off, maintainOffset=True)
        self.add_constraint(
            'orient', mid01_joint, lo_start_off, maintainOffset=True)
        self.add_constraint(
            'parent', end_twist_loc, lo_end_off, maintainOffset=True)
        self.add_constraint('parent', scale_root, up_rbn_off, maintainOffset=True)
        self.add_constraint('parent', scale_root, lo_rbn_off, maintainOffset=True)
        cmds.parent(
            up_mid_ctl.plc_node, lo_mid_ctl.plc_node, self.ctrl_root)
        ws_root = self.ws_root
        if ws_root:
            cmds.parent(up_rbn_root, lo_rbn_root, ws_root)

        # connect twist joints to follicle
        # could add ctrl for each joint in the future
        for i in range(upper_twist_joints):
            self._up_twist_joints[i].align(up_flcs[i], skipRotate=True)
            self.add_constraint(
                'parent', up_flcs[i], self._up_twist_joints[i],
                maintainOffset=True)
        for i in range(lower_twist_joints):
            self._lo_twist_joints[i].align(lo_flcs[i], skipRotate=True)
            self.add_constraint(
                'parent', lo_flcs[i], self._lo_twist_joints[i],
                maintainOffset=True)

        # setup mid bend ctrl
        local_scale = [i * 0.6 for i in ctrl_scale]
        name = NodeName(mid00_joint, desc='bend', ext='IKCTRL')
        limb_mid_ctrl = self.add_ctrl(
            name=name,
            xform=mid00_joint,
            parent=ik_root,
            scale=local_scale,
            color=(1, 1, 0),
            shape='sphereCurve')
        limb_mid_ctrl.plc_node.align(mid00_joint, mid01_joint, skipRotate=True)
        self.add_constraint(
            'parent', mid00_joint, limb_mid_ctrl.plc_node, maintainOffset=True)

        # create limb mid joint
        name = NodeName(mid00_joint, desc='midLimb', ext=const.EXT_RIG_JOINT)
        self._mid_joint = mid00_joint.duplicate(name=name, parentOnly=True)[0]
        self._mid_joint.set_parent(mid00_joint)
        self.add_constraint('parent', limb_mid_ctrl, self._mid_joint, maintainOffset=True)

        name = NodeName(up_end_off, ext='HELPLOC')
        up_end_off_hlpLoc = Node.create('transform', name=name, parent=limb_mid_ctrl)
        up_end_off_hlpLoc.align(up_end_off)
        self.add_constraint(
            'point', up_end_off_hlpLoc, up_end_off, maintainOffset=True)

        name = NodeName(lo_start_off, ext='HELPLOC')
        lo_start_off_hlpLoc = Node.create('transform', name=name, parent=limb_mid_ctrl)
        lo_start_off_hlpLoc.align(lo_start_off)
        self.add_constraint(
            'point', lo_start_off_hlpLoc, lo_start_off, maintainOffset=True)

        # lock attributes on controls
        ik_end_ctrl.lock(attrs='s')
        self._ik_pole_vec_ctrl.lock(attrs='sr')
        upper_limb_fk_ctrl.lock(attrs='ts')
        mid_fk_ctrl.lock(attrs='ts')
        end_fk_ctrl.lock(attrs='ts')
        up_mid_ctl.lock(attrs='s')
        lo_mid_ctl.lock(attrs='s')
        limb_mid_ctrl.lock(attrs='s')

        # set attributes on Limb shape
        ik_fk_blend = self.add_limb_attr(
            'float', name='IKFKBlend',
            keyable=True, defaultValue=1, minValue=0, maxValue=1)
        stretch_max = self.add_limb_attr(
            'float', name='stretchMax',
            keyable=True, defaultValue=1, minValue=1, maxValue=10)
        gimble_vis = self.add_limb_attr(
            'bool', name='GimbleCtrlVisi', keyable=True, defaultValue=False)
        mid_limb_vis = self.add_limb_attr(
            'bool', name='midLimbCtrlVisi', keyable=True, defaultValue=True)
        limb_bendy_vis = self.add_limb_attr(
            'bool', name='limbBendyCtrlVisi', keyable=True, defaultValue=False)

        # setup IK end ctrl space switch
        if list(pole_vec_spaces) == []:
            pole_vec_spaces = ['world', 'local', [self._END_CTRL_NAME, ik_end_local_ctrl] ]
        ik_end_ctrl.create_space_switch(spaces=end_spaces, default=1)
        self._ik_pole_vec_ctrl.create_scale_space_switch(spaces=pole_vec_spaces, default=0)
        upper_limb_fk_ctrl.create_space_switch(mode='rot', default=0)

        self.add_constraint(
            'orient', gimble_ctrl, end_ik_jnt, maintainOffset=True)
        self.add_constraint(
            'point', self._ik_pole_vec_ctrl, vector, maintainOffset=True)

        # setup limb stretch
        # setup limb stretch start and end locs
        name = NodeName(start_ik_jnt, desc='stretchStart', ext='LOC')
        stretch_start_loc = Node.create(
            'transform', name=name, parent=scale_root)
        name = name.replace_desc('stretchEnd')
        stretch_end_loc = Node.create(
            'transform', name=name, parent=scale_root)

        self.add_constraint(
            'point', scale_root, stretch_start_loc, maintainOffset=False)
        self.add_constraint(
            'point', gimble_ctrl, stretch_end_loc, maintainOffset=False)

        mid_ik_tx = mid_ik_jnt.tx.value
        end_ik_tx = end_ik_jnt.tx.value

        mid00_sub_tx = mid00_sub_jnt.tx.value
        mid01_sub_tx = mid01_sub_jnt.tx.value
        end_sub_tx = end_sub_jnt.tx.value

        # get chain length
        length_upper = mmath.distance(start_ik_jnt, mid_ik_jnt)
        length_lower = mmath.distance(mid_ik_jnt, end_ik_jnt)
        length = length_upper + length_lower

        # create utility nodes
        name = NodeName(
            part=self.part.value, desc='stretchMultiply', ext='MDNODE')
        stretch_mult_node = Node.create('multiplyDivide', name=name)
        stretch_mult_node.operation.value = 1

        name = name.replace_desc('stretchDivide')
        stretch_divide_node = Node.create('multiplyDivide', name=name)
        stretch_divide_node.operation.value = 2

        name = NodeName(name, desc='stretchDist', ext='DISTNODE')
        stretch_dist_node = Node.create('distanceBetween', name=name)

        stretch_start_loc.t >> stretch_dist_node.point1
        stretch_end_loc.t >> stretch_dist_node.point2
        stretch_dist_node.distance >> stretch_divide_node.input1X
        stretch_divide_node.input2X.value = length

        stretch_cdn01 = utils.create_condition(
            stretch_divide_node.outputX, 1, 1, stretch_divide_node.outputX, 4)
        stretch_cdn02 = utils.create_condition(
            stretch_cdn01, stretch_max,
            stretch_cdn01, stretch_max, 4)
        stretch_cdn02 >> stretch_mult_node.input1X
        stretch_cdn02 >> stretch_mult_node.input1Y

        stretch_mult_node.input2X.value = mid_ik_tx
        stretch_mult_node.input2Y.value = end_ik_tx

        stretch_mult_node.outputX >> mid_ik_jnt.tx
        stretch_mult_node.outputY >> end_ik_jnt.tx

        name = NodeName(part=self.part.value, desc='stretchSubMultiply', ext='MDNODE')
        stretch_sub_mult_node = Node.create('multiplyDivide', name=name)
        stretch_sub_mult_node.operation.value = 1

        stretch_sub_mult_node.input2X.value = mid00_sub_tx
        stretch_sub_mult_node.input2Y.value = mid01_sub_tx
        stretch_sub_mult_node.input2Z.value = end_sub_tx
        stretch_cdn02 >> stretch_sub_mult_node.input1X
        stretch_cdn02 >> stretch_sub_mult_node.input1Y
        stretch_cdn02 >> stretch_sub_mult_node.input1Z

        stretch_sub_mult_node.outputX >> mid00_sub_jnt.tx
        stretch_sub_mult_node.outputY >> mid01_sub_jnt.tx
        stretch_sub_mult_node.outputZ >> end_sub_jnt.tx

        # setup mid_01 joint for binding skeleton
        self._mid01_joint = mid01_joint

        # connect IKFKBlend attribute
        name = NodeName(name, desc='IKFKBlend', ext='PMANODE')
        ik_fk_pma = Node.create('plusMinusAverage', name=name)
        ik_fk_pma.input1D[0].value = 1.0
        ik_fk_pma.operation.value = 2
        ik_fk_blend >> ik_fk_pma.input1D[1]
        ik_fk_blend >> handle.ikBlend
        upper_limb_fk_ctrl.unlock(attrs='v')
        mid_fk_ctrl.unlock(attrs='v')
        end_fk_ctrl.unlock(attrs='v')
        ik_fk_pma.output1D >> upper_limb_fk_ctrl.v
        ik_fk_pma.output1D >> mid_fk_ctrl.v
        ik_fk_pma.output1D >> end_fk_ctrl.v
        ik_fk_pma.output1D >> start_cns.attr(upper_limb_fk_ctrl.name + 'W0')
        ik_fk_pma.output1D >> mid_cns.attr(mid_fk_ctrl.name + 'W0')
        ik_fk_pma.output1D >> end_cns.attr(end_fk_ctrl.name + 'W0')
        ik_fk_blend >> end_cns.attr(end_ik_loc.name + 'W1')

        ik_end_ctrl.unlock(attrs='v')
        ik_fk_blend >> ik_end_ctrl.v
        self._ik_pole_vec_ctrl.unlock(attrs='v')
        ik_fk_blend >> self._ik_pole_vec_ctrl.v

        # visibility attributes
        limb_mid_ctrl.unlock(attrs='v')
        up_mid_ctl.unlock(attrs='v')
        lo_mid_ctl.unlock(attrs='v')
        gimble_ctrl.unlock(attrs='v')
        mid_limb_vis >> limb_mid_ctrl.v
        limb_bendy_vis >> up_mid_ctl.v
        limb_bendy_vis >> lo_mid_ctl.v
        gimble_vis >> gimble_ctrl.v

        # constrian rig joints at the end so that they won't be
        # altered by the ctrl rig.
        self.add_constraint('parent', start_sub_jnt, start_joint, maintainOffset=True)
        self.add_constraint('parent', mid00_sub_jnt, mid00_joint, maintainOffset=True)
        self.add_constraint('parent', mid01_sub_jnt, mid01_joint, maintainOffset=True)
        self.add_constraint('parent', end_sub_jnt, end_joint, maintainOffset=True)

        # setup scale
        for node in [start_joint, mid00_joint, mid01_joint, end_joint, self._mid_joint]:
            self.add_constraint('scale', scale_root, node)
        for node in self._up_twist_joints + self._lo_twist_joints:
            self.add_constraint('scale', scale_root, node)

        # setup leaf
        self.ctrl_leaf_parent = scale_root

        # set up output parameters for foot limb
        self.ik_end_ctrl.value = ik_end_local_ctrl
        self.ik_end_joint.value = end_ik_jnt
        self.fk_end_ctrl.value = end_fk_ctrl
        self.ikfk_blend_attr.value = ik_fk_blend

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        Bind skeleton = all the twist joints combined + the end joint.
        """
        # the main chain
        main_chain = (
            self._up_twist_joints[0],
            self._mid_joint,
            self._mid01_joint,
            self.rig_skeleton[0][-1])
        for i, joint in enumerate(main_chain):
            parent = None
            if i > 0:
                parent = main_chain[i - 1]
            self.tag_bind_joint(joint, parent=parent)

        # twist joints
        for joint in self._up_twist_joints[1:]:
            self.tag_bind_joint(joint, parent=main_chain[0])
        for joint in self._lo_twist_joints:
            self.tag_bind_joint(joint, parent=main_chain[2])

    def driver_chain_length(self, joint_chain=[]):
        """
        Calculate the lengthe of the first bone's length of the 3 joint chain
        to drive the four joint chain.
        """

        length = len(joint_chain)
        if length != 4:
            raise RuntimeError('The double mid joint chain has to have 4 joints!')
        jnt1 = joint_chain[0]
        jnt2 = joint_chain[1]
        jnt3 = joint_chain[2]
        jnt4 = joint_chain[3]

        L = abs(jnt2.tx.value) + abs(jnt3.tx.value) + abs(jnt4.tx.value)
        J2P = jnt2.get_translation(space='world', as_tuple=False)
        J4P = jnt4.get_translation(space='world', as_tuple=False)
        J1P = jnt1.get_translation(space='world', as_tuple=False)
        V0 = J2P - J1P
        V1 = J4P - J1P
        cosT = math.cos(V0.angle(V1))
        tx = (pow(L, 2) - pow(V1.length(), 2)) / 2 / (L - cosT * V1.length())
        return tx
