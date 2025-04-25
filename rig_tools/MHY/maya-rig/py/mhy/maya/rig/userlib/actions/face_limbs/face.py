from maya import cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.face.weighted_transform_system as wts
import mhy.maya.rig.face.parameter_driver_system as pds
import mhy.maya.rig.face.blinkline_system as blink
import mhy.maya.rig.face.curve_driver_system as cds
import traceback

from importlib import reload
reload(blink)
reload(pds)
reload(cds)

class HiFace(bl.BaseLimb):
    """
    TODO doc

    :limb type: face

    """

    _LIMB_TYPE = 'face'
    _CTRL_VIS_ATTR = 'face_ctrl'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'face'

    # -- input parameters

    @pa.str_param(default='FKCTRL')
    def ctrl_ext(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def weighted_transform(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def parameter_driver(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def parameter_tracer(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def paremeter_blinkline(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def is_pose_rig(self):
        """TODO doc."""

    @pa.str_param(default='Face')
    def face_mesh(self):
        """TODO doc."""

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
        """Core execution method."""
        start_joint = self.rig_skeleton[0][0]
        ws_root = self.ws_root

        # get input parameters
        ctrl_ext = self.ctrl_ext.value
        ctrl_scale = (.1, .1, .1)
        face_mesh = self.face_mesh.value

        # get face joints from startJoint,
        # face root joint will be excluded from bnd joint SET
        bind_joints = jutil.get_joints_in_category('bind')
        inf_joints = jutil.get_joints_in_category('influence', joints=bind_joints)
        wts_joints = jutil.get_joints_in_category('wts', joints=inf_joints)
        jaw_joints = jutil.get_joints_in_category('jaw', joints=bind_joints)
        teeth_joints = jutil.get_joints_in_category('teeth', joints=bind_joints)
        tongue_joints = jutil.get_joints_in_category('tongue', joints=bind_joints)
        lip_joints = jutil.get_joints_in_category('lip', joints=bind_joints)
        lip_tip_joints = jutil.get_joints_in_category('lip_tip', joints=bind_joints)

        # create face root ctrl
        root_ctrl = self.add_ctrl(
            xform=start_joint,
            ext=ctrl_ext,
            shape='cube',
            scale=ctrl_scale)
        root_ctrl.shape.v.value = False
        root_ctrl.lock()
        self.add_constraint(
            'point', root_ctrl, start_joint, maintainOffset=True)
        self.add_constraint(
            'orient', root_ctrl, start_joint, maintainOffset=True)

        # create face influence joint ctrls
        for jnt in inf_joints:
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=root_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET', 'POSE'))
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)
            if jnt in lip_joints:
                cmds.setAttr("{}.xrayMode".format(ctrl.shape), True)
            
        # create jaw joint ctrls
        '''
        bbMaxX = cmds.getAttr(face_mesh+'.boundingBoxMaxX')
        bbMinY = cmds.getAttr(face_mesh+'.boundingBoxMinY')
        bbMaxZ = cmds.getAttr(face_mesh+'.boundingBoxMaxZ')
        shape='circle',
        pos=(0.0, bbMinY/2, 0.0),
        scale=(bbMaxX*0.8, 1.0, bbMaxZ),
        '''
        jaw_jnt = jaw_joints[0]
        jaw_ctrl = self.add_ctrl(
            xform=jaw_jnt,
            parent=root_ctrl,
            ext=ctrl_ext, 
            shape='cube',
            scale=(2.0, 2.0, 2.0),
            rot_order=start_joint.rotateOrder.value,
            group_exts=('PLC', 'OFFSET', 'POSE'))
        jaw_ctrl.lock('sv')
        self.add_constraint('point', jaw_ctrl, jaw_jnt, maintainOffset=True)
        self.add_constraint('orient', jaw_ctrl, jaw_jnt, maintainOffset=True)
            
        # create tongue joint ctrls
        parent_ctrl = jaw_ctrl
        for jnt in tongue_joints:
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=parent_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET'))
            # hide tongue ctrls for pose rig
            if self.is_pose_rig:
                ctrl.v.value = False
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)
            parent_ctrl = ctrl
            
        # create teeth joint ctrls
        for jnt in teeth_joints:
            if 'palate' in jnt.name:
                parent_ctrl = root_ctrl
            else:
                parent_ctrl = jaw_ctrl
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=parent_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET'))
            # hide tongue ctrls for pose rig
            if self.is_pose_rig:
                ctrl.v.value = False
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)

        # add deformableTransform system
        if self.weighted_transform.value:
            wts_xforms = []
            for each in wts_joints:
                wts_xforms.append(Node(NodeName(each, ext=ctrl_ext)))
  
            WTS = wts.WeightedTransformSystem(
                wts_xforms,
                ctrl_ext=ctrl_ext,
                ws_root=ws_root)
            self.wts, self.wts_deform_mesh, self.wts_chew_target = WTS.create()
            self.wts_deform_mesh.v.value = False
            self.wts_chew_target.v.value = False
            
            # add jaw cluster weighted node
            wn_name = NodeName(self.wts_deform_mesh, ext='WEIGHTED')
            wnplc_name = NodeName(self.wts_deform_mesh, ext='WEIGHTEDPLC')
            wt_node = Node.create('transform', parent=self.wts, name=wn_name)
            wt_node_plc = Node.create('transform', parent=self.wts, name=wnplc_name)
            wt_node.align(jaw_ctrl)
            wt_node_plc.align(jaw_ctrl)
            wt_node.set_parent(wt_node_plc)
            
            # add jaw down cluster
            jaw_cluster = 'jawDown_CLUSTER'
            cmds.cluster(
                self.wts_deform_mesh,
                bindState=True,
                weightedNode=(wt_node, wt_node),
                n=jaw_cluster)
                
            # connect jaw ctrl to weighted node
            src_nodes = [jaw_ctrl, jaw_ctrl.offset_node, jaw_ctrl.pose_node]
            xform_sum_connect(src_nodes, wt_node)
                
        # add parameter skin sliding system
        if self.parameter_driver.value:
            PDS = pds.ParameterDriverSystem(
                parameter_tracer=self.parameter_tracer.value,
                ws_root=ws_root)
            PDS.build()
            
        # add parameter blinkline system
        if self.paremeter_blinkline.value:
            try:
                side = 'L'
                BLINK_L = blink.BlinklineSystem(
                    blink_attr = self.get_blink_attr(side),
                    bend_attr = self.get_bend_attr(side),
                    ws_root=ws_root)
                
                side = 'R'
                BLINK_R = blink.BlinklineSystem(
                    blink_attr = self.get_blink_attr(side),
                    bend_attr = self.get_bend_attr(side),
                    ws_root=ws_root)

                blinkline_handles_L = BLINK_L.build()
                blinkline_handles_R = BLINK_R.build()
                
                # set bend defaut
                self.get_bend_attr('L').value = -0.85
                self.get_bend_attr('R').value = -0.85
                
            except BaseException as e:
                traceback.print_exc()
                raise e
        
        # parent lip tip joints to lip joints
        # TODO: add sticky lips func
        for tipjnt in lip_tip_joints: 
            tipdesc = NodeName(tipjnt).desc
            lipjnt = NodeName(tipjnt, desc=tipdesc.replace('Tip',''))
            tipjnt.set_parent(lipjnt)
            

        ws_root.unlock('v')
        if self.is_pose_rig.value:
            ws_root.v.value = True


    def get_blink_attr(self, side):
        """Returns the blink attribute. Create a new one if not exists."""
        name = 'blink_{}'.format(side)
        limb_root = self.limb_root.value
        if limb_root.shape.has_attr(name):
            return limb_root.shape.attr(name)
        return self.add_limb_attr(
            'float', name=name, as_pose=True,
            keyable=True, minValue=0, maxValue=1, defaultValue=0)


    def get_bend_attr(self, side):
        """Returns the bend attribute. Create a new one if not exists."""
        name = 'blinkline_bend_{}'.format(side)
        limb_root = self.limb_root.value
        if limb_root.shape.has_attr(name):
            return limb_root.shape.attr(name)
        return self.add_limb_attr(
            'float', name=name, as_pose=True,
            keyable=True, minValue=-1, maxValue=1, defaultValue=0)


# Old Face
PRE_EXCLUDE_RIG_JOINTS = (
    'face_eye_00_L_RIGJNT',
    'face_eye_00_R_RIGJNT',
    'face_eyelidBase_00_R_RIGJNT',
    'face_eyelidBase_00_L_RIGJNT',
    'face_root_00_M_RIGJNT')

PRE_EXCLUDE_WTS_JOINTS = (
    'face_eyelidBase_00_L_RIGJNT',
    'face_eyelidBase_00_R_RIGJNT',
    'face_jaw_00_M_RIGJNT',
    'face_root_00_M_RIGJNT')


class Face(bl.BaseLimb):
    """
    TODO doc

    :limb type: face
    """

    _LIMB_TYPE = 'face'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'face'

    # -- input parameters

    @pa.str_param(default='FKCTRL')
    def ctrl_ext(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def weighted_transform(self):
        """TODO doc."""

    @pa.list_param(item_type='str')
    def weighted_xform_exclude(self):
        """TODO doc."""

    @pa.list_param(item_type='str')
    def face_joint_extra_exclude(self):
        """TODO doc."""

    @pa.str_param(default='face_jaw_00_M_RIGJNT')
    def jaw_joint(self):
        """TODO doc."""

    @pa.float_param(default=45)
    def jaw_open_max(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def insert_jaw_offset(self):
        """TODO doc."""

    @pa.str_param(default='face_top_00_M_RIGJNT')
    def face_top_joint(self):
        """TODO doc."""

    @pa.str_param(default='face_bot_00_M_RIGJNT')
    def face_bot_joint(self):
        """TODO doc."""

    @pa.list_param(item_type='str')
    def tongue_joints(self):
        """TODO doc."""

    @pa.list_param(item_type='str')
    def palate_joints(self):
        """TODO doc."""

    # --- output parameters

    @pa.str_param(output=True)
    def jaw_ctrl(self):
        """TODO doc."""

    @pa.str_param(output=True)
    def jaw_offset(self):
        """TODO doc."""

    @pa.str_param(output=True)
    def face_top_ctrl(self):
        """TODO doc."""

    @pa.str_param(output=True)
    def face_bot_ctrl(self):
        """TODO doc."""

    @pa.list_param(item_type='str', output=True)
    def face_joints(self):
        """TODO doc."""

    @pa.str_param(output=True)
    def wts_deform_mesh(self):
        """TODO doc."""

    # --- end of parameter definition

    def __init__(self, *args, **kwargs):
        """Initializes a new limb object."""
        super(Face, self).__init__(*args, **kwargs)
        # update some parameter defaults
        self.tongue_joints.value = (
            'face_tongue_00_M_RIGJNT',
            'face_tongue_01_M_RIGJNT',
            'face_tongue_02_M_RIGJNT')
        self.palate_joints.value = (
            'face_upperPalate_00_M_RIGJNT',
            'face_lowerPalate_00_M_RIGJNT')

    def run(self):
        """Core execution method."""
        start_joint = self.rig_skeleton[0][0]
        ws_root = self.ws_root

        # get input parameters
        ctrl_ext = self.ctrl_ext.value
        ctrl_scale = (.1, .1, .1)
        jaw_open_max = self.jaw_open_max.value

        tongue_joints = [Node(j) for j in self.tongue_joints.value]
        palate_joints = [Node(j) for j in self.palate_joints.value]
        face_top_joint = Node(self.face_top_joint.value)
        face_bot_joint = Node(self.face_bot_joint.value)
        jaw_joint = Node(self.jaw_joint.value)

        pre_exclude_wts_joints = list(PRE_EXCLUDE_WTS_JOINTS)
        pre_exclude_wts_joints += [j.name for j in tongue_joints]
        pre_exclude_wts_joints += [j.name for j in palate_joints]
        pre_exclude_wts_joints += [face_top_joint.name, face_bot_joint.name]
        pre_exclude_xforms = [NodeName(j, ext=ctrl_ext)
                              for j in pre_exclude_wts_joints]
        exclude_joints = list(PRE_EXCLUDE_RIG_JOINTS) + \
            self.face_joint_extra_exclude.value
        weighted_xform_exclude = self.weighted_xform_exclude.value

        # get face joints from startJoint,
        # face root joint should not be in bnd joint SET
        face_hierarchy_joints = start_joint.get_hierarchy(skip_self=True)
        face_joints = [j for j in face_hierarchy_joints
                       if j.name not in exclude_joints]

        # create face root ctrl
        root_ctrl = self.add_ctrl(
            xform=start_joint,
            ext=ctrl_ext,
            shape='cube',
            scale=ctrl_scale)
        self.add_constraint(
            'point', root_ctrl, start_joint, maintainOffset=True)
        self.add_constraint(
            'orient', root_ctrl, start_joint, maintainOffset=True)

        # find joints who have child joints
        child_parent_joint_dict = {}
        for jnt in self.face_joints:
            for child in jnt.get_children(type_='joint'):
                child_parent_joint_dict[child] = jnt

        # create fk ctrl
        child_joint_ctrl_dict = {}
        for jnt in self.face_joints:
            # tmp set non-face ctrl shape
            if jnt == jaw_joint:
                kwargs = {'shape': 'circleY'}
            elif jnt in tongue_joints:
                kwargs = {'shape': 'circleX'}
            elif jnt in palate_joints:
                kwargs = {'shape': 'circleY'}
            elif jnt in (face_top_joint, face_bot_joint):
                kwargs = {'shape': 'circleY'}
            else:
                kwargs = {'shape': 'cube',
                          'group_exts': ('PLC', 'OFFSET', 'POSE')}

            ctrl = self.add_ctrl(
                xform=jnt,
                parent=root_ctrl,
                ext=ctrl_ext,
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                **kwargs)
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)

            if jnt in child_parent_joint_dict.keys():
                child_joint_ctrl_dict[jnt] = ctrl

            # set jaw ctrl rx limits
            if jnt == self.jaw_joint:
                jaw_ctrl = ctrl
                jaw_ctrl.set_limit(
                    enableRotationX=(True, True), rotationX=(0.0, jaw_open_max))

            # set face bot ctrl vars
            if jnt == face_top_joint:
                face_top_ctrl = ctrl
            if jnt == face_bot_joint:
                face_bot_ctrl = ctrl

        # re-parent child ctrls to their real parents
        if child_joint_ctrl_dict:
            for jnt, ctrl in child_joint_ctrl_dict.items():
                parent = child_parent_joint_dict[jnt].ctrl
                ctrl.plc_node.set_parent(parent)

        # insert jaw behavior offset node
        if self.insert_jaw_offset.value:
            ch_nodes = jaw_ctrl.get_children(type_='transform')
            jaw_offset = insert_jaw_offset_node(
                jaw_ctrl, children=ch_nodes)
            jaw_offset.lock('txrsv')

        # add deformableTransform system
        if self.weighted_transform.value:
            exclude_xforms = pre_exclude_xforms + weighted_xform_exclude
            wts_xforms = [c for c in self.get_ctrls()
                          if c.name not in exclude_xforms]
            WTS = wts.WeightedTransformSystem(
                wts_xforms,
                ctrl_ext=ctrl_ext,
                ws_root=ws_root)
            wts_deform_mesh = WTS.create()

        ws_root.unlock('v')

        # generate skin proxymesh

        # set output parameters
        self.jaw_ctrl.value = jaw_ctrl.name
        self.jaw_offset.value = jaw_offset.name
        self.face_top_ctrl.value = face_top_ctrl.name
        self.face_bot_ctrl.value = face_bot_ctrl.name
        self.face_joints.value = face_joints.name
        if self.weighted_transform.value:
            self.wts_deform_mesh.value = wts_deform_mesh.name


class LumiFace(bl.BaseLimb):
    """
    TODO doc

    :limb type: face

    """

    _LIMB_TYPE = 'face'
    _CTRL_VIS_ATTR = 'face_ctrl'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'face'

    # -- input parameters

    @pa.str_param(default='FKCTRL')
    def ctrl_ext(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def weighted_transform(self):
        """TODO doc."""

    @pa.bool_param(default=True)
    def parameter_driver(self):
        """TODO doc."""
        
    @pa.bool_param(default=True)
    def curve_driver(self):
        """TODO doc."""
        
    @pa.bool_param(default=True)
    def curve_blinkline(self):
        """TODO doc."""

    @pa.bool_param(default=False)
    def is_pose_rig(self):
        """TODO doc."""

    @pa.str_param(default='Face')
    def face_mesh(self):
        """TODO doc."""


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
        """Core execution method."""
        start_joint = self.rig_skeleton[0][0]
        #start_joint = jutil.get_joints_in_category('face_base')[0]

        # get input parameters
        ctrl_ext = self.ctrl_ext.value
        ctrl_scale = (.1, .1, .1)
        face_mesh = self.face_mesh.value

        # get basic joint groups
        bind_joints = jutil.get_joints_in_category('bind')      # all joints under face root joint, need tp solove bind/rig category issue
        skin_joints = jutil.get_joints_in_category('influence')
        face_ctrl_joints = jutil.get_joints_in_category('face_ctrl')
        wts_joints = jutil.get_joints_in_category('wts')
        jaw_joints = jutil.get_joints_in_category('jaw')
        teeth_joints = jutil.get_joints_in_category('teeth')
        tongue_joints = jutil.get_joints_in_category('tongue')
        
        # blinkline system
        eyelid_joints = jutil.get_joints_in_category('lid')
        eye_corner_joints = jutil.get_joints_in_category('lid_corner')
        crv_bind_joints = jutil.get_joints_in_category('lid_crv_bind')
        
        # curve flc driver system
        cds_mouth_joints = jutil.get_joints_in_category('cds_mouth')
        cds_mth_crnr_joints = jutil.get_joints_in_category('cds_mouth_crnr')
        cds_lip_joints = jutil.get_joints_in_category('cds_lip')
        cds_lip_crnr_joints = jutil.get_joints_in_category('cds_lip_crnr')
        cds_lip_bind_joints = jutil.get_joints_in_category('cds_lip_bind')

        # sticky lips system
        lip_joints = cds_lip_joints
        lip_tip_joints = jutil.get_joints_in_category('lip_tip')

        # create face root ctrl
        root_ctrl = self.add_ctrl(
            xform=start_joint,
            ext=ctrl_ext,
            shape='hexagram',
            scale=(1,1,1))
        #root_ctrl.shape.v.value = False
        root_ctrl.lock()
        self.add_constraint(
            'point', root_ctrl, start_joint, maintainOffset=True)
        self.add_constraint(
            'orient', root_ctrl, start_joint, maintainOffset=True)

        # create pre-tagged face joint ctrls
        for jnt in face_ctrl_joints:
                
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=root_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET', 'POSE'))       # changed offset/pose order <<<<
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)
            if jnt in lip_joints:
                cmds.setAttr("{}.xrayMode".format(ctrl.shape), True)
                
        # parent lid ctrl to lid_base ctrl
        for jnt in eyelid_joints:
            base_jnt = Node(jnt).get_parent()
            ctrl_plc = Node(jutil.get_ctrl(jnt)).plc_node
            base_ctrl = Node(jutil.get_ctrl(base_jnt))
            ctrl_plc.set_parent(base_ctrl)
            
            
        # Build Jaw Ctrls
        jaw_jnt = jaw_joints[0]
        jaw_ctrl = self.add_ctrl(
            xform=jaw_jnt,
            parent=root_ctrl,
            ext=ctrl_ext, 
            shape='cube',
            scale=(2.0, 2.0, 2.0),
            rot_order=start_joint.rotateOrder.value,
            group_exts=('PLC', 'OFFSET', 'POSE'))
        jaw_ctrl.lock('sv')
        self.add_constraint('point', jaw_ctrl, jaw_jnt, maintainOffset=True)
        self.add_constraint('orient', jaw_ctrl, jaw_jnt, maintainOffset=True)
            
            
        # Build Tongue Ctrls
        parent_ctrl = jaw_ctrl
        for jnt in tongue_joints:
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=parent_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET'))
            # hide tongue ctrls for pose rig
            #if self.is_pose_rig:
            #    ctrl.v.value = False       # tmp <<<<<<<<<<<<<<<<<<<<<<<<<<<
            #TODO:  separate tongue and gum to a limb
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)
            parent_ctrl = ctrl
        
    
        # Build Teeth Joint Ctrls
        for jnt in teeth_joints:
            if 'palate' in jnt.name:
                parent_ctrl = root_ctrl
            else:
                parent_ctrl = jaw_ctrl
            ctrl = self.add_ctrl(
                xform=jnt,
                parent=parent_ctrl,
                ext=ctrl_ext,
                shape='cube',
                scale=ctrl_scale,
                rot_order=start_joint.rotateOrder.value,
                group_exts=('PLC', 'OFFSET'))
            # hide teeth ctrls for pose rig
            #if self.is_pose_rig:
            #    ctrl.v.value = False       #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            #TODO:  separate tongue and gum to a limb
            ctrl.lock('sv')
            self.add_constraint('point', ctrl, jnt, maintainOffset=True)
            self.add_constraint('orient', ctrl, jnt, maintainOffset=True)
        
        
        # Add DeformableTransform System
        if self.weighted_transform.value:
            wts_xforms = []
            for each in wts_joints:
                wts_xforms.append(Node(NodeName(each, ext=ctrl_ext)))
                
            WTS = wts.WeightedTransformSystem(
                wts_xforms,
                ctrl_ext=ctrl_ext,
                ws_root=self.ws_root)
            self.wts, self.wts_deform_mesh, self.wts_chew_target = WTS.create()
            self.wts_deform_mesh.v.value = False
            self.wts_chew_target.v.value = False
            
            # add jaw cluster weighted node
            wn_name = NodeName(self.wts_deform_mesh, ext='WEIGHTED')
            wnplc_name = NodeName(self.wts_deform_mesh, ext='WEIGHTEDPLC')
            wt_node = Node.create('transform', parent=self.wts, name=wn_name)
            wt_node_plc = Node.create('transform', parent=self.wts, name=wnplc_name)
            wt_node.align(jaw_ctrl)
            wt_node_plc.align(jaw_ctrl)
            wt_node.set_parent(wt_node_plc)
            
            # add jaw down cluster
            jaw_cluster = 'jawDown_CLUSTER'
            cmds.cluster(
                self.wts_deform_mesh,
                bindState=True,
                weightedNode=(wt_node, wt_node),
                n=jaw_cluster)
            # connect jaw ctrl to weighted node
            src_nodes = [jaw_ctrl, jaw_ctrl.offset_node, jaw_ctrl.pose_node]
            xform_sum_connect(src_nodes, wt_node)
        

        # Add Curve Blinkline System
        if self.curve_blinkline.value:
            lid_jnts_L = [NodeName(jnt) for jnt in eyelid_joints if NodeName(jnt).side=='L']
            lid_jnts_R = [NodeName(jnt) for jnt in eyelid_joints if NodeName(jnt).side=='R']
            crnr_jnts_L = [NodeName(jnt) for jnt in eye_corner_joints if NodeName(jnt).side=='L']
            crnr_jnts_R = [NodeName(jnt) for jnt in eye_corner_joints if NodeName(jnt).side=='R']
            crv_jnts_L = [NodeName(jnt) for jnt in crv_bind_joints if NodeName(jnt).side=='L']
            crv_jnts_R = [NodeName(jnt) for jnt in crv_bind_joints if NodeName(jnt).side=='R']
            
            lid_jnts_upper_L = [jnt for jnt in lid_jnts_L if 'Upper' in jnt.desc]
            lid_jnts_lower_L = [jnt for jnt in lid_jnts_L if 'Lower' in jnt.desc]
            lid_jnts_upper_R = [jnt for jnt in lid_jnts_R if 'Upper' in jnt.desc]
            lid_jnts_lower_R = [jnt for jnt in lid_jnts_R if 'Lower' in jnt.desc]
            
            bnd_jnts_crnr_L = [jnt for jnt in crv_jnts_L if 'Crnr' in jnt.desc]
            bnd_jnts_upper_L = [jnt for jnt in crv_jnts_L if 'Upper' in jnt.desc]
            bnd_jnts_upper_L.insert(0, bnd_jnts_crnr_L[0])
            bnd_jnts_upper_L.insert(-1, bnd_jnts_crnr_L[1])
            
            bnd_jnts_lower_L = [jnt for jnt in crv_jnts_L if 'Lower' in jnt.desc]
            bnd_jnts_lower_L.insert(0, bnd_jnts_crnr_L[0])
            bnd_jnts_lower_L.insert(-1, bnd_jnts_crnr_L[1])
            
            bnd_jnts_crnr_R = [jnt for jnt in crv_jnts_R if 'Crnr' in jnt.desc]
            bnd_jnts_upper_R = [jnt for jnt in crv_jnts_R if 'Upper' in jnt.desc]
            bnd_jnts_upper_R.insert(0, bnd_jnts_crnr_R[0])
            bnd_jnts_upper_R.insert(-1, bnd_jnts_crnr_R[1])
            
            bnd_jnts_lower_R = [jnt for jnt in crv_jnts_R if 'Lower' in jnt.desc]
            bnd_jnts_lower_R.insert(0, bnd_jnts_crnr_R[0])
            bnd_jnts_lower_R.insert(-1, bnd_jnts_crnr_R[1])
            
            
            # compose blink joints dict
            blink_setup_data = [
                [ crnr_jnts_L, (lid_jnts_upper_L, bnd_jnts_upper_L), (lid_jnts_lower_L, bnd_jnts_lower_L) ],
                [ crnr_jnts_R, (lid_jnts_upper_R, bnd_jnts_upper_R), (lid_jnts_lower_R, bnd_jnts_lower_R) ]
            ]
            
            for blink_data in blink_setup_data:
                crnr_jnts = blink_data[0]
                lid_jnts_pairs = blink_data[1:]
                
                for lid_pair in lid_jnts_pairs:
                    lid_jnts, bnd_jnts = lid_pair
                    if lid_jnts:
                        BLINK = blink.CurveBlinklineSystem(
                            lid_profile_joints = lid_jnts,
                            eye_corner_joints = crnr_jnts,
                            lid_curve_joints = bnd_jnts,
                            ws_root = self.ws_root,
                            limb_root = self.limb_root.value )
                            
                        blinkline_handles = BLINK.build()       # need to use bend curve gerated from the lower eyelid jnts.

                    else:
                        continue

        # Add Parameter Skin Sliding System to eyelid curve corner ctrls
        if self.parameter_driver.value:
            
            crnr_joints = bnd_jnts_crnr_L + bnd_jnts_crnr_R
            crnr_PDS = pds.ParameterDriverSystem(
                joints = crnr_joints,
                build_tracer = 'worldspace',
                ws_root = self.ws_root)
            crnr_PDS.build()
        
        
        # Initial Texture Driver System
        # Add distance node for furtue texture blending
        #(1.846395, 0.0) > (0.0830429, 1.0)
        for lid_jnts in [lid_jnts_upper_L, lid_jnts_upper_R]:
            mid = int(len(lid_jnts_upper_L) / 2)
            up_jnt = Node(lid_jnts[mid])
            dn_jnt = Node(NodeName(up_jnt, desc=up_jnt.get_attr('corr_desc')))
            
            #TODO: add message conn to face mesh to build dist network procedurally
            nd_name = NodeName(
                part='lid',
                desc='updn',
                num='00',
                side=NodeName(up_jnt).side,
                ext='DISTANCE')
            dist_nd = Node.create('distanceBetween', n=nd_name)
            up_jnt.worldMatrix[0] >> dist_nd.inMatrix1
            dn_jnt.worldMatrix[0] >> dist_nd.inMatrix2

        
        # Add Parameter Skin Sliding System to lip/mouth ctrls
        if self.parameter_driver.value:
            
            pds_joints = cds_mouth_joints + cds_lip_joints
            PDS = pds.ParameterDriverSystem(
                joints = pds_joints,
                build_tracer = False,
                ws_root = self.ws_root)
            PDS.build()
            
            crnr_joints = cds_mth_crnr_joints + cds_lip_crnr_joints
            crnr_PDS = pds.ParameterDriverSystem(
                joints = crnr_joints,
                build_tracer = 'worldspace',
                ws_root = self.ws_root)
            crnr_PDS.build()
            
        
        # Insert CDS Curve Driver System to lip/mth ctrls
        if self.curve_driver.value:
            mth_jnts_upper = [jnt for jnt in cds_mouth_joints if 'Upper' in NodeName(jnt).desc]
            mth_jnts_lower = [jnt for jnt in cds_mouth_joints if 'Lower' in NodeName(jnt).desc]
            lip_jnts_upper = [jnt for jnt in cds_lip_joints if 'Upper' in NodeName(jnt).desc]
            lip_jnts_lower = [jnt for jnt in cds_lip_joints if 'Lower' in NodeName(jnt).desc]
            lip_bind_jnts_upper = [jnt for jnt in cds_lip_bind_joints if 'Upper' in NodeName(jnt).desc]
            lip_bind_jnts_lower = [jnt for jnt in cds_lip_bind_joints if 'Lower' in NodeName(jnt).desc]
                        
            mth_jnts_up_L = [jnt for jnt in mth_jnts_upper if NodeName(jnt).side=='L']
            mth_jnts_up_M = [jnt for jnt in mth_jnts_upper if NodeName(jnt).side=='M']
            mth_jnts_up_R = [jnt for jnt in mth_jnts_upper if NodeName(jnt).side=='R']
            mth_jnts_lo_L = [jnt for jnt in mth_jnts_lower if NodeName(jnt).side=='L']
            mth_jnts_lo_M = [jnt for jnt in mth_jnts_lower if NodeName(jnt).side=='M']
            mth_jnts_lo_R = [jnt for jnt in mth_jnts_lower if NodeName(jnt).side=='R']
            mth_crnr_jnt_L = [jnt for jnt in cds_mth_crnr_joints if NodeName(jnt).side=='L']
            mth_crnr_jnt_R = [jnt for jnt in cds_mth_crnr_joints if NodeName(jnt).side=='R']
            
            lip_jnts_up_L = [jnt for jnt in lip_jnts_upper if NodeName(jnt).side=='L']
            lip_jnts_up_M = [jnt for jnt in lip_jnts_upper if NodeName(jnt).side=='M']
            lip_jnts_up_R = [jnt for jnt in lip_jnts_upper if NodeName(jnt).side=='R']
            lip_jnts_lo_L = [jnt for jnt in lip_jnts_lower if NodeName(jnt).side=='L']
            lip_jnts_lo_M = [jnt for jnt in lip_jnts_lower if NodeName(jnt).side=='M']
            lip_jnts_lo_R = [jnt for jnt in lip_jnts_lower if NodeName(jnt).side=='R']
            lip_crnr_jnt_L = [jnt for jnt in cds_lip_crnr_joints if NodeName(jnt).side=='L']
            lip_crnr_jnt_R = [jnt for jnt in cds_lip_crnr_joints if NodeName(jnt).side=='R']

            mth_jnts_up_R.reverse()
            mth_jnts_lo_R.reverse()
            lip_jnts_up_R.reverse()
            lip_jnts_lo_R.reverse()
            
            cds_mth_up_ordered = mth_crnr_jnt_R + mth_jnts_up_R + mth_jnts_up_M + mth_jnts_up_L + mth_crnr_jnt_L
            cds_mth_lo_ordered = mth_crnr_jnt_R + mth_jnts_lo_R + mth_jnts_lo_M + mth_jnts_lo_L + mth_crnr_jnt_L                      
            cds_lip_up_ordered = lip_crnr_jnt_R + lip_jnts_up_R + lip_jnts_up_M + lip_jnts_up_L + lip_crnr_jnt_L
            cds_lip_lo_ordered = lip_crnr_jnt_R + lip_jnts_lo_R + lip_jnts_lo_M + lip_jnts_lo_L + lip_crnr_jnt_L

            mth_crnr_joints = cds_mth_crnr_joints
            mth_wt_mult = 0.65
            lip_crnr_joints = cds_lip_crnr_joints
            lip_wt_mult = 1.0
       
            # Build upper/lower mouth joints CDS
            mth_conn_data = [
                mth_crnr_joints,
                mth_wt_mult,
                [lip_bind_jnts_upper, cds_mth_up_ordered],
                [lip_bind_jnts_lower, cds_mth_lo_ordered]
            ]

            crv_crnr_jnts = mth_conn_data[0]
            mult_value = mth_conn_data[1]
            joints_data = mth_conn_data[2:]

            
            for bind_jnts, build_jnts in joints_data:
                CDS = cds.CurveFollicleDriverSystem(
                    joints = build_jnts,
                    curve_crnr_joints = crv_crnr_jnts,
                    curve_bind_joints = bind_jnts,
                    mid_cv_weight_mult = mult_value,
                    ws_root = self.ws_root
                    )
                    
                CDS.build()
            
            # Build upper/lower lip joints CDS
            lip_conn_data = [
                lip_crnr_joints,
                lip_wt_mult,
                [lip_bind_jnts_upper, cds_lip_up_ordered],
                [lip_bind_jnts_lower, cds_lip_lo_ordered]
            ]

            crv_crnr_jnts = lip_conn_data[0]
            mult_value = lip_conn_data[1]
            joints_data = lip_conn_data[2:]

            for bind_jnts, build_jnts in joints_data:
                CDS = cds.CurveFollicleDriverSystem(
                    joints = build_jnts,
                    curve_crnr_joints = crv_crnr_jnts,
                    curve_bind_joints = bind_jnts,
                    mid_cv_weight_mult = mult_value,
                    ws_root = self.ws_root
                    )
                    
                CDS.build()
        
        # parent lip tip joints to lip joints
        # TODO: setup sticky lips
        for tipjnt in lip_tip_joints: 
            tipdesc = NodeName(tipjnt).desc
            lipjnt = NodeName(tipjnt, desc=tipdesc.replace('Tip',''))
            tipjnt.set_parent(lipjnt)



    def get_blink_attr(self, side):
        """Returns the blink attribute. Create a new one if not exists."""
        name = 'blink_{}'.format(side)
        limb_root = self.limb_root.value
        if limb_root.shape.has_attr(name):
            return limb_root.shape.attr(name)
        return self.add_limb_attr(
            'float', name=name, as_pose=True,
            keyable=True, minValue=0, maxValue=1, defaultValue=0)


    def get_bend_attr(self, side):
        """Returns the bend attribute. Create a new one if not exists."""
        name = 'blinkline_bend_{}'.format(side)
        limb_root = self.limb_root.value
        if limb_root.shape.has_attr(name):
            return limb_root.shape.attr(name)
        return self.add_limb_attr(
            'float', name=name, as_pose=True,
            keyable=True, minValue=-1, maxValue=1, defaultValue=0)



def insert_jaw_offset_node(base_node, align_node=None):
    """TODO doc"""
    base_node = Node(base_node)

    name = NodeName(base_node, ext='JAWPARENTOFFSET')
    parent_offset = Node.create(
        'transform', name=name, parent=base_node.get_parent())
    name = name.replace_ext('JAWOFFSET')
    offset = Node.create('transform', name=name, parent=parent_offset)
    if align_node:
        parent_offset.align(align_node)

    base_node.set_parent(offset)
    return parent_offset, offset

def xform_sum_connect(src_nodes, des_node, channels=None):
    """TODO doc"""
    if not isinstance(src_nodes, (list, tuple)):
        src_nodes = [src_nodes]
    if not channels:
        channels = ['translate','rotate']
    
    sum_node=None
    for i,src_node in enumerate(src_nodes):
        for ch in channels:
            sum_node = NodeName(des_node, ext=ch.upper()+'SUM')
            if not cmds.objExists(sum_node):
                cmds.createNode('plusMinusAverage', n=sum_node)
            
            # connect src channels
            for ax in 'XYZ':
                cmds.connectAttr(
                    "{0}.{1}{2}".format(src_node, ch, ax),
                    '{0}.input3D[{1}].input3D{2}'.format(sum_node, i, ax.lower()) )
                
    # connect des channels
    for ch in channels:
        for ax in 'XYZ':
            sum_node = NodeName(des_node, ext=ch.upper()+'SUM')
            cmds.connectAttr(
                "{0}.output3D{1}".format(sum_node, ax.lower()),
                "{0}.{1}{2}".format(des_node, ch, ax) )
    
    return sum_node

        
