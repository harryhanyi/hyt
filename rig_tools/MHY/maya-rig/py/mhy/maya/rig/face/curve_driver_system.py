import maya.cmds as cmds
import math
from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.constants as const
import mhy.maya.maya_math as mmath
import mhy.maya.rig.utils as utils
import mhy.maya.rig.joint_utils as jutil


class CurveOnSurfaceDriverSystem(object):
    """
    TODO doc
    """

    def __init__(self, tracers, param_surface, driver_curve, ctrl_num=3):
        """TODO doc"""
        self.param_surface = Node(param_surface).get_shapes()[0]
        self.ctrl_num = ctrl_num
        self.ws_node = const.WS_NODE

        # get origin uv
        self.tracers = [Node(t) for t in tracers]
        self.tracer_uv_pairs = []
        for tracer in tracers:
            self.tracer_uv_pairs.append((tracer.originU.value, tracer.originV))

        # get or create the driver curve
        if not cmds.objExists(driver_curve):
            self.driver_curve = Node.create(
                'nurbsCurve',
                self.param_surface,
                self.tracer_uv_pairs,
                name=self.driver_curve)
        else:
            self.driver_curve = Node(driver_curve).get_shapes()[0]

    def build(self):
        """TODO doc"""
        # Insert curve driver to tracer network
        for tracer in self.tracers:
            # create nodes
            poci = Node.create(
                'pointOnCurveInfo', name=NodeName(tracer, ext='poci'))
            pma_sub = Node.create(
                'plusMinusAverage', name=NodeName(tracer, ext='subtract'))
            pma_sub.operation.value = 2
            pma_sum = Node.create(
                'plusMinusAverage', name=NodeName(tracer, ext='sum'))

            # attach poci to driver curve
            self.driver_curve.worldSpace[0] >> poci.inputCurve

            # set poci parameter
            param = self.driver_curve.closest_param(tracer)
            poci.set_attr('parameter', param)

            # connect substract
            for ch in 'XY':
                src_plug = poci.attr('parameter' + ch)
                des_plug0 = pma_sub.attr('input2D[0].input2D' + ch.lower())
                des_plug1 = pma_sub.attr('input2D[1].input2D' + ch.lower())
                src_plug >> des_plug0
                des_plug1.value = des_plug0.value

            # connect summary
            for ch in 'XY':
                src_plug0 = tracer.attr('translate' + ch)
                src_plug1 = pma_sub.attr('output2D' + ch.lower())
                des_plug0 = pma_sum.attr('input2D[0].input2D' + ch.lower())
                des_plug1 = pma_sum.attr('input2D[1].input2D' + ch.lower())
                src_plug0 >> des_plug0
                src_plug1 >> des_plug1

            # force connect sum node to flc
            flc = Node(NodeName(tracer, ext='flc'))
            for src, dst in zip('xy', 'UV'):
                pma_sum.attr('output2D' + src) >> flc.attr('parameter' + dst)

        return self.driver_curve


class CurveFollicleDriverSystem():
    """
    TODO doc
    """

    def __init__(
            self,
            joints,
            curve_crnr_joints,
            
            curve_bind_joints=None,
            driver_curve=None,
            mid_cv_weight_mult=None,
            ws_root=None,
            root_joint=None ):
        """TODO doc"""
        
        if not mid_cv_weight_mult:
            mid_cv_weight_mult=1.0
        
        if not ws_root:
            ws_root = const.WS_NODE
            
        if not root_joint:
            root_joint = jutil.get_joints_in_category('face_root')[0]

        self.side = 'M'
        self.joints = [Node(joint) for joint in joints]
        self.mid_cv_weight_mult = mid_cv_weight_mult
        self.ws_root = ws_root
        self.face_root_jnt = Node(root_joint)
        self.flc_attr = 'flc'
        self.driver_attr = 'flc_driver'
        self.parameter_attr = 'parameter'
        self.curve_crnr_joints = curve_crnr_joints
        self.driver_blend_curve=''
        self.curve_bind_joints=None
        
        if driver_curve:
            self.driver_curve = driver_curve
        else:
            self.driver_curve = NodeName(
                joints[1], part='cornerDriver', num='00', side=self.side, ext='CURVE')
                
        if curve_bind_joints:
            self.curve_bind_joints = [Node(joint) for joint in curve_bind_joints]
                
        self.curve_bind_scls = NodeName(self.driver_curve, ext='SKINCLUSTER')
        
        anchor_jnt_name = NodeName(self.face_root_jnt, part='cds', desc='anchor', ext='CRVJNT')
        if cmds.objExists(anchor_jnt_name):
            self.curve_anchor_joint = Node(anchor_jnt_name)
        else:
            self.curve_anchor_joint = self.face_root_jnt.duplicate(
                parentOnly=True, name=anchor_jnt_name)[0]
                
            # remove categories on anchor joint
            cats = jutil.get_category(self.face_root_jnt)
            for cat in cats:
                jutil.remove_category(self.curve_anchor_joint, cat)
                
        # create curve locators and get position
        self.locator_position=[]
        self.curve_locators=[]
        for jnt in self.joints:
            # create curve locator
            loc_name = NodeName(jnt, ext='LOCATOR')
            if cmds.objExists(loc_name):
                itr = NodeName(loc_name).num
                loc_name = NodeName(loc_name, num=itr)
            crv_loc = Node(cmds.spaceLocator(name=loc_name)[0])
            
            # position curve locator, get ws position
            crv_loc.parent_align(jnt)
            loc_position = crv_loc.get_translation(space='world')
            
            # add driver attribute and clean up
            if not jnt.has_attr(self.driver_attr):
                jnt.add_attr('string', name=self.driver_attr)
            attr = jnt.attr(self.driver_attr)
            attr.locked = False
            attr.value = crv_loc
            attr.locked = True
            
            crv_loc.set_parent(self.get_system_node())
            crv_loc.set_scale((0.05, 0.05, 0.05))
            
            self.curve_locators.append(crv_loc)
            self.locator_position.append(loc_position)
        
        
    def build(self):
        # create driver curve
        if not cmds.objExists(self.driver_curve):
            self.driver_curve = Node.create(
                    'nurbsCurve',
                    self.locator_position,
                    name=self.driver_curve )
              
            # get driver curve shape and rebuild curve
            self.driver_curve_shape = Node(self.driver_curve).get_shapes()[0]
            self.driver_curve_shape.rebuild(
                ch=False,
                replaceOriginal=True,
                rebuildType=0, endKnots=1,
                keepRange=0, spans=9 )      # 4 to 5 to 9
        
            self.driver_curve.set_parent(self.get_system_node())

        # connect curve locators to the driver curve
        # setup driver
        # bind driver curve to corner joints
        # setup driver curve blend
        self.curve_locators_pin()
        self.locators_flcs_connect()
        self.curve_joints_bind()
        self.driver_curve_blend()
        
        if self.curve_bind_joints:
            self.blend_curve_bind()
        

    
    def curve_locators_pin(self):
        crv_locators = self.curve_locators

        # create poci node for each loctor
        for loc in crv_locators:
            poci = Node.create(
                'pointOnCurveInfo',
                name=NodeName(loc, ext='poci')
                )
            poci.set_attr('isHistoricallyInteresting', 0)
            self.driver_curve_shape.worldSpace[0] >> poci.inputCurve
    
            # set poci parameter and connect to curve locator
            param = self.driver_curve_shape.closest_param(loc)
            poci.set_attr('parameter', param)
            poci.position >> loc.translate
    
    
    def locators_flcs_connect(self):
        driven_jnts = [jnt for jnt in self.joints if 'Crnr' not in NodeName(jnt).desc]
        
        for jnt in driven_jnts:
            flc = Node(jnt.get_attr(self.flc_attr))
            loc = Node(jnt.get_attr(self.driver_attr))
            param_patch = Node(jnt.get_attr(self.parameter_attr))
            param_shape = param_patch.get_shapes()[0]
            
            cpos = Node.create(
                'closestPointOnSurface',
                name=NodeName(jnt, ext='cpos') )
            param_shape.worldSpace[0] >> cpos.inputSurface
            loc.translate >> cpos.inPosition
            
            loc_u = cpos.get_attr('parameterU')
            loc_v = cpos.get_attr('parameterV')
            flc_u = flc.get_attr('parameterU')
            flc_v = flc.get_attr('parameterV')
            offset_u = loc_u - flc_u
            offset_v = loc_v - flc_v
            
            adl_u = Node.create(
                'addDoubleLinear',
                name=NodeName(loc, ext='adlU'))
            adl_v = Node.create(
                'addDoubleLinear',
                name=NodeName(loc, ext='adlV'))
                
            cpos.parameterU >> adl_u.input1
            adl_u.set_attr('input2', offset_u)
            cpos.parameterV >> adl_v.input1
            adl_v.set_attr('input2', offset_v)
            
            adl_u.output >> flc.parameterU
            adl_v.output >> flc.parameterV
            
    
    def curve_joints_bind(self):
        """ TODO doc """
        ctrl_crv = self.driver_curve
        crv_shape = self.driver_curve_shape
        anchor_jnt = self.curve_anchor_joint
        crv_bind_jnts = self.curve_crnr_joints
        anchor_jnt.set_parent(self.get_system_node())

        # bind curve to face root joint
        scls_name = self.curve_bind_scls
        crv_scls = Node.create(
            'skinCluster',
            anchor_jnt,
            crv_shape,
            toSelectedBones=True,
            name=scls_name )
        
        crnr_jnt_dups=[]
        for jnt in crv_bind_jnts:
            bnd_jnt_name = NodeName(jnt, ext='CRVJNT')
            
            if cmds.objExists(bnd_jnt_name):
                bnd_jnt = Node(bnd_jnt_name)
            else:
                bnd_jnt = jnt.duplicate(radius=0.3, parentOnly=True, name=bnd_jnt_name)[0]
                flc = Node(jnt.get_attr('flc'))
                for ax in 'XYZ':
                    flc.attr('outTranslate'+ax) >> bnd_jnt.attr('translate'+ax)
                    flc.attr('outRotate'+ax) >> bnd_jnt.attr('rotate'+ax)
                bnd_jnt.set_parent(self.get_system_node())
                
            crv_scls.add_influence(bnd_jnt)
            crnr_jnt_dups.append(bnd_jnt)
        
        # set weights
        cv_num = ctrl_crv.get_attr('spans') + ctrl_crv.get_attr('degree')
        mid_cv = math.floor(cv_num/2)
        base_token = 1.0/float(mid_cv-1)
        
        pre_wt_ls=[]
        for n in list(range(2, mid_cv)):
            base_wt = base_token * n
            interp_wt = mmath.curve_interp(base_wt)
            pre_wt_ls.append(interp_wt)

        wt_list = pre_wt_ls
        wt_list.insert(0, wt_list[0]*1.333)
        wt_list.insert(0, 1.0)
        wt_list_L = wt_list.copy()
        wt_list_L.reverse()
        wt_list_R = wt_list


        # get cv index list for L/R
        cv_index_R = list(range(0, mid_cv))
        cv_index_L = list(range(mid_cv, cv_num))
        crnr_jnt_L = [jnt for jnt in crnr_jnt_dups if NodeName(jnt).side=='L'][0]
        crnr_jnt_R = [jnt for jnt in crnr_jnt_dups if NodeName(jnt).side=='R'][0]

        set_wt_data = {
            crnr_jnt_L : [ cv_index_L, wt_list_L ],
            crnr_jnt_R : [ cv_index_R, wt_list_R ]
        }

        for inf, wt_data_ls in set_wt_data.items():
            for index,weight in zip(wt_data_ls[0], wt_data_ls[1]):
                cmds.skinPercent(
                        crv_scls,
                        '{}.cv[{}]'.format(crv_shape, index),
                        transformValue=[(inf, weight)] )

        self.curve_bind_scls = crv_scls
    
    
    def driver_curve_blend(self):
        """
        1. The blend will happen in front of the deformation chain.
        2. Local curve controls can be added to the blend target curve
        """
        base_crv = self.driver_curve
        base_crv_shape = self.driver_curve_shape
        bs_node_name = NodeName(base_crv, ext='BLENDSHAPE')
        
        # duplicate blend target curve
        target_crv_name = NodeName(base_crv, ext='TARGET')
        target_crv = Node(base_crv.duplicate(name=target_crv_name)[0])
        target_crv.set_parent(self.get_system_node())
        self.driver_blend_curve = target_crv
        
        # create blend shape
        bs_node = Node.create(
            'blendShape',
            target_crv,
            base_crv,
            origin='local',
            frontOfChain=True,
            weight=[0, 1.0],
            name=bs_node_name )
            
        return(bs_node.attr(target_crv.name))
        
        
    def blend_curve_bind(self):
        target_crv = self.driver_blend_curve
        target_crv_shape = target_crv.get_shapes()[0]
        crv_bind_jnts = self.curve_bind_joints
        anchor_jnt = self.curve_anchor_joint
        wt_mult = self.mid_cv_weight_mult
        
        crv_bind_jnts_dup=[]
        # duplicate joints
        for jnt in crv_bind_jnts:
            bnd_jnt_name = NodeName(jnt, ext='CRVJNT')
            
            if cmds.objExists(bnd_jnt_name):
                bnd_jnt = Node(bnd_jnt_name)
            else:
                bnd_jnt = jnt.duplicate(radius=0.3, parentOnly=True, name=bnd_jnt_name)[0]

            jnt_trans_name = NodeName(bnd_jnt, ext='TRANSFORM')
            if cmds.objExists(jnt_trans_name):
                bnd_jnt_trans = Node(jnt_trans_name)
            else:
                bnd_jnt_trans = Node.create('transform', name=jnt_trans_name)
                bnd_jnt_trans.align(bnd_jnt)
                bnd_jnt_trans.set_parent(self.get_system_node())
                bnd_jnt.set_parent(bnd_jnt_trans)
                
            crv_bind_jnts_dup.append(bnd_jnt)

        # bind blend target curve
        crv_scls_name = NodeName(target_crv, ext='BLENDSCLS')
        crv_scls = Node.create(
            'skinCluster',
            anchor_jnt,
            target_crv,
            toSelectedBones=True,
            name=crv_scls_name )
            
        for jnt in crv_bind_jnts_dup:
            crv_scls.add_influence(jnt)
            
        # set curve index pair - 
        # currently hard coded for 9 spans 11 cvs
        # TODO: need procedural
        crv_index_pairs = [
            [9, 8, 7],
            [6, 5],
            [4, 3, 2]
        ]

        # set weights
        for inf, ind_pair in zip(crv_bind_jnts_dup, crv_index_pairs):
            for cv_ind in ind_pair:
                cmds.skinPercent(
                    crv_scls,
                    '{}.cv[{}]'.format(target_crv_shape, cv_ind),
                    transformValue=[(inf, 1.0 * wt_mult)] )
                    
        # set weights for index 1 and 10
        # TODO: need to be procedural
        wt_data = {
            crv_bind_jnts_dup[0] : [(10, 0.35), (7, 0.5)],
            crv_bind_jnts_dup[-1] : [(1, 0.35), (4, 0.5)]
        }
        for inf, data in wt_data.items():
            for index, wt in data:
                cmds.skinPercent(
                    crv_scls,
                    '{}.cv[{}]'.format(target_crv_shape, index),
                    transformValue=[(inf, wt * wt_mult)] )

        # connect ctrl joints to bind joints
        for driver, driven in zip(crv_bind_jnts, crv_bind_jnts_dup):
            '''
            # direct connect crv jnt to dup crv jnt
            driver_ctrl = jutil.get_ctrl(driver)
            src_node = driven.attr('translateX').source_node
            if not driver==src_node:
                # cns will cause double trans
                for ax in 'XYZ':
                    driver_ctrl.attr('translate'+ax) >> driven.attr('translate'+ax)
                    driver_ctrl.attr('rotate'+ax) >> driven.attr('rotate'+ax)
            '''
            # direct connect with multiple drivers,
            #   so the driver ctrl can be an inf in other poses.
            driver_ctrl = Node(jutil.get_ctrl(driver))
            driver_pose = driver_ctrl.pose_node
            driver_offset = driver_ctrl.offset_node
            drivers = [driver_ctrl, driver_pose, driver_offset]
            
            for attr in ['translate', 'rotate']:
                driven_attr = '{}.{}'.format(driven, attr)
                driver_attrs=[]
                for node in drivers:
                    driver_attrs.append('{}.{}'.format(node, attr))
                    
                node_name = NodeName(driver_ctrl)
                sum_name = NodeName(
                    driver_ctrl,
                    part = node_name.desc,
                    desc = '{}Sum'.format(attr),
                    num = node_name.num,
                    side = node_name.side,
                    ext = 'pma'
                    )
                utils.create_sum(
                    input_attrs = driver_attrs,
                    output_attr = driven_attr,
                    dimension = 3,
                    name= sum_name
                    )
                
            else:
                continue


    def get_system_node(self, worldspace=True):
        """Returns the system node. Create a new one if not exists."""

        sys_parent_name = 'CurveDriverSystem_ws'
        root_node = self.ws_root
        if not worldspace:
            sys_parent_name = 'CurveDriverSystem'
            root_node = self.limb_root
            
        grp_name = '{0}_{1}'.format(sys_parent_name, self.side)

        if not cmds.objExists(sys_parent_name):
            parent_node = Node.create(
                'transform', parent=root_node, name=sys_parent_name)
            parent_node.lock(attrs='trs')
            parent_node.v.value = False
            
        if not cmds.objExists(grp_name):
            system_node = Node.create(
                'transform', parent=sys_parent_name, name=grp_name)
            system_node.lock(attrs='trs')
        
        else:
            system_node = Node(grp_name)
            
        return system_node 
        
    
    
