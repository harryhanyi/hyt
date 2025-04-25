import mhy.protostar.core.parameter as pa

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.constants as const
import maya.cmds as cmds

class IKFKNeckHead(bl.BaseLimb):
    """IKFKNeckhead limb class

    :limb type: neck
    """

    _LIMB_TYPE = 'neck'

    _UI_ICON = 'neck'

    # --- input parameters

    @pa.str_param(default='head')
    def head_name(self):
        """Name of the head token."""

    @pa.enum_param(items=const.ROT_ORDERS, default='xzy')
    def rotate_order(self):
        """The rotation order."""

    @pa.bool_param(default=False)
    def enable_scale(self):
        """If True, enable scale constraint."""

    @pa.int_param(default=3, min_value=2)
    def num_joints(self):
        """Neck joint account."""
    # --- end of parameter definition

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        head_name = self.head_name.value
        side = self.side.enum_value
        data = {
            'aim_axis': 'x',
            'up_axis': 'z',
            'up_ctrl_position': (0.0, 144.5, 9.8),
            'markers': []}

        sp = (0.0, 144.5, 1.8)
        ep = (0.0, 159.0, 4.8)
        count = self.num_joints.value
        for i in range(0, count):
            if i < count-1:
                p = part
                num = i
                cns = 'aim'
            else:
                p = head_name
                num = None
                cns = None

            pos= (0.0, sp[1]+(ep[1]-sp[1])*i/(count-1), sp[1]+(ep[2]-sp[2])*i/(count-1))
            name = NodeName(part=p, side=side, num=num, ext=const.EXT_MARKER)
            data['markers'].append({
                'name': name,
                'position': pos,
                'rotation': cns,
                'up_type': 'ctrl',
            })

        return data
    def run(self):
        """Builds the limb ctrl rig."""
        head_ctrl = None
        neck_ctrls = []

        base_joint = self.rig_skeleton[0][0]
        head_joint = self.rig_skeleton[0][-1]
        self.debug('Head Joint: {}'.format(head_joint))

        # get joint chain
        joint_chain = jutil.JointChain(
            start=self.rig_skeleton[0][0], end=self.rig_skeleton[0][-1])
        self.debug('Joint Chain Length: {}'.format(joint_chain.chain_length))

        amount = len(self.rig_skeleton[0])
        # check orientation
        if joint_chain.long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(joint_chain.long_axis))
            long_axis = joint_chain.long_axis
        else:
            self.warn('Not all joint has the same orientation.')
            long_axis = 'X'

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set neck joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # setup IK
        ik_ctrl = self.add_ctrl(xform=head_joint,
            ext='IKCTRL',
            shape='circle',
            parent=self.ctrl_root,
            rot=(0,0,90),
            rot_order=0)
        channel = 's'
        for axis in 'XYZ':
            if axis not in long_axis:
                channel = channel + 'r' + axis
        ik_ctrl.lock(attrs=channel)
        name = NodeName(base_joint, ext='IKJNT')
        ik_base_jnt = base_joint.duplicate(
            name=name, 
            parentOnly=True)[0]
        name = NodeName(head_joint, ext='IKJNT')
        ik_head_jnt = head_joint.duplicate(
            name=name,
            parentOnly=True)[0]
        aim_vecs = {'X':[(1,0,0),(0,1,0)], '-X':[(-1,0,0),(0,1,0)],
            'Y':[(0,1,0),(0,0,1)], '-Y':[(0,-1,0),(0,0,1)],
            'Z':[(0,0,1),(1,0,0)], '-Z':[(0,0,-1),(1,0,0)]}
        vecs = aim_vecs[long_axis]
        temp_cns = self.add_constraint('aim', ik_head_jnt, ik_base_jnt,
            aimVector=vecs[0], upVector=vecs[1],worldUpVector=vecs[1],
            worldUpType='objectrotation', worldUpObject=base_joint,
            maintainOffset=False)
        cmds.delete(temp_cns)
        ik_head_jnt.set_parent(ik_base_jnt)
        ik_base_jnt.set_parent(self.ctrl_root)
        handle = Node.create('ikHandle',startJoint=ik_base_jnt, 
            endEffector=ik_head_jnt, 
            solver='ikSCsolver', 
            name=name.replace_ext('IKHDL'))[0]
        handle.set_parent(self.ctrl_root)
        handle.v.value = 0
        ik_base_jnt.v.value = 0
        self.add_constraint('point', ik_ctrl, handle, maintainOffset=False)
        # swing nodes
        name = NodeName(ik_base_jnt, ext='SWLOC')
        swing_loc = Node.create('transform', name=name, parent=self.ctrl_root)
        swing_loc.align(ik_base_jnt, skipRotate=False)
        #swing_drc = Node.create('transform', name=name.replace_ext('SWDRC'), 
        #    parent=ik_base_jnt)
        long_axis_num = {'X':0, 'Y':1, 'Z':2, '-X':0, '-Y':1, '-Z':2}
        self.add_twist_node(driver=ik_base_jnt, 
            driven=swing_loc, 
            twist=0, 
            swing=1, 
            twistAxis=long_axis_num[long_axis])
        auto_bend = self.add_limb_attr('float', 
            name='auto_bend', 
            defaultValue=1, 
            maxValue=1, 
            minValue=0, 
            keyable=True)
        twist_md = Node.create('multiplyDivide', name=name.replace_ext('TWMD'))
        twist_md.operation.value = 2
        long_rot = 'r' + long_axis.lower()[-1]
        long_tran = 't' + long_axis.lower()[-1]
        ik_ctrl.attr(long_rot) >> twist_md.input1X
        twist_md.input2X.value = amount
        # stretch
        stretch = self.add_limb_attr('float', name='stretch', defaultValue=0, minValue=0, maxValue=1, keyable=True)
        name = NodeName(ik_ctrl, ext='DIST')
        dist_node = Node.create('distanceBetween', name=name)
        ik_ctrl.worldMatrix >> dist_node.inMatrix1
        ik_base_jnt.worldMatrix >> dist_node.inMatrix2
        origin_dist = dist_node.distance.value
        stretch_sub = Node.create('plusMinusAverage', name=name.replace_ext('SUB'))
        stretch_sub.operation.value = 2
        dist_node.distance >> stretch_sub.input1D[0]
        stretch_sub.input1D[1].value = origin_dist
        stretch_div = Node.create('multiplyDivide', name=name.replace_ext('DIV'))
        stretch_div.operation.value = 2
        stretch_sub.output1D >> stretch_div.input1X
        stretch_div.input2X.value = origin_dist
        stretch_mult = Node.create('multiplyDivide', name=name.replace_ext('MUL'))
        stretch_div.outputX >> stretch_mult.input1X
        stretch >> stretch_mult.input2X
        stretch_add = Node.create('plusMinusAverage', name=name.replace_ext('ADD'))
        stretch_add.input1D[0].value = 1
        stretch_mult.outputX >> stretch_add.input1D[1]

        # create main FK ctrls
        ctrls = []
        joint = None
        for index, joint in enumerate(self.rig_skeleton[0]):
            #ctrls = self.get_ctrls()
            parent = ctrls[-1] if ctrls else self.ctrl_root
            # auto rotate node
            name = NodeName(joint, ext='RTGRP')
            rot_grp = Node.create('transform', name=name, parent=parent)
            rot_loc = Node.create('transform', name=name.replace_ext('RTLOC'), parent=rot_grp)
            rot_grp.align(joint)          
            parent = rot_loc         
            
            ctrl_shape = 'circle'
            if joint == head_joint:
                ctrl_shape = 'cube'

            ctrl = self.add_ctrl(
                xform=joint,
                parent=parent,
                ext='FKCTRL',
                shape=ctrl_shape,
                rot=(0, 0, 90),
                rot_order=0)
            twist_md.outputX >> ctrl.offset_node.attr(long_rot)
            if index == 0:
                self.add_constraint('orient', swing_loc, rot_loc, maintainOffset=True)
                bend_md = Node.create('multiplyDivide', name=name.replace_ext('RTMD'))
                rot_loc.rotate >> bend_md.input1
                for axis in 'XYZ':
                    auto_bend >> bend_md.attr('input2' + axis)
            else:
                mult_node = Node.create('multiplyDivide', name=name.replace_ext('STMUL'))
                stretch_add.output1D >> mult_node.input1X
                mult_node.input2X.value = rot_grp.get_attr(long_tran)
                mult_node.outputX >> rot_grp.attr(long_tran)
                bend_md.output >> rot_loc.rotate

            # get head ctrl and neckCtrls
            self.add_constraint('parent', ctrl, joint, maintainOffset=True)
            if self.enable_scale.value:
                self.add_constraint('scale', ctrl, joint, maintainOffset=True)
            ctrls.append(ctrl)

        # set leaf parent node
        if joint and joint == head_joint:
            self.ctrl_leaf_parent = ctrls[-1].name

        ctrls[-1].create_scale_space_switch(mode='rot')


class NeckHead(bl.BaseLimb):
    """Neckhead limb class

    :limb type: neck
    """

    _LIMB_TYPE = 'neck'

    _UI_ICON = 'neck'

    # --- input parameters

    @pa.str_param(default='head')
    def head_name(self):
        """Name of the head token."""

    @pa.enum_param(items=const.ROT_ORDERS, default='xzy')
    def rotate_order(self):
        """The rotation order."""

    @pa.bool_param(default=False)
    def enable_scale(self):
        """If True, enable scale constraint."""

    @pa.int_param(default=3, min_value=2)
    def num_joints(self):
        """Neck joint account."""

    # --- end of parameter definition

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        head_name = self.head_name.value
        side = self.side.enum_value
        data = {
            'aim_axis': 'x',
            'up_axis': 'z',
            'up_ctrl_position': (0.0, 144.5, 9.8),
            'markers': []}

        sp = (0.0, 144.5, 1.8)
        ep = (0.0, 159.0, 4.8)
        count = self.num_joints.value
        for i in range(0, count):
            if i < count-1:
                p = part
                num = i
                cns = 'aim'
            else:
                p = head_name
                num = None
                cns = None

            pos= (0.0, sp[1]+(ep[1]-sp[1])*i/(count-1), sp[1]+(ep[2]-sp[2])*i/(count-1))
            name = NodeName(part=p, side=side, num=num, ext=const.EXT_MARKER)
            data['markers'].append({
                'name': name,
                'position': pos,
                'rotation': cns,
                'up_type': 'ctrl',
            })

        return data

    def run(self):
        """Builds the limb ctrl rig."""
        head_ctrl = None
        neck_ctrls = []

        base_joint = self.rig_skeleton[0][0]
        head_joint = self.rig_skeleton[0][-1]
        self.debug('Head Joint: {}'.format(head_joint))

        # get joint chain
        joint_chain = jutil.JointChain(
            start=self.rig_skeleton[0][0], end=self.rig_skeleton[0][-1])
        self.debug('Joint Chain Length: {}'.format(joint_chain.chain_length))

        # check orientation
        if joint_chain.long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(joint_chain.long_axis))
        else:
            self.warn('Not all joint has the same orientation.')

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set neck joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # create main FK ctrls
        ctrl_scale = (1, 1, 1)
        ctrls = []

        joint = None
        for _, joint in enumerate(self.rig_skeleton[0]):
            ctrls = self.get_ctrls()
            parent = ctrls[-1] if ctrls else self.ctrl_root

            ctrl_shape = 'circle'
            if joint == head_joint:
                ctrl_shape = 'cube'
                ctrl_scale = [2.5 * x for x in ctrl_scale]

            ctrl = self.add_ctrl(
                xform=joint,
                parent=parent,
                ext='FKCTRL',
                shape=ctrl_shape,
                rot=(0, 0, 90),
                rot_order=0,
                scale=ctrl_scale)

            # get head ctrl and neckCtrls
            if joint == head_joint:
                head_ctrl = ctrl
                name = NodeName(ctrl, ext='CNSLOC')
                cns_loc = Node.create('transform', name=name)
                cns_loc.align(ctrl)
                cns_loc.set_parent(ctrl.offset_node)
                name = NodeName(ctrl, ext='CNS')
                self.add_constraint('parent', cns_loc, joint, maintainOffset=True)
            else:
                neck_ctrls.append(ctrl)
                self.add_constraint('parent', ctrl, joint, maintainOffset=True)

            if self.enable_scale.value:
                self.add_constraint('scale', ctrl, joint, maintainOffset=True)

            ctrls.append(ctrl)

        # set leaf parent node
        if joint and joint == head_joint:
            self.ctrl_leaf_parent = ctrls[-1].name

        # create ik chain
        name = NodeName(base_joint, ext='IKJNT')
        start_jnt = base_joint.duplicate(name=name, parentOnly=True)[0]
        start_jnt.set_parent(self.ws_root)
        start_ctrl = neck_ctrls[0]
        self.add_constraint('point', start_ctrl.plc_node, start_jnt, maintainOffset=True)
        name = NodeName(head_joint, ext='IKJNT')
        end_jnt = head_joint.duplicate(name=name, parentOnly=True)[0]
        end_jnt.set_parent(start_jnt)
        name = NodeName(base_joint, desc='stretch', ext='IKHDL')
        result = cmds.ikHandle(
            solver='ikSCsolver',
            startJoint=start_jnt,
            endEffector=end_jnt,
            name=name)
        ik_handle, _ = [Node(n) for n in result]
        ik_handle.set_parent(self.ws_root)
        self.add_constraint(
            'point', head_ctrl, ik_handle, maintainOffset=True)

        # add stretch switch attribute
        stretch = self.add_limb_attr(
            'float', name='stretch', keyable=True,
            defaultValue=0, minValue=0, maxValue=1)
        name = NodeName(start_jnt, desc='stretch', ext='DIST')
        distance = Node.create('distanceBetween', name=name)
        start_ctrl.plc_node.worldMatrix[0] >> distance.inMatrix1
        head_ctrl.worldMatrix[0] >> distance.inMatrix2
        name = NodeName(start_jnt, desc='stretch', ext='RMP')
        remap = Node.create('remapValue', name=name)
        distance.distance >> remap.outputMax
        remap.outputMin.value = distance.distance.value
        stretch >> remap.inputValue
        remap.outValue >> end_jnt.tx

        # Negation Setup
        func_axis_dict = {
            'X': {
                'twist': ('rx', 0.55),
                'lateral': ('ry', 0.35),
                'forward': ('rz', 0.65)},
            'Y': {
                'twist': ('ry', 0.55),
                'lateral': ('rz', 0.35),
                'forward': ('rx', 0.65)}}

        channel_dict = func_axis_dict.get(joint_chain.long_axis[-1])
        if not channel_dict:
            self.error('Limb NeckHead does not work on Z down joint chain, '
                       'this option can be added if necessary.')

        # insert negation nodes and make relatonship dict
        neck_groups = []
        for ctrl in ctrls:
            name = NodeName(ctrl, ext='NEG')
            # insert
            if ctrl == head_ctrl:
                neg = ctrl.sdk_node.add_child(name=name)
                head_neg = neg
            else:
                neg = ctrl.add_child(name=name)
                neck_groups.append((ctrl.sdk_node, neg))
            neg.set_attr('useOutlinerColor', True)
            neg.set_attr('outlinerColor', (0.0, .55, .95))

        name = NodeName(head_ctrl, ext='transSplit')
        trans_split = Node.create('multiplyDivide', name=name)
        name = name.replace_ext('transNeg')
        trans_neg = Node.create('multiplyDivide', name=name)
        name = name.replace_ext('rotMult')
        rot_mult = Node.create('multiplyDivide', name=name)

        neck_ctrl_len = float(len(neck_groups))
        unit_split = 1.0 / neck_ctrl_len
        average_split = 1.0 / (neck_ctrl_len + 1.0)

        # translate
        for ch in 'XYZ':
            t = 'translate' + ch
            head_ctrl.attr(t) >> trans_split.attr('input1' + ch)
            trans_split.attr('input2' + ch).value = average_split
            for neck_sdk, neck_neg in neck_groups:
                trans_split.attr('output' + ch) >> neck_sdk.attr(t)

            trans_split.attr('output' + ch) >> trans_neg.attr('input1' + ch)
            trans_neg.attr('input2' + ch).value = -neck_ctrl_len
            trans_neg.attr('output' + ch) >> head_neg.attr(t)

        # rotation
        num_sections = len(neck_groups)
        if num_sections <= 1:
            self.warn('Skipped creating rotate effects: only 1 joint section')
        else:
            for func in ('twist', 'lateral', 'forward'):
                channel, default_mult = channel_dict[func]
                axis = channel[-1].upper()
                limb_mult_attr = self.add_limb_attr(
                    'float', name=func + 'Mult', keyable=True,
                    minValue=0, maxValue=1, defaultValue=default_mult)

                head_ctrl.attr(channel) >> rot_mult.attr('input1' + axis)
                limb_mult_attr >> rot_mult.attr('input2' + axis)

                if func == 'twist':
                    for neck_sdk, neck_neg in neck_groups:
                        split = 0.5 / float(num_sections - 1)
                        if (neck_sdk, neck_neg) == neck_groups[-1]:
                            split = unit_split * 1.5

                        name = NodeName(neck_sdk, ext='twistSplit')
                        split_div = Node.create('multDoubleLinear', name=name)
                        rot_mult.attr('output' + axis) >> split_div.input1
                        split_div.input2.value = split
                        split_div.output >> neck_sdk.attr(channel)

                        name = name.replace_ext('twistNegMult')
                        twist_neg_mult = Node.create(
                            'multDoubleLinear', name=name)
                        neck_sdk.attr(channel) >> twist_neg_mult.input1
                        twist_neg_mult.input2.value = -1.0
                        twist_neg_mult.output >> neck_neg.attr(channel)

                elif func == 'lateral':
                    name = NodeName(head_ctrl, ext='lateralNegMult')
                    neg_mult = Node.create('multDoubleLinear', name=name)
                    rot_mult.attr('output' + axis) >> neg_mult.input1
                    neg_mult.input2.value = -1.0
                    neg_mult.output >> head_neg.attr(channel)

                    for neck_sdk, neck_neg in neck_groups:
                        split = 0.5 / float(num_sections - 1)
                        if (neck_sdk, neck_neg) == neck_groups[-1]:
                            split = unit_split * 1.5

                        name = NodeName(neck_neg, ext='lateralSplit')
                        split_div = Node.create('multDoubleLinear', name=name)
                        rot_mult.attr('output' + axis) >> split_div.input1
                        split_div.input2.value = split
                        split_div.output >> neck_sdk.attr(channel)

                elif func == 'forward':
                    name = NodeName(head_ctrl, ext='forwardNegMult')
                    neg_mult = Node.create('multDoubleLinear', name=name)
                    rot_mult.attr('output' + axis) >> neg_mult.input1
                    neg_mult.input2 = -1.0
                    neg_mult.output >> head_neg.attr(channel)

                    for neck_sdk, neck_neg in neck_groups:
                        split = 0.5 / float(num_sections - 1)
                        if (neck_sdk, neck_neg) == neck_groups[-1]:
                            split = unit_split * 1.5

                        name = NodeName(neck_neg, ext='forwardSplit')
                        split_div = Node.create('multDoubleLinear', name=name)
                        rot_mult.attr('output' + axis) >> split_div.input1
                        split_div.input2 = split
                        split_div.output >> neck_sdk.attr(channel)
        self.add_constraint('point', end_jnt, cns_loc, maintainOffset=True)
        self.add_constraint('orient', head_ctrl, cns_loc, maintainOffset=True)
        # add FK ctrls vis attr
        attr = self.add_limb_attr(
            'bool', name='showFKCtrls', keyable=True, defaultValue=False)
        for ctrl in neck_ctrls:
            attr >> ctrl.shape.v

        neck_ctrls[0].create_scale_space_switch(mode='rot')
        head_ctrl.create_scale_space_switch(mode='rot')
