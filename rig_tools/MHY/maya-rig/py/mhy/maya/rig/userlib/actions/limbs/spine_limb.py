from typing_extensions import runtime
import maya.cmds as cmds

import mhy.protostar.core.parameter as pa

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.utils as utils
import mhy.maya.rig.constants as const


class BaseSpine(bl.BaseLimb):
    """
    Base spine class containing shared parameters
    and marker implementation.

    :limb type: spine
    """

    _LIMB_TYPE = 'spine'
    _UI_ICON = 'spine'

    # --- input parameters

    @pa.int_param(default=6, min_value=3)
    def num_joints(self):
        """The number of spine joints."""

    @pa.enum_param(items=const.ROT_ORDERS, default='xyz')
    def rotate_order(self):
        """The joint rotation order."""

    # -- end of parameter definition

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        data = {
            'aim_axis': 'x',
            'up_axis': 'z',
            'up_ctrl_position': (0, 93.4, 8),
            'markers': []}

        count = self.num_joints.value
        for i in range(count):
            name = NodeName(part=part, side=side, num=i, ext=const.EXT_MARKER)
            cns = None if i == count - 1 else 'aim'
            data['markers'].append({
                'name': name,
                'position': (0, 93.4 + 8 * i, 0),
                'rotation': cns,
                'up_type': 'ctrl',
            })

        return data


class IKFKSpine(BaseSpine):
    """
    Spline spine system which has IK and FK works in the same time.
    Ik_root should be parentConstrainted to upper body ctrl.
    """

    def connect_parent(self, parent_limb):
        """Re-implemented to make a custom connection to hip limb."""
        if parent_limb.limb_type == 'hip':
            ctrls = parent_limb.get_ctrls()
            self.add_constraint(
                'parent', ctrls[-1], self.ik_bottom_plug, maintainOffset=True)
            self.add_constraint(
                'parent', ctrls[0], self.limb_root.value, maintainOffset=True)
        else:
            super(IKFKSpine, self).connect_parent(parent_limb)
        

    def run(self):
        """Builds the limb ctrl rig."""
        start_joint = self.rig_skeleton[0][0]
        end_joint = self.rig_skeleton[0][-1]
        limb_root = self.limb_root.value
        ws_root = self.ws_root

        # get joint chain
        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)
        self.debug('Joint Chain Length: {}'.format(joint_chain.chain_length))

        # create spline ik joint chain ik_joints
        name = NodeName(start_joint, ext='GRP')
        root = Node.create('transform', name=name)
        root.set_parent(ws_root)
        self.add_constraint('parent', limb_root, root, maintainOffset=False)
        ik_joints = []
        for joint in joint_chain.joints:
            name = NodeName(joint, ext='IKJNT')
            ik_jnt = joint.duplicate(name=name, parentOnly=True)[0]
            parent = ik_joints[-1] if ik_joints else root
            ik_jnt.set_parent(parent)
            self.add_constraint('parent', ik_jnt, joint, maintainOffset=True)
            ik_joints.append(ik_jnt)
        num_span = len(ik_joints)

        # check orientation
        long_axis = joint_chain.long_axis
        if long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(long_axis))
        else:
            self.warn('Not all joint has the same orientation.')

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set spine joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # Create Spline Curve ik_curve
        name = NodeName(start_joint, ext='SPLINEHANDLE')
        result = cmds.ikHandle(
            solver='ikSplineSolver',
            parentCurve=False,
            startJoint=ik_joints[0],
            endEffector=ik_joints[-1],  
            numSpans=3,         
            name=name)
        ik_handle, ik_effector, ik_curve = [Node(n) for n in result]
        cmds.delete(ik_handle)
        ik_curve.name = name.replace_ext('CURVE')
        # get the aim axis and upvec axis
        aim = (1.0,0,0)
        up = (0,1.0,0)
        if long_axis == 'Y':
            aim = (0,1.0,0)
            up = (0,0,1.0)           
        elif long_axis == 'Z':
            aim = (0,0,1.0)
            up = (1.0,0,0)
        ik_ctrl_jnt_list=[]
        for index in range(0,3):
            name = NodeName(start_joint, desc='IKLayer2', num=index, ext='IKHLPJNT')
            ik_ctrl_jnt = start_joint.duplicate(name=name,parentOnly=True)[0]
            if index in [1,2]: 
                temp_loc = Node.create('transform',name='tempLoc')
                temp_ribbon = Node(cmds.extrude(ik_curve, extrudeType=0, length=1, direction=(0,0,1))[0])
                temp_ribbon_shape = temp_ribbon.get_shapes()[0]
                temp_cns = Node.create('mhyGeometryInfo')
                temp_ribbon_shape.worldSpace[0] >> temp_cns.targetGeometry
                temp_ribbon_shape.worldMatrix[0] >> temp_cns.targetMatrix
                cmds.setAttr(temp_cns.name+'.coord[0].v', 0)
                cmds.setAttr(temp_cns.name+'.coord[0].u', float(index)/3.0)
                temp_cns.rotate[0] >> temp_loc.rotate
                temp_cns.translate[0] >> temp_loc.translate
                temp_target = temp_loc.duplicate()[0]
                temp_target.align(temp_loc)
                temp_target.set_parent(temp_loc)
                temp_target.set_attr('translate'+long_axis, 1)
                ik_ctrl_jnt.align(temp_loc, skipRotate=True)
                self.add_constraint('aim', temp_target, ik_ctrl_jnt, 
                    aimVector=aim, upVector=up, worldUpObject=start_joint,
                    worldUpType='objectrotation', maintainOffset=False)
                cmds.delete(temp_loc,temp_ribbon,temp_cns)
            elif index == 3:
                ik_ctrl_jnt.align(end_joint)
            if index == 0:
                ik_ctrl_jnt.set_parent(ws_root)
            else:
                ik_ctrl_jnt.set_parent(ik_ctrl_jnt_list[-1])
            ik_ctrl_jnt_list.append(ik_ctrl_jnt)
        name = name.replace_num(3)
        ik_ctrl_jnt = end_joint.duplicate(name=name,parentOnly=True)[0]
        ik_ctrl_jnt.set_parent(ik_ctrl_jnt_list[-1])
        ik_ctrl_jnt_list.append(ik_ctrl_jnt)
        name = NodeName(start_joint,desc='ikCtrl', ext='SPLINEHANDLE')
        result = cmds.ikHandle(
            solver='ikSplineSolver',
            curve=ik_curve,
            createCurve=False,
            startJoint=ik_ctrl_jnt_list[0],
            endEffector=ik_ctrl_jnt_list[-1],           
            name=name)
        
        ik_handle, ik_effector = [Node(n) for n in result]
        ik_handle.set_parent(ws_root)
        # Create IK Ctrls
        name = NodeName(start_joint, desc='ikRoot', ext='GRP')
        ik_root = Node.create('transform',name=name)
        ik_root.set_parent(limb_root)
        name = name.replace_desc('ikBottom')
        ik_bottom_grp = Node.create('transform',name=name)
        ik_bottom_grp.align(start_joint)
        ik_bottom_grp.set_parent(ik_root)
        name = NodeName(start_joint, desc='ikMidHelp', ext='LOC')
        ik_mid_loc = Node.create('transform',name=name)
        ik_mid_grp = Node.create('transform',name=name.replace_ext('GRP'))
        ik_mid_grp.align(ik_bottom_grp)
        ik_mid_grp.set_parent(ik_root)
        ik_mid_loc.set_parent(ik_mid_grp)
        self.add_constraint(
            'parent',
            ik_ctrl_jnt_list[1],
            ik_mid_loc,
            maintainOffset=False)

        # Setup first layer of ik ctrl, ik_bottom_grp is the hip leaf to connect to the hip ctrl
        name = NodeName(ik_joints[0], desc='IKLayer1', num=0, ext='IKHLPJNT')
        ik_start_jnt = ik_joints[0].duplicate(name=name, parentOnly=True)[0]
        ik_start_jnt.v.value=False
        name = name.replace_num(1)
        ik_end_jnt = ik_joints[-1].duplicate(name=name, parentOnly=True)[0]
        ik_start_jnt.set_parent(ik_root)
        ik_end_jnt.set_parent(ik_start_jnt)
        name = NodeName(ik_curve,ext='SKINCLUSTER')
        curve_skin = cmds.skinCluster(
            ik_curve,
            ik_start_jnt,
            toSelectedBones=False,
            name=name)[0]
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[1]',
            transformValue=[(ik_start_jnt,1), (ik_end_jnt,0)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[2]',
            transformValue=[(ik_start_jnt,0.95), (ik_end_jnt,0.05)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[3]',
            transformValue=[(ik_start_jnt,0.75), (ik_end_jnt,0.25)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[4]',
            transformValue=[(ik_start_jnt,0.3), (ik_end_jnt,0.7)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[5]',
            transformValue=[(ik_start_jnt,0), (ik_end_jnt,1)])
        
        name = NodeName(start_joint, desc='bottom',ext = 'LOC')
        bottom_ik_loc = Node.create('transform',name=name)
        bottom_ik_loc.align(ik_ctrl_jnt_list[0])
        bottom_ik_loc.set_parent(ik_bottom_grp)
        name = name.replace_desc('end')
        name = name.replace_ext('IKCTRL')
        end_ikctrl = self.add_ctrl(xform=ik_ctrl_jnt_list[3],
            name=name,
            ext='IKCTRL',
            parent=ik_root,
            shape='cube')
        self.add_constraint('parent',end_ikctrl,ik_end_jnt,maintainOffset=True)
        name = name.replace_desc('mid')
        mid_00_ikctrl = self.add_ctrl(xform=ik_ctrl_jnt_list[1],
            name=name,
            ext='IKCTRL',
            parent=ik_bottom_grp,
            shape='sphereCurve')
        ik_mid_loc.translate >> mid_00_ikctrl.plc_node.translate
        ik_mid_loc.rotate >> mid_00_ikctrl.plc_node.rotate
        name = name.replace_num(1)
        mid_01_ikctrl = self.add_ctrl(xform=ik_ctrl_jnt_list[2],
            name=name,
            ext='IKCTRL',
            parent=ik_root,
            shape='sphereCurve')
        self.add_constraint(
            'parent',
            ik_ctrl_jnt_list[2],
            mid_01_ikctrl.plc_node,
            maintainOffset=False)

        # Create FK help joints
        fkctrl_jnt_list=[]
        for index in range(0,3):
            name = NodeName(start_joint, desc='FK', num=index, ext='FKHLPJNT')
            fkCtrl_jnt = ik_ctrl_jnt_list[index].duplicate(name=name,parentOnly=True)[0]
            if index == 0:
                fkCtrl_jnt.set_parent(ws_root)
            else:
                fkCtrl_jnt.set_parent(fkctrl_jnt_list[-1])
            fkctrl_jnt_list.append(fkCtrl_jnt)
        fkctrl_jnt_list.append(ik_ctrl_jnt_list[-1])
        self.add_constraint('parent',bottom_ik_loc,fkctrl_jnt_list[0],maintainOffset=False)
        self.add_constraint('parent',mid_00_ikctrl,fkctrl_jnt_list[1],maintainOffset=False)
        self.add_constraint('parent',mid_01_ikctrl,fkctrl_jnt_list[2],maintainOffset=False)
        ik_handle.dTwistControlEnable.value=True
        ik_handle.dWorldUpType.value = 4
        ik_handle.dWorldUpAxis.value = 0
        bottom_ik_loc.worldMatrix[0] >> ik_handle.dWorldUpMatrix
        end_ikctrl.worldMatrix[0] >> ik_handle.dWorldUpMatrixEnd

        # Create FK ribbon and binding it to ik help joints
        name=NodeName(start_joint,desc='fkRibbon',ext='RIBBON')
        fk_ribbon,extrudeNode = cmds.extrude(
            ik_curve,
            extrudeType=0,
            direction=[1,0,0],
            length=1,
            degreeAlongLength=3,
            name=name,
            polygon=0)
        fk_ribbon = Node(fk_ribbon)
        cmds.delete(extrudeNode)
        cmds.rebuildSurface(fk_ribbon, spansU=3,spansV=1,degreeU=3,degreeV=1,keepRange=0)
        name = NodeName(start_joint,desc='spineRibbon',ext='RIBBON')
        fk_ribbon_shape = fk_ribbon.get_shapes()[0]
        cmds.move(
            -0.5,
            fk_ribbon_shape.name+'.cv[0:5][0:1]',
            worldSpace=True,
            moveX=True,
            relative=True)
        spine_ribbon = fk_ribbon.duplicate(name=name,parentOnly=False)[0]
        spine_ribbon_shape = spine_ribbon.get_shapes()[0]
        spine_ribbon.set_parent(ws_root)
        fk_ribbon.set_parent(ws_root)
        name=NodeName(start_joint,desc='fkRibbon',ext='SKINCLUSTER')
        fk_skin=cmds.skinCluster(
            fk_ribbon,
            fkctrl_jnt_list,
            name=name,
            toSelectedBones=True)[0]
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[0][0:1]',
            transformValue=[(fkctrl_jnt_list[0],1)])
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[1][0:1]',
            transformValue=[(fkctrl_jnt_list[0],0.8), (fkctrl_jnt_list[1],0.2)])
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[2][0:1]',
            transformValue=[(fkctrl_jnt_list[1],0.8), (fkctrl_jnt_list[2],0.2)])
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[3][0:1]',
            transformValue=[(fkctrl_jnt_list[1],0.2),(fkctrl_jnt_list[2],0.8)])
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[4][0:1]',
            transformValue=[(fkctrl_jnt_list[3],1)])
        cmds.skinPercent(
            fk_skin,
            fk_ribbon_shape.name+'.cv[5][0:1]',
            transformValue=[(fkctrl_jnt_list[3],1)])

        # Create FK ribbon locators        
        name = NodeName(start_joint, desc='fkCtrl', ext='MATRIXCONSTRAINT')
        fk_matrix_cns = Node.create('mhyGeometryInfo',name=name)
        fk_ribbon_shape.worldSpace[0] >> fk_matrix_cns.targetGeometry
        fk_ribbon.worldMatrix[0] >> fk_matrix_cns.targetMatrix
        fkCtrl_list = []
        fkJoint_list = []
        for index in range(0,4):
            name = NodeName(start_joint,desc='fkCtrl',num=index,ext='LOC')
            loc = Node.create('transform',name=name)
            loc.set_parent(ws_root)
            cmds.setAttr(fk_matrix_cns.name+'.coord[%d].v'%index, 0.5)
            cmds.setAttr(fk_matrix_cns.name+'.coord[%d].u'%index, float(index)/3.0)
            fk_matrix_cns.rotate[index] >> loc.rotate
            fk_matrix_cns.translate[index] >> loc.translate
            name = NodeName(start_joint,num=index,ext='FKCTRL')
            if index==0:
                parent=ik_root
            else:
                parent=fkCtrl_list[-1]
            temp_target = loc.duplicate()[0]
            temp_target.align(loc)
            temp_target.set_parent(loc)
            temp_target.set_attr('translate'+long_axis, 1)
            fkCtrl = self.add_ctrl(xform=loc,
                name=name,
                shape='square',
                parent=parent)
            fkCtrl.plc_node.align(loc, skipRotate=True)
            self.add_constraint('aim', temp_target, fkCtrl.plc_node, 
                aimVector=aim, upVector=up, worldUpObject=start_joint, worldUpVector=up,
                worldUpType='objectrotation', maintainOffset=False)
            cmds.delete(temp_target)
            loc.inheritsTransform.value = False
            fkCtrl.lock(attrs='s')
            name = NodeName(start_joint,desc='fkJoint',num=index,ext='FKJNT')
            fk_ribbon_joint=Node.create('joint',name=name)
            fk_ribbon_joint.set_parent(ws_root)
            fk_ribbon_joint.v.value=False
            fkJoint_list.append(fk_ribbon_joint)
            self.add_constraint('parent',fkCtrl,fk_ribbon_joint,maintainOffset=False)
            if index > 0:
                if index == 1:
                    transParent = parent.offset_node
                else:
                    transParent = trans_loc
                name = NodeName(start_joint,desc='fkTrans',num=index,ext='LOC')
                trans_loc = Node.create('transform',name=name)
                trans_loc.align(fkCtrl)
                trans_loc.set_parent(transParent)
                self.add_constraint('parent',loc,trans_loc,maintainOffset=True)
                trans_loc.translate >> fkCtrl.plc_node.translate
                trans_loc.rotate >> fkCtrl.plc_node.rotate
            else:
                self.add_constraint('parent',loc,fkCtrl.plc_node,maintainOffset=True)
            fkCtrl_list.append(fkCtrl)
        cmds.skinCluster(spine_ribbon,fkJoint_list)
        name = NodeName(start_joint, desc='spine', ext='MATRIXCONSTRAINT')
        spine_matrix_cns = Node.create('mhyGeometryInfo',name=name)
        spine_ribbon_shape.worldSpace[0] >> spine_matrix_cns.targetGeometry
        spine_ribbon.worldMatrix[0] >> spine_matrix_cns.targetMatrix
        closest_node = Node.create('closestPointOnSurface')
        spine_ribbon_shape.worldSpace[0] >> closest_node.inputSurface
        for index in range(0,num_span-1):
            name = NodeName(start_joint,desc='spine',num=index,ext='LOC')
            loc = Node.create('transform',name=name)
            loc.set_parent(ws_root)
            loc.inheritsTransform=False
            joint = ik_joints[index]
            position = joint.get_translation(space='world')
            closest_node.inPosition.value=position
            u = closest_node.parameterU.value
            v = closest_node.parameterV.value
            cmds.setAttr(spine_matrix_cns.name+'.coord[%d].v'%index,v)
            cmds.setAttr(spine_matrix_cns.name+'.coord[%d].u'%index,u)
            spine_matrix_cns.rotate[index] >> loc.rotate
            spine_matrix_cns.translate[index] >> loc.translate
            self.add_constraint('parent',loc,joint,maintainOffset=True)
        self.add_constraint('parent',fkCtrl_list[-1],ik_joints[-1],maintainOffset=True)
        cmds.delete(closest_node)
        # Setup spine strech
        limb_stretch = self.add_limb_attr('bool', name='stretch',
            keyable=True, defaultValue=False)
        
        ratio_attr = utils.create_curve_stretch_output(ik_curve)
        for jnt in ik_ctrl_jnt_list:
            cond = utils.create_condition(limb_stretch, True, ratio_attr, 1, 0)
            mult = Node.create(
                'multiplyDivide', name=NodeName(jnt, ext='MDNODE'))
            length = jnt.attr('translate' + long_axis[-1]).value
            mult.operation.value = 1
            mult.input1X.value = length
            cond >> mult.input2X
            mult.outputX >> jnt.attr('translate' + long_axis[-1])

        # setup leaf parent and hip connection
        name = NodeName(start_joint, desc='leafParent',ext='GRP')
        leafParent = Node.create('transform',name=name)
        leafParent.set_parent(ik_root)
        self.add_constraint('parent',ik_joints[-1],leafParent,maintainOffset=False)
        self.ctrl_leaf_parent=leafParent

        self.ik_bottom_plug = ik_bottom_grp


class SingleFKIKSpine(BaseSpine):
    """Spline spine system which has IK and FK works in the same time.
        Ik_root should be parentConstrainted to upper body ctrl

    """
    def connect_parent(self, parent_limb):
        """Re-implemented to make a custom connection to hip limb."""
        if parent_limb.limb_type == 'hip':
            ctrls = parent_limb.get_ctrls()
            self.add_constraint(
                'parent', ctrls[-1], self.ik_bottom_plug, maintainOffset=True)
            self.add_constraint(
                'parent', ctrls[0], self.limb_root.value, maintainOffset=True)
        else:
            super(SingleFKIKSpine, self).connect_parent(parent_limb)

    def run(self):
        """Builds the limb ctrl rig."""
        start_joint = self.rig_skeleton[0][0]
        end_joint = self.rig_skeleton[0][-1]
        limb_root = self.limb_root.value
        ws_root = self.ws_root

        # get joint chain
        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)
        self.debug('Joint Chain Length: {}'.format(joint_chain.chain_length))
        # check orientation
        long_axis = joint_chain.long_axis
        if long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(long_axis))
        else:
            self.warn('Not all joint has the same orientation.')

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set spine joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # create spline ik joint chain ik_joints
        name = NodeName(start_joint, ext='GRP')
        root = Node.create('transform', name=name)
        root.set_parent(ws_root)
        self.add_constraint('parent', limb_root, root, maintainOffset=False)
        # create fk root
        name = NodeName(start_joint, desc='fkRoot', ext='GRP')
        fk_root = Node.create('transform',name=name)
        fk_root.set_parent(limb_root)

        fk_joints = []
        fk_child_joints = []
        ik_joints = []
        ik_child_joints = []
        joint_position_list = []
        for joint in joint_chain.joints:
            name = NodeName(joint, ext='FKJNT')
            fk_jnt = joint.duplicate(name=name, parentOnly=True)[0]
            name = NodeName(joint, ext='CHJNT')
            fk_child_jnt = joint.duplicate(name=name, parentOnly=True)[0]
            fk_child_jnt.set_parent(fk_jnt)
            self.add_constraint('parent',fk_child_jnt,joint,maintainOffset=True)
            parent = fk_joints[-1] if fk_joints else root
            fk_jnt.set_parent(parent)
            fk_joints.append(fk_jnt)
            fk_child_joints.append(fk_child_jnt)
        
            name = NodeName(joint, ext='IKJNT')
            ik_jnt = joint.duplicate(name=name, parentOnly=True)[0]
            name = NodeName(joint, ext='IKCHJNT')
            ik_child_jnt = ik_jnt.duplicate(name=name, parentOnly=True)[0]
            ik_child_jnt.set_parent(ik_jnt)
            parent = ik_joints[-1] if ik_joints else root
            ik_jnt.set_parent(parent)
            ik_joints.append(ik_jnt)
            ik_child_joints.append(ik_child_jnt)

            joint_position_list.append(joint.get_translation(space='world'))
        num_span = len(ik_joints)
        # Set up fk chain
        # Create main ctrl
        name = NodeName(part=self.part, desc='main', ext='FKCTRL')
        main_ctrl = self.add_ctrl(xform=fk_joints[0],
            name=name,
            shape='sphereCurve',
            parent=fk_root)
        bending_weight = self.add_limb_attr('float', 
            name='bendingWeight', keyable=True,
            defaultValue=0.5, minValue=0, maxValue=1)
    
        # Create fk ctrl chain
        bend_scale = self.add_limb_attr('float', 
            name='bendScale', 
            keyable=True, 
            defaultValue=2.0, 
            min=0.5, 
            max=4)
        fk_ctrls = []
        for index, joint in enumerate(fk_joints):
            if index == 0:
                parent = fk_root
            else:
                parent = fk_ctrls[-1]
            name = NodeName(joint, ext='FKCTRL')
            fk_ctrl = self.add_ctrl(xform=joint,
                name=name,
                parent=parent,
                shape='circle')
            fk_ctrls.append(fk_ctrl)
            name = NodeName(joint, desc='bending', ext='MDNODE')
            md_node = Node.create('multiplyDivide', name=name)
            name = NodeName(joint, desc='bending', ext='PMANODE')
            pma_node = Node.create('plusMinusAverage', name=name)
            name = NodeName(joint, desc='bending', ext='RBFNODE')
            rbf_node = Node.create('rbfSolver', name=name)
            md_node.operation = 1
            md_node.input1X.value = float(index)/(num_span - 1)
            bend_scale >> md_node.input2X
            pma_node.operation.value = 2
            bend_scale >> pma_node.input1D[0]
            md_node.outputX >> pma_node.input1D[1]
            bending_weight >> rbf_node.nInput[0]
            rbf_node.poses[0].nKey[0].value = 0
            rbf_node.poses[1].nKey[0].value = 0.5
            rbf_node.poses[2].nKey[0].value = 1
            rbf_node.poses[1].mValue[0].value = 1
            pma_node.output1D >> rbf_node.poses[0].mValue[0]
            md_node.outputX >> rbf_node.poses[2].mValue[0]
            name = NodeName(fk_ctrl, desc='fkCtrl', ext='MDN')
            multiply_node = Node.create('multiplyDivide', name=name)
            multiply_node.operation.value = 1
            rbf_node.mOutput[0] >> multiply_node.input1X
            multiply_node.input1X >> multiply_node.input1Y
            multiply_node.input1X >> multiply_node.input1Z
            main_ctrl.rx >> multiply_node.input2X
            main_ctrl.ry >> multiply_node.input2Y
            main_ctrl.rz >> multiply_node.input2Z
            multiply_node.outputX >> fk_ctrl.sdk_node.rx
            multiply_node.outputY >> fk_ctrl.sdk_node.ry
            multiply_node.outputZ >> fk_ctrl.sdk_node.rz

            self.add_constraint(
                'parent', 
                fk_ctrl, 
                fk_joints[index], 
                maintainOffset=True)
        # Create Spline Curve ik_curve
        name = NodeName(start_joint, desc='base', ext='CURVE')
        base_curve = Node.create('nurbsCurve', joint_position_list, degree=1, name=name)
        cmds.parent(base_curve,ws_root)
        #base_curve.set_parent(ws_root)
        name = name.replace_ext('SKINCLUSTER')
        Node.create('skinCluster', base_curve,fk_joints,toSelectedBones=True,name=name)
        
        # build double ik setup
        name = NodeName(start_joint, desc='ikBase', ext='CURVE')
        ik_base_curve = cmds.rebuildCurve( base_curve,constructionHistory=True,
            replaceOriginal=False, rebuildType=0, endKnots=1, keepRange=0, 
            keepControlPoints=False, keepEndPoints=True, keepTangents=False,
            spans=3, degree=3, tolerance=0.01, name=name)[0]
        ik_base_curve = Node(ik_base_curve)
        name = name.replace_desc('ik')
        ik_curve = ik_base_curve.duplicate(name=name)[0]
        name = NodeName(ik_curve, ext='BLANDSHAPE')
        Node.create('blendShape', ik_base_curve, ik_curve, weight=[(0,1)])
        ik_ctrl_jnt_list = []
        ik_base_jnt_list = []
        name = NodeName(start_joint, desc='ikRoot', ext='GRP')
        ik_root = Node.create('transform',name=name)
        ik_root.set_parent(limb_root)
        for index in range(0,4):
            name = NodeName(start_joint, desc='IKLayer2', num=index, ext='IKHLPJNT')
            ik_ctrl_jnt = start_joint.duplicate(name=name,parentOnly=True)[0]
            if index in [1,2]:
                temp_loc = Node.create('transform',name='tempLoc')
                temp_loc.inheritsTransform.value = False
                temp_ribbon = Node(cmds.extrude(ik_curve, extrudeType=0, length=1, direction=(0,0,1))[0])
                temp_ribbon_shape = temp_ribbon.get_shapes()[0]
                temp_cns = Node.create('mhyGeometryInfo')
                temp_ribbon_shape.worldSpace[0] >> temp_cns.targetGeometry
                temp_ribbon_shape.worldMatrix[0] >> temp_cns.targetMatrix
                cmds.setAttr(temp_cns.name+'.coord[0].v', 0)
                cmds.setAttr(temp_cns.name+'.coord[0].u', float(index)/3.0)
                temp_cns.rotate[0] >> temp_loc.rotate
                temp_cns.translate[0] >> temp_loc.translate
                ik_ctrl_jnt.align(temp_loc)
                cmds.delete(temp_loc,temp_ribbon,temp_cns)
            elif index == 3:
                ik_ctrl_jnt.align(end_joint)
            name = name.replace_ext('IKBASEJNT')
            ik_base_jnt = ik_ctrl_jnt.duplicate(name=name,parentOnly=True)[0]           
            if index == 0:
                ik_ctrl_jnt.set_parent(ik_root)
                ik_base_jnt.set_parent(ik_root)
                ik_ctrl_jnt.v.value = False
                ik_base_jnt.v.value = False
            else:
                ik_ctrl_jnt.set_parent(ik_ctrl_jnt_list[-1])
                ik_base_jnt.set_parent(ik_base_jnt_list[-1])  
            ik_ctrl_jnt_list.append(ik_ctrl_jnt)
            ik_base_jnt_list.append(ik_base_jnt)   
        name = NodeName(start_joint,desc='ikCtrl', ext='SPLINEHANDLE')
        ik_handle, ik_effector = Node.create('ikHandle',
            solver='ikSplineSolver',
            curve=ik_curve,
            createCurve=False,
            startJoint=ik_ctrl_jnt_list[0],
            endEffector=ik_ctrl_jnt_list[-1],           
            name=name)
        ik_handle = Node(ik_handle)
        ik_handle.set_parent(ws_root)

        name = NodeName(start_joint,desc='ikBase', ext='SPLINEHANDLE')
        ik_base_handle, ikBase_effector = Node.create('ikHandle',
            solver='ikSplineSolver',
            curve=ik_base_curve,
            createCurve=False,
            startJoint=ik_base_jnt_list[0],
            endEffector=ik_base_jnt_list[-1],           
            name=name)
        ik_base_handle = Node(ik_base_handle)
        ik_base_handle.set_parent(ws_root)
        ik_base_curve.set_parent(ws_root)
        ik_curve.set_parent(ws_root)
        # Create IK Ctrls     
        name = name.replace_desc('ikBottom')
        name = name.replace_ext('GRP')
        ik_bottom_grp = Node.create('transform',name=name)
        ik_bottom_grp.align(start_joint)
        ik_bottom_grp.set_parent(ik_root)
        name = name.replace_desc('ikTop')
        ik_top_grp = Node.create('transform',name=name)
        ik_top_grp.align(end_joint)
        ik_top_grp.set_parent(ik_root)

        name = NodeName(start_joint, desc='ikMidHelp', ext='LOC')
        ik_mid_loc = Node.create('transform',name=name)
        ik_mid_grp = Node.create('transform',name=name.replace_ext('GRP'))
        ik_mid_grp.align(ik_bottom_grp)
        ik_mid_grp.set_parent(ik_root)
        ik_mid_loc.set_parent(ik_mid_grp)
        self.add_constraint('parent',ik_ctrl_jnt_list[1],ik_mid_loc,maintainOffset=False)

        name = NodeName(start_joint, desc='ikUpHelp', ext='LOC')
        ik_up_loc = Node.create('transform',name=name)
        ikUp_grp = Node.create('transform',name=name.replace_ext('GRP'))
        ikUp_grp.align(ik_top_grp)
        ikUp_grp.set_parent(ik_top_grp)
        ik_up_loc.set_parent(ikUp_grp)
        self.add_constraint('parent',ik_ctrl_jnt_list[-2],ik_up_loc,maintainOffset=False)

        # Setup first layer of ik ctrl, ik_bottom_grp is the hip leaf to connect to the hip ctrl
        name = NodeName(ik_joints[0], desc='IKLayer1', num=0, ext='IKHLPJNT')
        ik_start_jnt = ik_joints[0].duplicate(name=name, parentOnly=True)[0]
        ik_start_jnt.v.value=False
        name = name.replace_ext('IKHLPJNTGRP')
        ik_start_jnt_grp = Node.create('transform',name=name)
        ik_start_jnt_grp.align(ik_start_jnt)
        ik_start_jnt_grp.set_parent(ik_root)
        ik_start_jnt.set_parent(ik_start_jnt_grp)
        name = NodeName(ik_joints[0], desc='IKLayer1', num=1, ext='IKHLPJNT')
        ik_end_jnt = ik_joints[-1].duplicate(name=name, parentOnly=True)[0]
        name = name.replace_ext('IKHLPJNTGRP')
        ik_end_jnt_grp = Node.create('transform',name=name)
        ik_end_jnt_grp.align(ik_end_jnt)   
        ik_end_jnt_grp.set_parent(ik_root)
        ik_end_jnt_grp.v.value = False
        ik_end_jnt.set_parent(ik_end_jnt_grp)
        self.add_constraint('parent', fk_ctrls[-1], ik_end_jnt_grp, maintainOffset=True)

        # setup skin cluster of ik_curve
        name = NodeName(ik_curve,ext='SKINCLUSTER')
        curve_skin = Node.create(
            'skinCluster', 
            ik_curve,ik_start_jnt, 
            ik_end_jnt,
            toSelectedBones=True,
            name=name)
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[1]',
            transformValue=[(ik_start_jnt,1),(ik_end_jnt,0)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[2]',
            transformValue=[(ik_start_jnt,0.95),(ik_end_jnt,0.05)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[3]',
            transformValue=[(ik_start_jnt,0.75),(ik_end_jnt,0.25)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[4]',
            transformValue=[(ik_start_jnt,0.3),(ik_end_jnt,0.7)])
        cmds.skinPercent(
            curve_skin, 
            ik_curve.name+'.cv[5]',
            transformValue=[(ik_start_jnt,0),(ik_end_jnt,1)])
        curve_skin = Node(curve_skin)
        ik_start_jnt_grp.worldInverseMatrix[0] >> curve_skin.bindPreMatrix[0]
        ik_end_jnt_grp.worldInverseMatrix[0] >> curve_skin.bindPreMatrix[1]     

        # setup hip loc  
        name = NodeName(start_joint, desc='bottom',ext = 'LOC')
        bottom_ik_loc = Node.create('transform',name=name)
        bottom_ik_loc.align(ik_ctrl_jnt_list[0])
        bottom_ik_loc.set_parent(ik_bottom_grp)
        name = name.replace_desc('bottomMidBase')
        bottom_mid_base_loc = bottom_ik_loc.duplicate(name=name)[0]
        bottom_mid_base_loc.set_parent(ik_root)
        name = NodeName(bottom_ik_loc,desc='end',ext='IKCTRL')
        end_ikctrl = self.add_ctrl(xform=ik_ctrl_jnt_list[3],
            name=name,
            ext='IKCTRL',
            parent=ik_root,
            shape='cube')
        self.add_constraint(
            'parent', 
            end_ikctrl,
            ik_end_jnt, 
            maintainOffset=True)
        self.add_constraint(
            'parent', 
            fk_ctrls[-1], 
            end_ikctrl.plc_node, 
            maintainOffset=True)
        name = name.replace_desc('mid')
        mid_00_ikctrl = self.add_ctrl(
            xform=ik_ctrl_jnt_list[1],
            name=name,
            ext='IKCTRL',
            parent=bottom_mid_base_loc,
            shape='sphereCurve')
        self.add_constraint(
            'orient',
            ik_mid_grp,
            ik_bottom_grp,
            bottom_mid_base_loc,
            maintainOffset=True)
        self.add_constraint(
            'point',
            ik_bottom_grp,
            bottom_mid_base_loc,
            maintainOffset=True)
        ik_mid_loc.translate >> mid_00_ikctrl.plc_node.translate
        ik_mid_loc.rotate >> mid_00_ikctrl.plc_node.rotate

        # setup top loc, mid_01_ctrl will follow half of end_fkctrl movement
        name = NodeName(end_joint, desc='topMid',ext = 'GRP')
        top_mid_grp = Node.create('transform',name=name)
        top_mid_grp.align(ik_ctrl_jnt_list[-1])
        top_mid_grp.set_parent(ik_top_grp)
        name = NodeName(end_joint, desc='topMid',ext = 'LOC')
        top_mid_loc = Node.create('transform',name=name, parent=top_mid_grp)
        top_mid_loc.align(ik_ctrl_jnt_list[-1])
        name = name.replace_desc('topMidBase')
        top_mid_base_loc = top_mid_loc.duplicate(name=name)[0]
        top_mid_base_loc.align(ik_ctrl_jnt_list[-1])
        top_mid_base_loc.set_parent(top_mid_grp)
        

        name = NodeName(top_mid_loc, desc='top',ext='FKCTRL')
        end_fkctrl = self.add_ctrl(xform=ik_ctrl_jnt_list[-1],
            name=name,
            parent=ik_top_grp,
            shape='circle')
        end_fkctrl.lock(attrs='ts')

        self.add_constraint(
            'parent', 
            end_fkctrl,
            ik_child_joints[-1], 
            maintainOffset=True)
        self.add_constraint(
            'parent', 
            ik_ctrl_jnt_list[-1], 
            ik_top_grp, 
            maintainOffset=True)
        name = name.replace_num(1)
        mid_01_ikctrl = self.add_ctrl(
            xform=ik_ctrl_jnt_list[-2],
            name=name,
            ext='IKCTRL',
            parent=top_mid_base_loc,
            shape='sphereCurve')
        self.add_constraint(
            'orient',
            top_mid_loc,
            end_fkctrl,
            top_mid_base_loc, 
            maintainOffset=True)
        ik_up_loc.translate >> mid_01_ikctrl.plc_node.translate
        ik_up_loc.rotate >> mid_01_ikctrl.plc_node.rotate
        end_ikctrl.rotate >> end_fkctrl.sdk_node.rotate

        # Create IK help joints
        ik_ribbon_jnt_list=[]
        for index in range(0,3):
            name = NodeName(start_joint, desc='ikRibbon', num=index, ext='IKHLPJNT')
            ik_ribbon_jnt = ik_ctrl_jnt_list[index].duplicate(name=name,parentOnly=True)[0]
            if index == 0:
                ik_ribbon_jnt.set_parent(ws_root)
            else:
                ik_ribbon_jnt.set_parent(ik_ribbon_jnt_list[-1])
            ik_ribbon_jnt_list.append(ik_ribbon_jnt)
        ik_ribbon_jnt_list.append(ik_ctrl_jnt_list[-1])
        self.add_constraint(
            'parent',
            bottom_ik_loc,
            ik_ribbon_jnt_list[0],
            maintainOffset=False)
        self.add_constraint(
            'parent',
            mid_00_ikctrl,
            ik_ribbon_jnt_list[1],
            maintainOffset=False)
        self.add_constraint(
            'parent',
            mid_01_ikctrl,
            ik_ribbon_jnt_list[2],
            maintainOffset=False)

        # Create FK ribbon and binding it to ik help joints
        name = NodeName(start_joint,desc='Ribbon',ext='RIBBON')
        ik_ribbon,extrudeNode = cmds.extrude(
            ik_curve,
            extrudeType=0,
            direction=[1,0,0],
            length=1,
            degreeAlongLength=3,
            name=name,
            polygon=0)
        ik_ribbon = Node(ik_ribbon)
        cmds.delete(extrudeNode)
        cmds.rebuildSurface(
            ik_ribbon, 
            spansU=3,
            spansV=1,
            degreeU=3,
            degreeV=1,
            keepRange=0)
        name = NodeName(start_joint,desc='spineRibbon',ext='RIBBON')
        ik_ribbon_shape = ik_ribbon.get_shapes()[0]
        cmds.move(
            -0.5,
            ik_ribbon_shape.name+'.cv[0:5][0:1]',
            worldSpace=True,moveX=True,
            relative=True)
        base_ribbon = ik_ribbon.duplicate(name=name,parentOnly=False)[0]
        base_ribbon_shape = base_ribbon.get_shapes()[0]
        base_ribbon.set_parent(ws_root)
        ik_ribbon.set_parent(ws_root)
        name = NodeName(start_joint,desc='ikRibbon',ext='SKINCLUSTER')
        ik_skin=Node.create(
            'skinCluster', 
            ik_ribbon,ik_ribbon_jnt_list
            ,name=name,
            toSelectedBones=True)
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[0][0:1]',
            transformValue=[(ik_ribbon_jnt_list[0],1)])
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[1][0:1]',
            transformValue=[(ik_ribbon_jnt_list[0],0.8),(ik_ribbon_jnt_list[1],0.2)])
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[2][0:1]',
            transformValue=[(ik_ribbon_jnt_list[1],0.8),(ik_ribbon_jnt_list[2],0.2)])
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[3][0:1]',
            transformValue=[(ik_ribbon_jnt_list[1],0.2),(ik_ribbon_jnt_list[2],0.8)])
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[4][0:1]',
            transformValue=[(ik_ribbon_jnt_list[3],1)])
        cmds.skinPercent(
            ik_skin,
            ik_ribbon_shape.name+'.cv[5][0:1]',
            transformValue=[(ik_ribbon_jnt_list[3],1)])

        name = name.replace_desc('baseRibbon')
        base_skin=Node.create(
            'skinCluster',
            base_ribbon,
            ik_base_jnt_list,
            name=name,
            toSelectedBones=True)
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[0][0:1]',
            transformValue=[(ik_base_jnt_list[0],1)])
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[1][0:1]',
            transformValue=[(ik_base_jnt_list[0],0.8),(ik_base_jnt_list[1],0.2)])
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[2][0:1]',
            transformValue=[(ik_base_jnt_list[1],0.8),(ik_base_jnt_list[2],0.2)])
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[3][0:1]',
            transformValue=[(ik_base_jnt_list[1],0.2),(ik_base_jnt_list[2],0.8)])
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[4][0:1]',
            transformValue=[(ik_base_jnt_list[3],1)])
        cmds.skinPercent(
            base_skin,
            base_ribbon_shape.name+'.cv[5][0:1]',
            transformValue=[(ik_base_jnt_list[3],1)])
        # Create ik ribbon locators and base ribbon locators        
        name = NodeName(start_joint, desc='ikJoint', ext='MATRIXCONSTRAINT')
        ik_matrix_cns = Node.create('mhyGeometryInfo',name=name)
        ik_ribbon_shape.worldSpace[0] >> ik_matrix_cns.targetGeometry
        ik_ribbon.worldMatrix[0] >> ik_matrix_cns.targetMatrix

        name = NodeName(start_joint, desc='Base', ext='MATRIXCONSTRAINT')
        base_matrix_cns = Node.create('mhyGeometryInfo',name=name)
        base_ribbon_shape.worldSpace[0] >> base_matrix_cns.targetGeometry
        base_ribbon.worldMatrix[0] >> base_matrix_cns.targetMatrix

        closest_node = Node.create('closestPointOnSurface')
        base_ribbon_shape.worldSpace[0] >> closest_node.inputSurface
        
        for index in range(0,num_span):
            name = NodeName(start_joint,desc='ikJoint',num=index,ext='LOC')
            ik_loc = Node.create('transform',name=name)
            ik_loc.set_parent(ws_root)

            name = NodeName(start_joint,desc='BaseJoint',num=index,ext='LOC')
            base_loc = Node.create('transform',name=name)
            base_loc.set_parent(ws_root)

            joint = ik_joints[index]
            position = joint.get_translation(space='world')
            closest_node.inPosition.value=position
            u = closest_node.parameterU.value
            v = closest_node.parameterV.value

            ik_loc.inheritsTransform.value = False
            cmds.setAttr(ik_matrix_cns.name+'.coord[%d].v'%index, v)
            cmds.setAttr(ik_matrix_cns.name+'.coord[%d].u'%index, u)
            ik_matrix_cns.rotate[index] >> ik_loc.rotate
            ik_matrix_cns.translate[index] >> ik_loc.translate

            base_loc.inheritsTransform.value = False
            cmds.setAttr(base_matrix_cns.name+'.coord[%d].v'%index, v)
            cmds.setAttr(base_matrix_cns.name+'.coord[%d].u'%index, u)
            base_matrix_cns.rotate[index] >> base_loc.rotate
            base_matrix_cns.translate[index] >> base_loc.translate

            self.add_constraint('parent', base_loc, ik_joints[index], maintainOffset=True)
            if index<num_span-1:
                self.add_constraint('parent', ik_loc, ik_child_joints[index], maintainOffset=True)
            else:
                self.add_constraint('parent', end_fkctrl, ik_child_joints[index], maintainOffset=True)
            ik_child_joints[index].translate >> fk_child_joints[index].translate
            ik_child_joints[index].rotate >> fk_child_joints[index].rotate
        # Setup fk_ctrl visibility and lock transform
        fk_visi = self.add_limb_attr('bool', name='fkCtrl_visibility',
            keyable=True, defaultValue=False)
        for each in fk_ctrls:
            each.lock(attrs='ts')
            fk_visi >> each.v
        # Setup spine strech
        limb_stretch = self.add_limb_attr('float', name='stretch',
            keyable=True, defaultValue=0, max=1, min=0)
        ratio_attr = utils.create_curve_stretch_output(ik_curve)
        name = NodeName(ik_root, desc='stretch', num=1, ext='PLUSMINUSNODE')
        sub_node = Node.create('plusMinusAverage', name=name)
        sub_node.operation.value=2
        ratio_attr >> sub_node.input1D[0]
        sub_node.input1D[1].value = 1.0
        name = NodeName(ik_root, desc='stretch', ext='MDNODE')
        mult_node = Node.create('multiplyDivide', name=name)
        mult_node.operation.value=1
        sub_node.output1D >> mult_node.input1X
        limb_stretch >> mult_node.input2X
        name = NodeName(ik_root, desc='stretch', num=2, ext='PLUSMINUSNODE')
        plus_node = Node.create('plusMinusAverage', name=name)
        plus_node.operation.value=1
        plus_node.input1D[0].value=1
        mult_node.outputX >> plus_node.input1D[1]

        for jnt in ik_ctrl_jnt_list:
            mult = Node.create(
                'multiplyDivide', name=NodeName(jnt, ext='MDNODE'))
            length = jnt.attr('translate' + long_axis[-1]).value
            mult.operation.value = 1
            mult.input1X.value = length
            plus_node.output1D >> mult.input2X
            mult.outputX >> jnt.attr('translate' + long_axis[-1])

        # setup leaf parent and hip connection
        name = NodeName(start_joint, desc='leafParent',ext='GRP')
        leafParent = Node.create('transform',name=name)
        leafParent.set_parent(ik_root)
        self.add_constraint('parent',ik_joints[-1],leafParent,maintainOffset=False)
        self.ctrl_leaf_parent=leafParent

        self.ik_bottom_plug = ik_bottom_grp


class SplineSpine(BaseSpine):
    """Spline spine class.
    """

    # -- input parameters

    @pa.int_param(default=8, min_value=3)
    def num_span(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def simplify_curve(self):
        """TODO doc."""

    # --- end of parameter definition

    def run(self):
        """Builds the limb ctrl rig."""
        start_joint = self.rig_skeleton[0][0]
        end_joint = self.rig_skeleton[0][-1]
        limb_root = self.limb_root.value
        ws_root = self.ws_root

        # create spline ik joint chain
        name = NodeName(start_joint, ext='GRP')
        root = Node.create('transform', name=name)
        root.set_parent(ws_root)
        self.add_constraint('parent', limb_root, root, maintainOffset=False)
        ik_joints = []
        for joint in self.rig_skeleton[0]:
            name = NodeName(joint, ext='IKJNT')
            ik_jnt = joint.duplicate(name=name, parentOnly=True)[0]
            parent = ik_joints[-1] if ik_joints else root
            ik_jnt.set_parent(parent)
            self.add_constraint('parent', ik_jnt, joint, maintainOffset=True)
            ik_joints.append(ik_jnt)

        # check orientation
        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)
        long_axis = joint_chain.long_axis
        if long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(long_axis))
        else:
            self.warn('Not all joint has the same orientation.')

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set spine joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # Create Spline IK Handle
        name = NodeName(start_joint, ext='SPLINEHAN')
        result = cmds.ikHandle(
            solver='ikSplineSolver',
            numSpans=self.num_span.value,
            parentCurve=False,
            startJoint=ik_joints[0],
            endEffector=ik_joints[-1],
            simplifyCurve=self.simplify_curve.value,
            name=name)
        ik_handle, ik_effector, ik_curve = [Node(n) for n in result]
        ik_effector.name = name.replace_ext('EFFECTOR')
        ik_curve.name = name.replace_ext('CURVE')

        # add ctrl joints
        self.debug('STARTING DUPLICATE')
        name = NodeName(
            start_joint, part='splineBottom', num=0, ext='CTRLJNT')
        start_ctrl_jnt = start_joint.duplicate(
            name=name, radius=5, parentOnly=True)[0]
        mid01_ctrl_jnt = start_joint.duplicate(
            name=name.replace_part('spineMid01'), radius=5, parentOnly=True)[0]
        mid02_ctrl_jnt = start_joint.duplicate(
            name=name.replace_part('spineMid02'), radius=5, parentOnly=True)[0]
        end_ctrl_jnt = end_joint.duplicate(
            name=name.replace_part('spineTop'), radius=5, parentOnly=True)[0]

        mid01_pos = mmath.get_fractional_position(
            start_joint, end_joint, fraction=0.3)
        mid02_pos = mmath.get_fractional_position(mid01_pos, end_joint)
        mid01_ctrl_jnt.set_translation(mid01_pos, space='world')
        mid02_ctrl_jnt.set_translation(mid02_pos, space='world')

        cmds.parent(
            start_ctrl_jnt, mid01_ctrl_jnt,
            mid02_ctrl_jnt, end_ctrl_jnt, ws_root)

        # create main ctrls
        ctrl_scale = (7, 1, 4)
        name = NodeName(start_joint, ext='FKCTRL')
        start_ctrl = self.add_ctrl(
            name=name,
            xform=start_ctrl_jnt,
            shape='circle',
            rot=(0, 0, 90),
            scale=ctrl_scale)

        self.add_constraint(
            'parent', start_ctrl, start_ctrl_jnt, maintainOffset=True)

        name = name.replace_num(1)
        mid01_ctrl = self.add_ctrl(
            name=name,
            xform=mid01_ctrl_jnt,
            shape='circle',
            rot=(0, 0, 90),
            scale=ctrl_scale)

        self.add_constraint(
            'parent', mid01_ctrl, mid01_ctrl_jnt, maintainOffset=True)

        name = name.replace_num(2)
        mid02_ctrl = self.add_ctrl(
            name=name,
            xform=mid02_ctrl_jnt,
            rot=(0, 0, 90),
            shape='circle',
            scale=ctrl_scale)

        self.add_constraint(
            'parent', mid02_ctrl, mid02_ctrl_jnt, maintainOffset=True)

        name = name.replace_num(3)
        end_ctrl = self.add_ctrl(
            name=name,
            xform=end_ctrl_jnt,
            shape='circle',
            rot=(0, 0, 90),
            scale=ctrl_scale)

        self.add_constraint(
            'parent', end_ctrl, end_ctrl_jnt, maintainOffset=True)

        self.ctrl_leaf_parent = end_ctrl

        # connect hip node
        parent_limb = self.get_parent_limb()
        if parent_limb and parent_limb.limb_type == 'hip':
            hip_leaf = parent_limb.get_ctrls()[-1]
            if hip_leaf:
                self.add_constraint(
                    'parent', hip_leaf, start_ctrl.plc_node, maintainOffset=True)

        # bind ctrl joints
        cmds.skinCluster(
            start_ctrl_jnt, mid01_ctrl_jnt, mid02_ctrl_jnt,
            end_ctrl_jnt, ik_curve, maximumInfluences=2,
            name=NodeName(ik_curve, ext='SKINCLUSTER'))

        # set up bind joints stretchable
        ratio_attr = utils.create_curve_stretch_output(ik_curve)

        for jnt in ik_joints:
            mult = Node.create(
                'multiplyDivide', name=NodeName(jnt, ext='MDNODE'))
            length = jnt.attr('translate' + long_axis[-1]).value
            mult.operation.value = 1
            mult.input1X.value = length
            ratio_attr >> mult.input2X
            mult.outputX >> jnt.attr('translate' + long_axis[-1])

        # average translate mid ctrls in x-axis
        utils.create_stretchy_xforms((
            start_ctrl,
            mid01_ctrl.sdk_node,
            mid02_ctrl.sdk_node,
            end_ctrl))

        # clean up
        for each in (start_ctrl, mid01_ctrl, mid02_ctrl, end_ctrl):
            each.lock(attrs='sv')

        cmds.parent(ik_handle, ik_curve, ws_root)
        for each in (ik_handle, ik_effector, ik_curve):
            each.lock()


class FKSpine(BaseSpine):
    """FK spine class.
    """

    # -- input parameters

    @pa.bool_param(default=False)
    def enable_scale(self):
        """If True, enable scale constraint."""

    @pa.bool_param(default=True)
    def ctrl_on_end_joint(self):
        """If True, build a ctrl on each finger end joint."""

    @pa.list_param()
    def bend_joints(self):
        """If True, build a ctrl on each finger end joint."""

    # --- end of parameter definition

    def __init__(self, *args, **kwargs):
        """Initializes a new limb object."""
        super(FKSpine, self).__init__(*args, **kwargs)
        self.rotate_order.default = 'xzy'

    def run(self):
        """Builds the limb ctrl rig."""
        # get joint chain
        joint_chain = jutil.JointChain(
            start=self.rig_skeleton[0][0], end=self.rig_skeleton[0][-1])
        joints = joint_chain.joints
        self.debug('Joint Chain Length: {}'.format(joint_chain.chain_length))

        # check orientation
        long_axis = joint_chain.long_axis
        if long_axis:
            self.debug('input joint chain long axis '
                       'alignment check: {}-axis'.format(long_axis))
        else:
            self.warn('Not all joint has the same orientation.')

        # reset rotation order
        rot_order = self.rotate_order.value
        self.debug('set spine joint rotation order: {}'.format(rot_order))
        joint_chain.set_rotate_order(rot_order)

        # create main FK ctrls
        fk_joints = joints
        if not self.ctrl_on_end_joint.value:
            fk_joints.pop(-1)
        do_scale = self.enable_scale.value
        ctrl_scale = (7, 1, 4)

        for i, jnt in enumerate(fk_joints):
            ctrls = self.get_ctrls()
            parent = ctrls[-1] if ctrls else self.ctrl_root
            fk_ctrl = self.add_ctrl(
                xform=jnt,
                parent=parent,
                ext='FKCTRL',
                rot=(0, 0, 90),
                shape='circle',
                scale=ctrl_scale)

            self.add_constraint(
                'parent', fk_ctrl, jnt, maintainOffset=True)
            if do_scale:
                self.add_constraint(
                    'scale', fk_ctrl, jnt, maintainOffset=True)

            # set leaf parent node
            if jnt == fk_joints[-1]:
                self.ctrl_leaf_parent = fk_ctrl

        # create bend joint ctrls
        jnt_rotate_order = jnt.rotateOrder.value
        bend_ctrls = []
        for b_jnt in [Node(n) for n in self.bend_joints.value or []]:
            self.ls_name.fullname = b_jnt

            parent_jnt = b_jnt.get_parent(type_='joint')
            if not parent_jnt:
                self.error(
                    'bend joint: {} dose not have a parent joint'.format(b_jnt))

            parent_ctrl = parent_jnt.ctrl
            bend_ctrl = self.add_ctrl(
                xform=b_jnt,
                parent=parent_ctrl,
                ext='CTRL',
                rot_order=jnt_rotate_order,
                shape='square',
                scale=(1, 1, 1))

            self.add_constraint(
                'parent', bend_ctrl, b_jnt, maintainOffset=True)
            if do_scale:
                self.add_constraint(
                    'scale', bend_ctrl, b_jnt, maintainOffset=True)

            bend_ctrls.append(bend_ctrl)

        # add bend ctrls vis attr
        attr = self.add_limb_attr(
            'bool', name='showBendCtrls', keyable=True, defaultValue=False)
        for ctrl in bend_ctrls:
            attr > ctrl.v


