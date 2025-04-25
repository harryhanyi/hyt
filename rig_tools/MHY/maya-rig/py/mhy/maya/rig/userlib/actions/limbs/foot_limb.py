import maya.cmds as cmds

import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.utils as utils
import mhy.maya.rig.constants as const


class IKFKFoot(bl.BaseLimb):
    """
    IKFK foot limb class

    To create a three joints foot chain with heel node, foot inner node,
    and foot outer node.

    :limb type: foot
    """

    _LIMB_TYPE = 'foot'
    _DEFAULT_SIDE = 'L'
    _REPLACE_BIND_SOCKET = True

    _UI_ICON = 'foot'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value

        base_name = NodeName(
            part=part, side=side, num=None, ext=const.EXT_MARKER)
        data = []

        # main joint chain
        main_chain = {
            'aim_axis': 'x',
            'up_axis': 'y',
            'markers': []}
        for desc, pos, cns, up in zip(
                ('ankle', 'ball', 'toe'),
                ((9.4, 8.7, -4.4), (10.9, 0.0, 9.0), (11.8, 0.0, 19.1)),
                ('aim', 'aim', 'parent'),
                ((0, 1, 0), (0, 1, 0), None)):
            name = base_name.replace_desc(desc)
            main_chain['markers'].append({
                'name': name,
                'position': pos,
                'rotation': cns,
                'up_type': up})
        data.append(main_chain)

        # heel pivot
        chain = {
            'parent': main_chain['markers'][0]['name'],
            'markers': [
                {
                    'name': base_name.replace_desc('heel'),
                    'position': (8.8, 0, -9.8),
                    'rotation': main_chain['markers'][1]['name']
                }
            ]}
        data.append(chain)

        # outer pivot
        chain = {
            'parent': main_chain['markers'][0]['name'],
            'markers': [
                {
                    'name': base_name.replace_desc('outer'),
                    'position': (16.3, 0, 7.4),
                    'rotation': main_chain['markers'][1]['name']
                }
            ]}
        data.append(chain)

        # inner pivot
        chain = {
            'parent': main_chain['markers'][0]['name'],
            'markers': [
                {
                    'name': base_name.replace_desc('inner'),
                    'position': (4.2, 0, 8.8),
                    'rotation': main_chain['markers'][1]['name']
                }
            ]}
        data.append(chain)

        return data

    def resolve_input_skeleton(self):
        """Re-implemented to find pivot joints from the main chain."""
        super(IKFKFoot, self).resolve_input_skeleton()
        skel = self.rig_skeleton
        root = skel[0][0]
        heel_joint = None
        out_joint = None
        in_joint = None

        for each in root.get_children(type_='joint'):
            name = each.name.lower()
            if 'heel' in name:
                heel_joint = each
            elif 'outer' in name:
                out_joint = each
            elif 'inner' in name:
                in_joint = each
        if not heel_joint:
            raise exp.ActionError(
                'Failed locating heel joint under {}'.format(root))
        if not in_joint:
            raise exp.ActionError(
                'Failed locating inner joint under {}'.format(root))
        if not out_joint:
            raise exp.ActionError(
                'Failed locating outer joint under {}'.format(root))

        skel.append([heel_joint])
        skel.append([out_joint])
        skel.append([in_joint])
        self._set_rig_skeleton(skel)

    def connect_marker_system(self, parent_limb):
        """Connects this marker system to the parent marker system.
        Use "follow" connection mode if the parent is an arm or leg
        (to avoid overlapping markers).
        """
        parent_ms = parent_limb.marker_system
        if parent_ms:
            pmarker = parent_ms.get_marker(0, -1)
            mode = const.MarkerConnectMode.none
            if parent_limb.limb_type in ('arm', 'leg'):
                mode = const.MarkerConnectMode.follow
            self.marker_system.set_parent_marker(pmarker, mode=mode)

    def connect_parent(self, parent_limb):
        """Re-implemented to skip default constraint if
        the parent limb is arm or leg."""
        if not parent_limb.has_param('ik_end_ctrl'):
            super(IKFKFoot, self).connect_parent(parent_limb)

    def run(self):
        """Builds the limb ctrl rig."""
        foot_joint, ball_joint, toe_joint = self.rig_skeleton[0]
        heel_joint = self.rig_skeleton[1][0]
        outer_side_joint = self.rig_skeleton[2][0]
        inner_side_joint = self.rig_skeleton[3][0]
        limb_root = self.limb_root.value

        # create root nodes
        name = NodeName(foot_joint, desc='IKRoot', ext='GRP')
        ik_root = Node.create('transform', name=name, parent=limb_root)
        ik_root.parent_align(foot_joint)

        name = name.replace_desc('FKRoot')
        fk_root = Node.create('transform', name=name, parent=limb_root)
        fk_root.parent_align(foot_joint)

        # create ik joint chain
        name = NodeName(foot_joint, ext='IKJNT')
        foot_ik_jnt = foot_joint.duplicate(name=name, parentOnly=True)[0]
        foot_ik_jnt.v.value = False
        name = NodeName(ball_joint, ext='IKJNT')
        ball_ik_jnt = ball_joint.duplicate(name=name, parentOnly=True)[0]
        name = NodeName(toe_joint, ext='IKJNT')
        toe_ik_jnt = toe_joint.duplicate(name=name, parentOnly=True)[0]

        toe_ik_jnt.set_parent(ball_ik_jnt)
        ball_ik_jnt.set_parent(foot_ik_jnt)
        foot_ik_jnt.set_parent(ik_root)

        # create IK handle
        handle, effector = cmds.ikHandle(
            startJoint=foot_ik_jnt,
            endEffector=toe_ik_jnt,
            name=NodeName(foot_ik_jnt, desc='IKHANDLE', ext='HANDLE'),
            solver='ikSCsolver',
            sticky='sticky')
        handle = Node(handle)
        handle.v.value = False

        # create foot ctrl
        temp_loc = Node.create(
            'transform', name=NodeName(foot_ik_jnt, ext='TEMPLOC'))
        temp_loc.align(foot_ik_jnt, skipRotate=True)
        temp_tgt = Node.create(
            'transform', name=NodeName(foot_ik_jnt, ext='TEMPTGT'))
        temp_tgt.align(toe_ik_jnt, skipRotate=True)
        
        hight = foot_ik_jnt.get_translation(space='world')[1]
        cmds.move(
            hight, temp_tgt,
            worldSpace=True, absolute=True, moveY=True)
        length = mmath.distance(foot_ik_jnt, temp_tgt)
        width = mmath.distance(inner_side_joint, outer_side_joint)
        
        local_scale = (length / 2, hight / 2, width / 2)
        side_factor = 1
        if not self.is_aim_down():
            side_factor = -1
        aim_vec = (side_factor, 0, 0)
        world_up = (0, side_factor, 0)
        local_position = (0.5 * length * side_factor, -0.5 * hight, 0)

        self.add_constraint(
            'aim', temp_tgt, temp_loc,
            aimVector=aim_vec, worldUpVector=world_up)

        parent = self.get_parent_limb()
        if not parent or not parent.has_param('ik_end_ctrl'):
            foot_ctrl = self.add_ctrl(
                name=NodeName(temp_loc, ext='IKCTRL'),
                xform=temp_loc,
                parent=ik_root,
                shape='cube',
                scale=local_scale,
                pose=local_position)
            foot_fk_ctrl = self.add_ctrl(
                xform=foot_joint,
                ext='FKCTRL',
                shape='circle',
                parent=fk_root)
        else:
            # setup foot ctrl
            foot_ctrl = parent.ik_end_ctrl.value
            end_leg_jnt = parent.ik_end_joint.value
            foot_fk_ctrl = parent.fk_end_ctrl.value
            ik_fk_leg = parent.ikfk_blend_attr.value

            locs = foot_ctrl.get_children(type_='transform')
            cmds.parent(locs, world=True)
            foot_ctrl.offset_node.align(temp_loc, skipTranslate=True)
            foot_ctrl.shape.local_scale = local_scale
            foot_ctrl.shape.shape_type = 'cube'
            foot_ctrl.shape.local_position = local_position
            cmds.parent(locs, foot_ctrl)
            parent_limb = parent.limb_root.value
            parent_adv = parent_limb.shape.add_attr('bool', name='foot_advance_ctrl_visi', defaultValue=False, keyable=False)
            parent_adv.channelBox = True

            # connect ik joint chains
            ik_loc = end_leg_jnt.get_children(type_='transform')[0]
            ik_loc.set_parent(foot_ik_jnt)
            self.add_constraint(
                'point', end_leg_jnt, foot_ik_jnt, maintainOffset=True)
        ball_fk_loc = Node.create(
            'transform', parent=foot_fk_ctrl,
            name=NodeName(ball_joint, desc='fkBall', ext='LOC'))
        ball_fk_loc.parent_align(ball_joint)

        # create reverse nodes
        heel_ctrl = self.add_ctrl(
            xform=heel_joint,
            shape='circle',
            scale=(0.2, 0.2, 0.2),
            ext='ROTCTRL',
            rot=(90, 0, 0),
            color=(1, 1, 0),
            parent=ik_root)
        heel_roll = Node.create(
            'transform', parent=heel_ctrl,
            name=NodeName(heel_joint, ext='ROLL'))
        heel_roll.parent_align(heel_ctrl)
        self.add_constraint(
            'parent', foot_ctrl, heel_ctrl.plc_node, maintainOffset=True)

        tip_roll = Node.create(
            'transform', name=NodeName(toe_joint, desc='tip', ext='ROLL'))
        tip_roll.align(toe_joint, skipRotate=True)
        tip_roll.ty.value = 0

        ball_grp = Node.create(
            'transform', parent=heel_roll,
            name=NodeName(ball_joint, ext='GRP'))
        ball_grp.align(temp_loc, skipTranslate=True)
        ball_grp.align(ball_joint, skipRotate=True)
        trans = ball_grp.get_translation(space='world')
        trans=(trans[0],0,trans[2])
        ball_grp.set_translation(trans, space='world')
        tip_roll.align(ball_grp, skipTranslate=True)
        cmds.delete(temp_loc,temp_tgt)
        ball_rot = Node.create(
            'transform', parent=ball_grp, name=NodeName(ball_grp, ext='ROT'))
        ball_rot.parent_align(ball_grp)

        foot_roll_ctrl = self.add_ctrl(
            xform=ball_rot,
            name=NodeName(ball_rot, ext='ROLLCTRL'),
            shape='sphere',
            pos=(0, 0, hight * side_factor),
            scale=(0.2, 0.2, 0.2),
            parent=ball_grp)
        foot_roll_ctrl.lock(attrs='ts')

        inner_ctrl = self.add_ctrl(
            xform=inner_side_joint,
            shape='circle',
            scale=(0.2, 0.2, 0.2),
            ext='ROTCTRL',
            rot=(90, 0, 0),
            color=(1, 1, 0),
            parent=ball_rot)

        outer_ctrl = self.add_ctrl(
            xform=outer_side_joint,
            shape='circle',
            scale=(0.2, 0.2, 0.2),
            ext='ROTCTRL',
            rot=(90, 0, 0),
            color=(1, 1, 0),
            parent=inner_ctrl)

        tip_ctrl = self.add_ctrl(
            xform=tip_roll,
            shape='circle',
            scale=(0.2, 0.2, 0.2),
            ext='ROTCTRL',
            rot=(90, 0, 0),
            color=(1, 1, 0),
            parent=outer_ctrl)
        tip_roll.set_parent(tip_ctrl)
        handle.set_parent(tip_roll)

        ball_ctrl = self.add_ctrl(
            name=NodeName(ball_joint, ext='ROTCTRL'),
            shape='circle',
            scale=(0.4, 0.4, 0.4),
            color=(1, 1, 0),
            parent=tip_roll)
        ball_ctrl.plc_node.parent_align(ball_joint)

        toe_ctrl = self.add_ctrl(
            name=NodeName(ball_joint, ext='FKCTRL'),
            shape='circle',
            scale=(0.6, 0.6, 0.6),
            rot=(0, 0, 90),
            parent=ik_root)
        toe_ctrl.plc_node.parent_align(ball_joint)

        self.add_constraint(
            'parent', toe_ctrl, ball_joint, maintainOffset=True)

        # give animator the flexbility to change the foot roll behave
        """ the foot_roll_ball_mid will be the ball joint rotate value when foot roll ctrl rotate to -20, 
            the foot _roll_ball_end will be the ball joint rotate value when foot roll ctrl rotate to -45,
            the foot_roll_tip will be the tip rotate value when foot roll ctrl rotate to -45"""

        foot_roll_ball_mid = self.add_limb_attr('float', name='ballMid', keyable=False, maxValue=0, minValue=-90, defaultValue=-45)
        foot_roll_ball_end = self.add_limb_attr('float', name='ballEnd', keyable=False, maxValue=0, minValue=-90, defaultValue=-10)
        foot_roll_tip = self.add_limb_attr('float', name='tipEnd', keyable=False, maxValue=0, minValue=-90, defaultValue=-65 )
        foot_roll_ball_mid.channelBox = True
        foot_roll_ball_end.channelBox = True
        foot_roll_tip.channelBox = True
        # setup foot roll and side roll
        foot_roll_ctrl.ry >> ball_rot.ry
        foot_roll_ctrl.set_transform_limits(
            enableRotationX=(True, True),
            enableRotationZ=(True, True),
            rotationX=(-65, 65), rotationZ=(-45, 30))
        utils.set_driven_keys(
            driver_attr=foot_roll_ctrl.rx,
            driven_attr=inner_ctrl.offset_node.rx,
            value_pairs=((0, 0), (65, 65)),
            pre_inf='constant', post_inf='constant')
        utils.set_driven_keys(
            driver_attr=foot_roll_ctrl.rx,
            driven_attr=outer_ctrl.offset_node.rx,
            value_pairs=((0, 0), (-65, -65)),
            pre_inf='constant', post_inf='constant')
        name = NodeName(foot_roll_ctrl, desc='ballRoll', ext='RBFNODE')
        rbf_node = Node.create('rbfSolver', name=name)
        rbf_node.rbfMode.value = 0
        foot_roll_ctrl.rz>>rbf_node.nInput[0]
        rbf_node.poses[0].nKey[0].value = 0.0
        rbf_node.poses[1].nKey[0].value = -20
        rbf_node.poses[2].nKey[0].value = -45
        rbf_node.poses[3].nKey[0].value = 30
        rbf_node.poses[0].mValue[0].value = 0
        rbf_node.poses[3].mValue[0].value = 0
        foot_roll_ball_mid>>rbf_node.poses[1].mValue[0]
        foot_roll_ball_end>>rbf_node.poses[2].mValue[0]
        rbf_node.mOutput[0]>>ball_ctrl.offset_node.rz
        name = NodeName(foot_roll_ctrl, desc='tipRoll', ext='RVNODE')
        rv_node = Node.create('remapValue', name=name)
        foot_roll_ctrl.rz>>rv_node.inputValue
        rv_node.inputMax.value = -20
        rv_node.inputMin.value = -45
        rv_node.outputMax.value = 0
        foot_roll_tip>>rv_node.outputMin
        rv_node.outValue>>tip_roll.rz
        utils.set_driven_keys(
            driver_attr=foot_roll_ctrl.rz,
            driven_attr=heel_roll.rz,
            value_pairs=((0, 0), (30, 45)),
            pre_inf='constant', post_inf='constant')

        ik_fk_blend = self.add_limb_attr(
            'float', name='IKFKBlend',
            keyable=True, defaultValue=0, minValue=0, maxValue=1)
        name = NodeName(
            foot_joint, part=self.part.value,
            desc='IKFKBlend', ext='PMANODE')
        ik_fk_pma_node = Node.create('plusMinusAverage', name=name)
        ik_fk_pma_node.input1D[0].value = 1.0
        ik_fk_pma_node.operation.value = 2
        ik_fk_blend >> ik_fk_pma_node.input1D[1]
        if locs:
            for loc in locs:
                if 'handleLoc' in loc.name:
                    loc.set_parent(ball_ctrl)
            ik_fk_leg >> ik_fk_blend
        else:
            ik_fk_blend >> foot_ctrl.v
            ik_fk_pma_node.output1D >> foot_fk_ctrl.v
            cns = self.add_constraint(
                'parent', foot_ik_jnt, foot_fk_ctrl, foot_joint,
                maintainOffset=True)
            ik_fk_blend >> cns.attr(foot_ik_jnt.name + 'W0')
            ik_fk_pma_node.output1D >> cns.attr(foot_fk_ctrl.name + 'W1')

        # set foot ik fk ctrls visibility
        for ik_ctrl in (heel_ctrl, tip_ctrl, inner_ctrl,
                        outer_ctrl, ball_ctrl, foot_roll_ctrl):
            ik_ctrl.unlock(attrs='v')
            ik_fk_blend >> ik_ctrl.v
            ik_ctrl.lock(attrs='ts')

        toe_ctrl.lock(attrs='ts')
        advance_ctrls = self.add_limb_attr(
            'bool', name='advanced_controllers',
            defaultValue=False, keyable=True)
        for adv_ctrl in (inner_ctrl, outer_ctrl, ball_ctrl):
            adv_ctrl_shape = adv_ctrl.get_shapes()[0]
            advance_ctrls >> adv_ctrl_shape.v
        
        if parent_adv:
            parent_adv >> advance_ctrls

        cns = self.add_constraint(
            'parent', ball_ik_jnt, ball_fk_loc, toe_ctrl.plc_node,
            maintainOffset=True)
        ik_fk_blend >> cns.attr(ball_ik_jnt.name + 'W0')
        ik_fk_pma_node.output1D >> cns.attr(ball_fk_loc.name + 'W1')

        self.ctrl_leaf_parent = ball_joint.name
        

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        Bind skeleton = foot joint + ball joint.
        """
        foot_joint, ball_joint, _ = self.rig_skeleton[0]
        self.tag_bind_joint(foot_joint)
        self.tag_bind_joint(ball_joint, parent=foot_joint)
