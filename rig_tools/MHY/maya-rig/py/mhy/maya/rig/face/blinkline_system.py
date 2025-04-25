from maya import cmds

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath

import mhy.maya.rig.face.tracer as tracer
import mhy.maya.rig.constants as const
import mhy.maya.rig.utils as utils
import mhy.maya.rig.joint_utils as jutil


class BlinklineSystem():
    """
    Lo-res blinkline sys will build both side of the eyelid.
        - Input eyelids base joints include left and right side.

    Parameter driven blinkline only builds one side of eyelids at a time.
        - run blinkline sys twice for left and right at the build time.
        - needs to be after hi face limb build.

    TODO:
    Lo-res methods are obsoleted, will be updated to be the same as the param-driven blinkline.
    """

    def __init__(
            self,
            #side=NodeName.SIDE_M,
            ctrl_limb=None,
            blink_attr=None,
            bend_attr=None,
            ws_root=const.WS_NODE):
            #io_follow_mult=None,
            #ud_follow_mult=None):

        """TODO doc"""
        self.blink_attr = blink_attr
        self.bend_attr = bend_attr

        self.side = str(blink_attr).split('_')[-1]
        self.param_patch = None
        self.param_shape = None
        self.eye_joints = None      # old method
        self.lid_base_joints = None     # old method

        # get joints - new method
        bind_joints = jutil.get_joints_in_category('bind')
        lid_joints = jutil.get_joints_in_category('lid', joints=bind_joints)

        self.lid_joints = [j for j in lid_joints if NodeName(j).side == self.side]
        if not self.lid_joints:
            raise RuntimeError('No lid joints found.')
        else:
            self.param_patch = Node(self.lid_joints[0].parameterPatch.value)
            self.param_shape = self.param_patch.get_shapes()[0]

        self.ws_root = Node(ws_root)

        # TODO: need merge the original to the parameter method
        self.lid_top_joints = [j for j in self.lid_joints if 'Upper' in j.name]
        self.lid_bot_joints = [j for j in self.lid_joints if 'Lower' in j.name]
        self.lid_cnr_joints = [j for j in self.lid_joints
                               if 'Crnr' in j.name or 'Corner' in j.name]
        if len(self.lid_cnr_joints) != 2:
            raise RuntimeError('Input corner joints can only be two.')

        self.blinkline_handledles = []
        self.blinkline_follicles = []
        self.lid_top_flcs = []
        self.lid_bot_flcs = []

        self.lid_corner_distance = None
        self.proximate_eye_ratio = None
        self.lid_corner_curves = []
        self.ud_lid_mid_joints = []
        self.uplid_io_key_joints = []
        self.top_bot_curve_jnts_dict = {}
        self.lid_jnt_blink_rt_jnt_ik_dict = {}
        self.lid_jnt_cns_loc_pair = {}
        self.lid_blink_loc_triplet = {}

    def get_system_node(self):
        """Returns the system node. Create a new one if not exists."""
        #name = 'blinklineSystem_' + self.side
        name = 'blinklineSystem_'
        if not cmds.objExists(name):
            system_node = Node.create(
                'transform', parent=self.ws_root, name=name)
            system_node.lock(attrs='trs')
            system_node.v.value = False
        else:
            system_node = Node(name)
        return system_node


    def build(self):
        """TODO doc"""
        if self.param_patch:
            self.create_param_blinkline_handles()
            self.setup_param_eye_blink()
            self.setup_param_blinkline_bend()
        else:
            self.insert_blink_nodes()
            self.get_lid_blinkline_data()
            self.setup_eye_close()
            self.setup_in_out_auto_offset()
            self.setup_up_down_auto_offset()
            self.distance_driven_ratio_offset(offset_channels=['ty'])

    def create_param_blinkline_handles(self):
        """TODO doc"""
        # create upper/lower eyelid ref curves
        lid_curves = []
        for top_jnt in self.lid_top_joints:
            bot_jnt = Node(top_jnt.name.replace('Upper', 'Lower'))
            if bot_jnt not in self.lid_bot_joints:
                raise RuntimeError(
                    'Relative bottom lid joint {} not in the list.'.format(
                        bot_jnt))

            tracer_uv_points = []
            for jnt in (top_jnt, bot_jnt):
                pos = jnt.get_translation(space='world')
                tracer_uv_points.append(self.param_shape.closest_param(pos))

            name = NodeName(top_jnt, ext='CRV')
            lid_crv = Node.create(
                'nurbsCurve', self.param_patch, tracer_uv_points,
                name=name, degree=1, underworld=True)
            lid_crv.rebuild(
                name=name,
                rebuildType=0, endKnots=1, keepEndPoints=True, keepRange=0,
                keepControlPoints=False, keepTangents=False,
                spans=4, degree=3)

            name = NodeName(top_jnt, ext='DUPCRV')
            dup_lid_crv = lid_crv.duplicate_curve(
                name=name, ch=False)[0]
            lid_crv.get_parent().delete()
            lid_curves.append(dup_lid_crv)

        tracer_uv_points = []
        for jnt in self.lid_cnr_joints:
            pos = jnt.get_translation(space='world')
            tracer_uv_points.append(self.param_shape.closest_param(pos))

        # create corner curve
        name = NodeName(self.lid_cnr_joints[0], ext='CRV')
        cnr_crv = Node.create(
            'nurbsCurve', self.param_patch, tracer_uv_points,
            name=name, degree=1, underworld=True)
        cnr_crv.rebuild(
            rebuildType=0, endKnots=1, keepEndPoints=True, keepRange=0,
            keepControlPoints=False, keepTangents=False,
            spans=4, degree=3)
        name = NodeName(self.lid_cnr_joints[0], ext='DUPCRV')
        dup_cnr_crv = cnr_crv.duplicate_curve(
            name=name, ch=False)[0]
        cnr_crv.get_parent().delete()

        for dup_lid_crv in lid_curves:
            param = intersect_points_on_two_curves(dup_lid_crv, dup_cnr_crv)[1]
            position = dup_cnr_crv.point_at_param(param)
            u, v = self.param_shape.closest_param(position)

            # blinkline handles should not be in any pose
            name = NodeName(dup_lid_crv, desc='blinkline', ext='FLCTRANSFORM')
            flc = Node.create('follicle', self.param_patch, name=name)
            flc.name = name.replace_ext('FLC')
            flc_xform = flc.get_parent()
            flc_xform.set_parent(self.get_system_node())

            blinkline_handle = name.replace_ext('HANDLE')
            TRACER = tracer.ParameterTracer(
                self.param_patch, name=blinkline_handle, shape_color=9)
            #blinkline_handle = TRACER.create()
            TRACER.create()     #

            blinkline_handle = Node(blinkline_handle)
            follicle_handle_attach(blinkline_handle, flc, uv=(u, v))
            self.blinkline_handledles.append(blinkline_handle)
            self.blinkline_follicles.append(flc)
            cmds.delete(dup_lid_crv.get_parent())

        cmds.delete(dup_cnr_crv.get_parent())

    def setup_param_eye_blink(self):
        """Creates blink function along the parameter patch.
        Should be built after the hi face limb.
        """
        self.lid_top_flcs = [Node(j.name.replace('JNT', 'FLC'))
                             for j in self.lid_top_joints]
        self.lid_bot_flcs = [Node(j.name.replace('JNT', 'FLC'))
                             for j in self.lid_bot_joints]

        #blink_attr = self.get_blink_attr(self.side)
        blink_attr = self.blink_attr

        for blink_flc, t_flc, b_flc in zip(
                self.blinkline_follicles,
                self.lid_top_flcs,
                self.lid_bot_flcs):

            top_bot_pair_blend_nodes = [b_flc]

            for flc in (t_flc, b_flc):
                blnd_flc = Node.create(
                    'follicle',
                    self.param_patch,
                    name=NodeName(flc, ext='BLFLCTRANSFORM'))
                blink_flc.name = NodeName(flc, ext='BLFLC')
                #blnd_flc_xform = blink_flc.get_parent()
                blnd_flc_xform = blnd_flc.get_parent()

                blend_node = pair_blend_transforms(
                    xform1=flc,
                    xform2=blink_flc,
                    driven=blnd_flc,
                    desc='blink',
                    channels=('parameter', 'parameter'),
                    axis='UV')
                top_bot_pair_blend_nodes.append(blend_node)

                # force connect to transport
                blink_attr >> blend_node.weight
                transport_node = Node(NodeName(flc, ext='TRANSPORT'))

                for ch in ('translate', 'rotate'):
                    for ax in 'XYZ':
                        attr = ch + ax
                        blnd_flc_xform.attr(attr) >> transport_node.attr(attr)

                # cleanup
                blnd_flc_xform.set_parent(self.get_system_node())

    def setup_param_blinkline_bend(self):
        """TODO doc"""
        if not self.blinkline_follicles:
            raise RuntimeError(
                'Blinkline follicle list self.blinkline_follicles is empty.')
        if not self.lid_top_flcs:
            raise RuntimeError(
                'Blinkline follicle list self.lid_top_flcs is empty.')
        if not self.lid_bot_flcs:
            raise RuntimeError(
                'Blinkline follicle list self.lid_bot_flcs is empty.')

        bend_attr = self.bend_attr

        for blink_handle, blink_flc, t_flc, b_flc in zip(
            self.blinkline_handledles,
            self.blinkline_follicles,
            self.lid_top_flcs,
            self.lid_bot_flcs):

            name = NodeName(blink_flc, desc='blinklineBend', ext='CND')
            cnd = Node.create('condition', name=name)
            t_desc = 'blinklineBendUp'
            b_desc = 'blinklineBendDn'
            t_uv = t_flc.parameter
            b_uv = b_flc.parameter

            pair_blend_nodes = []
            for description in (t_desc, b_desc):
                blend_node = pair_blend_transforms(
                    xform1=blink_handle,
                    desc=description,
                    channels=('parameter', 'parameter'),
                    axis='UV')
                pair_blend_nodes.append(blend_node)

            # set and lock xform2
            for blend_node, uv in zip(pair_blend_nodes, (t_uv, b_uv)):
                blend_node.inTranslateX2.value = uv[0]
                blend_node.inTranslateX2.locked = True
                blend_node.inTranslateY2.value = uv[1]
                blend_node.inTranslateY2.locked = True

            # set driver condition for bend
            bend_attr >> cnd.firstTerm
            cnd.operation.value = 2      # set greater than

            for blend_node in pair_blend_nodes:
                driver_driven_pair_value_list = []
                driven_attr = blend_node.weight
                kw=''     #
                if t_desc in blend_node.name:
                    kw = 'True'
                    driver_driven_pair_value_list = ((0.0, 0.0), (1.0, 1.4))
                if b_desc in blend_node.name:
                    kw = 'False'
                    driver_driven_pair_value_list = ((-1.0, 1.1), (0.0, 0.0))

                blend_node.outTranslateX >> cnd.attr('colorIf{}R'.format(kw))
                blend_node.outTranslateY >> cnd.attr('colorIf{}G'.format(kw))

                utils.set_driven_keys(
                    bend_attr, driven_attr,
                    driver_driven_pair_value_list,
                    in_tangent_type='linear', out_tangent_type='linear',
                    pre_inf='constant', post_inf='constant')

            cnd.outColorR >> blink_flc.parameterU
            cnd.outColorG >> blink_flc.parameterV


    # obsolete under this line
    def insert_blink_nodes(self):
        """TODO doc"""
        for eye_jnt, lid_base_jnt in zip(self.eye_joints, self.lid_base_joints):
            self.lid_joints = lid_base_jnt.get_hierarchy(skip_self=True)
            lid_top_bot_joints = [j for j in self.lid_joints
                                  if 'Corner' not in j.name]

            # insert blink nodes and ik ctrl joints
            for lid_jnt in lid_top_bot_joints:
                rot_order = lid_base_jnt.rotateOrder.value
                lid_ctrl = Node(NodeName(lid_jnt, ext='FKCTRL'))

                name = NodeName(lid_jnt, ext='BLINKROOTJNT')
                blink_root_jnt = Node.create('joint', radius=0.2, name=name)
                blink_root_jnt.set_rotate_order(rot_order)
                blink_end_jnt = blink_root_jnt.duplicate(
                    parentOnly=True,
                    name=name.replace_ext('BLINKENDJNT') )[0]
                blink_end_jnt.set_parent(blink_root_jnt)
                blink_end_jnt.tz.value = mmath.distance(lid_base_jnt, lid_jnt) / 2
                blink_root_jnt.align(lid_base_jnt, skipRotate=True)

                ikh, eff = cmds.ikHandle(
                    startJoint=blink_root_jnt,
                    endEffector=blink_end_jnt,
                    solver='ikSCsolver',
                    name=name.replace_ext('BLIINKIKHAN'))
                ikh = Node(ikh)

                lid_blink_node = Node.create(
                    'LSCtrl',
                    name=NodeName(lid_jnt, ext='BLINK'),
                    xform=lid_base_jnt,
                    pos=(0.1, 0.1, 0.1),
                    color=(0, 0, 0),
                    shape='cube',
                    group_exts=['BLINKPLC'])

                lid_blink_node.plc_node.set_parent(lid_ctrl.wts_transport)
                self.lid_jnt_blink_rt_jnt_ik_dict[lid_jnt] = [
                    lid_blink_node, blink_root_jnt, ikh]

                cmds.parent(blink_root_jnt, ikh, self.get_system_node())

        return self.lid_jnt_blink_rt_jnt_ik_dict

    def get_lid_blinkline_data(self):
        """TODO doc"""
        for eye_jnt, lid_base_jnt in zip(self.eye_joints, self.lid_base_joints):
            self.lid_joints = lid_base_jnt.get_hierarchy(skip_self=True)
            self.lid_top_joints = [j for j in self.lid_joints if 'Top' in j]
            self.lid_bot_joints = [j for j in self.lid_joints if 'Bot' in j]
            self.lid_cnr_joints = [j for j in self.lid_joints if 'Corner' in j]

            self.lid_top_joints.sort()
            self.lid_bot_joints.sort()
            self.lid_cnr_joints.sort()

            if len(self.lid_cnr_joints) != 2:
                raise RuntimeError('Input corner joints can only be two.')

            # mid and 1/3 lid joint index
            ind2 = int(len(self.lid_top_joints) / 2)
            ind3 = int(len(self.lid_top_joints) / 3)

            # get lid corner distance
            self.lid_corner_distance = mmath.distance(
                self.lid_cnr_joints[0], self.lid_cnr_joints[1])
            # get proximate eye ratio
            self.proximate_eye_ratio = mmath.distance(eye_jnt, self.lid_top_joints[ind2])
            # get up and down lids mid joints
            self.ud_lid_mid_joints.append(
                (self.lid_top_joints[ind2], self.lid_bot_joints[ind2]))
            # get look in and out lid stretch key joints
            self.uplid_io_key_joints.append(
                (self.lid_top_joints[ind3], self.lid_top_joints[-(ind3 + 1)]))

            # create eye corner to corner curve
            if NodeName(lid_base_jnt).is_left:
                cnr_crv_base = Node.create(
                    'nurbsCurve', self.lid_cnr_joints, degree=1)
            else:
                self.lid_cnr_joints.reverse()
                cnr_crv_base = Node.create(
                    'nurbsCurve', self.lid_cnr_joints, degree=1)

            self.lid_corner_curves.append(cnr_crv_base)

            # create corner line ref surface
            cnr_crv_offset = cmds.offsetCurve(
                cnr_crv_base, range=True, normal=(0, -1, 0),
                distance=5, ch=False)[0]
            cnr_surf = Node(cmds.loft(
                cnr_crv_base, cnr_crv_offset, range=True,
                autoReverse=True, ch=False)[0])
            cnr_surf_shape = cnr_surf.get_shapes()[0]
            cmds.delete(cnr_crv_offset)

            int_surf = Node.create('intersectSurface')
            cnr_surf_shape.worldSpace[0] >> int_surf.inputSurface1
            x_crv = Node.create('nurbsCurve', ((0, 0, 0), (1, 0, 0)), degree=1)
            x_crv_shape = x_crv.get_shapes()[0]
            int_surf.output3dCurve[0] >> x_crv_shape.create

            lid_surface_list = []
            self.top_bot_curve_jnts_dict[eye_jnt] = {}
            for top_jnt, bot_jnt in zip(
                    self.lid_top_joints, self.lid_bot_joints):
                lid_crv_top = Node.create('nurbsCurve', (eye_jnt, top_jnt))
                lid_crv_bot = Node.create('nurbsCurve', (eye_jnt, bot_jnt))
                lid_surf = Node(cmds.loft(
                    lid_crv_top, lid_crv_bot, range=True,
                    autoReverse=True, ch=False)[0])
                cmds.delete(lid_crv_top, lid_crv_bot)

                # calc and create blinkline locators
                lid_surf.worldSpace[0] >> int_surf.inputSurface2
                blink_matrix = Node(x_crv+'.ep[0]').get_matrix(space='world')
                blink_locator = Node.create(
                    'LSCtrl',
                    name=NodeName(top_jnt, part='blinkline', ext='BLINKLOC'),
                    pos=(0.1, 0.1, 0.1),
                    color=(0, 1, 0),
                    shape='triangle',
                    group_exts=['BLINKLOCPLC'])

                blink_locator.plc_node.set_matrix(blink_matrix, space='world')
                norm_cns = blink_locator.plc_node.constrain(
                    'normal', lid_surf, aim=(1, 0, 0))
                cmds.delete(norm_cns)
                blink_locator.plc_node.set_parent(self.get_system_node())
                lid_surface_list.append(lid_surf)

                # get rotate degree data for eye blink
                lid_locator_pair = []
                for lid_jnt in (top_jnt, bot_jnt):
                    lid_locator = Node.create(
                        'LSCtrl',
                        name=NodeName(lid_jnt, ext='LIDLOC'),
                        xform=lid_jnt,
                        scale=[0.1, 0.1, 0.1],
                        color=(0, 0, 0),
                        shape='triangle',
                        group_exts=['LIDLOCPLC'])

                    lid_locator.plc_node.align(
                        blink_locator, skipTranslate=True)
                    lid_locator.plc_node.rz.value = 0
                    lid_locator.plc_node.set_parent(self.get_system_node())
                    self.lid_jnt_cns_loc_pair[lid_jnt] = (lid_locator, blink_locator)
                    lid_locator_pair.append(lid_locator)

                self.lid_blink_loc_triplet[blink_locator] = lid_locator_pair

            cmds.delete(lid_surface_list, cnr_surf, x_crv)

        return self.lid_jnt_cns_loc_pair

    def setup_eye_close(self):
        """TODO doc"""

        for eye_jnt, lid_base_jnt in zip(self.eye_joints, self.lid_base_joints):
            self.lid_joints = lid_base_jnt.get_hierarchy(skip_self=True)
            lid_top_bot_joints = [j for j in self.lid_joints
                                  if 'Corner' not in j.name]
            blink_cns_attr_list = []

            for lid_jnt in lid_top_bot_joints:
                blink_node, root_jnt, ikh = self.lid_jnt_blink_rt_jnt_ik_dict[lid_jnt]
                lid_loc, blink_loc = self.lid_jnt_cns_loc_pair[lid_jnt]
                lid_ctrl = Node(NodeName(lid_jnt, ext='FKCTRL'))

                # setup constraint on ikh
                cns = ikh.constrain('point', lid_loc, blink_loc)
                open_cns_attr = cns.attr(lid_loc.name + 'W0')
                blink_cns_attr = cns.attr(blink_loc.name + 'W1')
                open_cns_attr.value = 1
                blink_cns_attr.value = 0
                for ax in 'xyz':
                    root_jnt.attr('r' + ax) >> blink_node.attr('r' + ax)
                lid_ctrl.plc_node.set_parent(blink_node)

                # reverse driving lid open and blink
                name = blink_cns_attr.short_name.replace('.', '__') + '_REVERSE'
                rvrs = Node.create('reverse', name=name)
                blink_cns_attr >> rvrs.inputX
                rvrs.outputX >> open_cns_attr

                blink_cns_attr_list.append(blink_cns_attr)

            # connect driver attributes blinkL/blinkR
            blink_attr = self.get_blink_attr(NodeName(eye_jnt).side)
            for cns_attr in blink_cns_attr_list:
                blink_attr >> cns_attr

    def setup_in_out_auto_offset(self):
        """TODO doc"""

        for eye_jnt, key_jnts, cnr_curv, top_jnts, cnr_jnts in zip(
                self.eye_joints,
                self.uplid_io_key_joints,
                self.lid_corner_curves,
                self.lid_top_joints,
                self.lid_cnr_joints):

            side = NodeName(eye_jnt).side
            in_key_jnt, out_key_jnt = key_jnts

            mid_pos = cnr_curv.closest_point(eye_jnt)
            end_pos = cmds.xform(
                '{}.ep[1]'.format(cnr_curv),
                query=True, worldSpace=True, translation=True)
            opp = mmath.distance(mid_pos, end_pos)
            hyp = self.proximate_eye_ratio
            degree = mmath.trig_get_angle(
                hypotenuse=hyp, opposite=opp, deg=True)

            in_key_idx = top_jnts.index(in_key_jnt)
            out_key_idx = top_jnts.index(out_key_jnt)
            look_in_jnts = top_jnts[in_key_idx:]
            look_out_jnts = top_jnts[out_key_idx:]

            # add mult attr
            in_out_attr = self.get_system_node().add_attr(
                'float', name='InOut_' + side,
                maxValue=1, minValue=-1, defaultValue=0)

            in_out_mult_attr = self.add_limb_attr(
                'float', name='InOut_' + side + '_Mult',
                minValue=0, maxValue=1, defaultValue=1, keyable=True)
            if self.in_out_follow_mult:
                in_out_mult_attr.value = self.in_out_follow_mult

            # setup mult attr
            mdl = Node.create(
                'multDoubleLinear', name=NodeName(eye_jnt, ext='inOutMult_MDL'))
            in_out_attr >> mdl.input1
            in_out_mult_attr >> mdl.input2
            in_out_driver_attr = mdl.output

            driver_attr = eye_jnt.ry
            driven_attr = in_out_attr
            driver_driven_pair_value_list = (
                (degree, -1.0), (0.0, 0.0), (-degree, 1.0))
            utils.set_driven_keys(
                driver_attr, driven_attr,
                driver_driven_pair_value_list,
                in_tangent_type='linear', out_tangent_type='linear',
                pre_inf='constant', post_inf='constant')

            look_in_value_dict = get_interp_value(
                in_key_jnt, cnr_jnts[-1], driven_nodes=look_in_jnts)
            look_out_value_dict = get_interp_value(
                out_key_jnt, cnr_jnts[0], driven_nodes=look_out_jnts)

            for lid_jnt in top_jnts:
                lid_loc = self.lid_jnt_cns_loc_pair[lid_jnt][0]
                # look in
                try:
                    trans_in = look_in_value_dict[lid_jnt]
                except BaseException:
                    trans_in = 0.02
                # look out
                try:
                    trans_out = look_out_value_dict[lid_jnt]
                except BaseException:
                    trans_out = 0.02

                driver_attr = in_out_driver_attr
                driven_attr = lid_loc.translateX
                driver_driven_pair_value_list = (
                    (-1.0, -trans_in), (0.0, 0.0), (1.0, trans_out))

                utils.set_driven_keys(
                    driver_attr, driven_attr,
                    driver_driven_pair_value_list,
                    in_tangent_type='flat', out_tangent_type='spline',
                    pre_inf='constant', post_inf='constant')

        cmds.delete(self.lid_corner_curves)

    def setup_up_down_auto_offset(self):
        """TODO doc"""

        for eye_jnt, mid_jnts, cnr_jnts, top_jnts, bot_jnts in zip(
                self.eye_joints,
                self.ud_lid_mid_joints,
                self.lid_cnr_joints,
                self.lid_top_joints,
                self.lid_bot_joints):

            side = NodeName(eye_jnt).side

            top_bot_crv = Node.create('nurbsCurve', mid_jnts)
            mid_pos = top_bot_crv.closest_point(eye_jnt)
            opp = mmath.distance(mid_pos, mid_jnts[0])
            hyp = self.proximate_eye_ratio
            degree = mmath.trig_get_angle(
                hypotenuse=hyp, opposite=opp, deg=True)
            cmds.delete(top_bot_crv)

            # add attributes
            up_dn_attr = self.get_system_node().add_attr(
                'float', name='UpDown_' + side,
                maxValue=1, minValue=-1, defaultValue=0)

            up_dn_mult_attr = self.addLimbAttribute(
                'float', name='UpDown_' + side + '_Mult',
                minValue=0, maxValue=1, defaultValue=1, keyable=True)
            if self.up_down_follow_mult:
                up_dn_mult_attr.value = self.up_down_follow_mult

            # setup mult attr
            mdl = Node.create(
                'multDoubleLinear', name=NodeName(eye_jnt, ext='upDnMult_MDL'))
            up_dn_attr >> mdl.input1
            up_dn_mult_attr >> mdl.input2
            up_dn_driver_attr = mdl.output

            driver_attr = eye_jnt.rx
            driven_attr = up_dn_attr
            driver_driven_pair_value_list = (
                (degree, -1.0), (0.0, 0.0), (-degree, 1.0))
            utils.set_driven_keys(
                driver_attr, driven_attr,
                driver_driven_pair_value_list,
                in_tangent_type='linear', out_tangent_type='linear',
                pre_inf='constant', post_inf='constant')

            top_mid_idx = top_jnts.index(mid_jnts[0])
            inner_top_jnts = top_jnts[:top_mid_idx]
            outer_top_jnts = top_jnts[top_mid_idx:]

            inner_top_value_dict = get_interp_value(
                mid_jnts[0], cnr_jnts[0], driven_nodes=inner_top_jnts)
            outer_top_value_dict = get_interp_value(
                mid_jnts[0], cnr_jnts[-1], driven_nodes=outer_top_jnts)

            # setup top lid joints auto falloff
            for lid_jnt in top_jnts:
                lid_loc, blink_loc = self.lid_jnt_cns_loc_pair[lid_jnt]

                # top look up
                try:
                    trans_up = inner_top_value_dict[lid_jnt]
                except BaseException:
                    trans_up = outer_top_value_dict[lid_jnt]

                # bot look down
                top_loc, bot_loc = self.lid_blink_loc_triplet[blink_loc]
                transDn = mmath.distance(top_loc, bot_loc)
                blink_loc_dist = mmath.distance(top_loc, blink_loc)
                up_mult = blink_loc_dist / self.proximate_eye_ratio
                dn_mult = 0.8

                driver_attr = up_dn_driver_attr
                driven_attr = lid_loc.translateY
                driver_driven_pair_value_list = (
                    (-1, -transDn * dn_mult), (0, 0), (1, trans_up * up_mult))

                utils.set_driven_keys(
                    driver_attr, driven_attr,
                    driver_driven_pair_value_list,
                    in_tangent_type='spline', out_tangent_type='spline',
                    pre_inf='linear', post_inf='linear')

            # TODO:
            # setup bot lid joints auto falloff

            # setup blinkline

    def distance_driven_ratio_offset(self, offset_channels=('tx', 'ty', 'tz')):
        """TODO doc"""
        for driven, drivers in self.lid_blink_loc_triplet.items():
            driver01, driver02 = drivers
            name = NodeName(driver01)
            name = NodeName(driver02, part=name.part, ext='dist')
            dist_node = Node.create('distance', name=name)
            driver01.worldMatrix[0] >> dist_node.inMatrix1
            driver02.worldMatrix[0] >> dist_node.inMatrix2
            distance = dist_node.distance.value

            driven_parent = driven.get_parent()
            driven_parent_off = Node.create(
                'transform', name=NodeName(driven, ext='PARENTOFFSET'))
            driven_parent_off.parent_align(driven_parent, keep_new_parent=True)
            driven_parent_off.constrain('point', driver01, driver02)
            driven.set_parent(driven_parent_off)

            # divNode = Node.create(
            #     'multiplyDivide', name=NodeName(dist_node, ext='md'))
            # divNode.operation.value = 2  # divide
            for ch in offset_channels:
                offset = driven.get_attr(ch)
                if offset:
                    ratio = offset / distance
                    mdl = Node.create(
                        'multDoubleLinear',
                        name=NodeName(dist_node, ext='MDL' + ch))
                    dist_node.distance >> mdl.input1
                    mdl.input2.value = ratio
                    mdl.output >> driven.attr(ch)


class CurveBlinklineSystem():
    """
    Auto eyelids blink setup
    """
    
    def __init__(
            self,
            lid_profile_joints,
            eye_corner_joints,
            lid_curve_joints,
            
            profile_curve=None,
            blinkline_curve=None,
            offset_mult=None,
            aim_vector=None,
            up_vector=None,
            world_up_type=None,
            world_up_obj=None,
            ws_root=None,
            limb_root=None,
            root_joint=None ):
        
    
        if not lid_profile_joints:
            raise ValueError('Nothing created, need a list of eyelid joints as input.')
            
        if not eye_corner_joints:
            raise ValueError('Nothing created, need to define eye corner joints.')
        
        self.side = NodeName(lid_profile_joints[0]).side
        
        if not aim_vector:
            aim_vector = (1,0,0)
            #if self.side=='R':
            #    aim_vector = (-1,0,0)
            
        if not up_vector:
            up_vector = (0,1,0)
            
        if not world_up_type:
            world_up_type = 'object'
            
        if not ws_root:
            ws_root = const.WS_NODE
            
        if not limb_root:
            limb_root = const.RIG_ROOT
            
        if not root_joint:
            root_joint = jutil.get_joints_in_category('face_base')[0]
        
        #
        self.lid_profile_joints = [Node(joint) for joint in lid_profile_joints]
        self.eye_corner_joints = [Node(joint) for joint in eye_corner_joints]
        self.base_jnt = Node(self.lid_profile_joints[0]).get_parent()
        self.aim_vector = aim_vector
        self.up_vector = up_vector
        self.world_up_type = world_up_type
        self.world_up_obj = world_up_obj
        self.ws_root = ws_root
        self.limb_root = limb_root
        self.aim_target_attr = 'aimTarget'
        self.face_root_jnt = Node(root_joint)
        self.lid_crv_jnts = lid_curve_joints
        
        if profile_curve:
            self.profile_curve = profile_curve
        else:
            self.profile_curve = NodeName(
                    lid_profile_joints[0], num='00', ext='CURVE'
                )

        if blinkline_curve:
            self.blinkline_curve = blinkline_curve
        else:
            self.blinkline_curve = NodeName(
                    lid_profile_joints[0], num='00', ext='BLINKLINE'
                )
        
        self.curve_bind_scls = NodeName(self.profile_curve, ext='SKINCLUSTER')

    
    def build(self):
        # create world_up_obj and set position
        if not self.world_up_obj:
            base_jnt_pos = self.base_jnt.get_translation(space='world')
            obj_name = NodeName(
                self.lid_profile_joints[0],
                num='00', ext='UPOBJECT'
                )
            self.world_up_obj = Node(cmds.spaceLocator(name=obj_name)[0])
            
        else:
            self.world_up_obj = Node(self.world_up_obj)
        
        self.world_up_obj.set_translation(base_jnt_pos, space='world')
        self.world_up_obj.set_translation((base_jnt_pos[0], base_jnt_pos[1]+10, base_jnt_pos[2]))
        self.world_up_obj.set_parent(self.get_system_node(worldspace=False))

        # create aim targets and get position
        self.aim_target_position=[]
        for profile_jnt in self.lid_profile_joints:
            # get base joint and create aim target
            base_jnt = Node(profile_jnt).get_parent()
            name = NodeName(base_jnt, ext='AIMTARGET')
            aim_target = Node(cmds.spaceLocator(name=name)[0])
            
            # position aim target locator, then get ws position
            pjnt_trans = profile_jnt.get_translation(space='world')
            aim_target.set_translation(pjnt_trans, space='world')
            
            aim_target.set_parent(self.get_system_node())
            aim_target.set_scale((0.1, 0.1, 0.1))
            aim_target_position = aim_target.get_translation(space='world')
            
            self.aim_target_position.append(aim_target_position)
            
            # tag base joint with aim target
            if not base_jnt.has_attr(self.aim_target_attr):
                base_jnt.add_attr('string', name=self.aim_target_attr)
            attr = base_jnt.attr(self.aim_target_attr)
            attr.locked = False
            attr.value = aim_target
            attr.locked = True
        
        # create eye corner util curve
        corner_positions=[]
        for jnt in self.eye_corner_joints:
            position = mmath.get_position(jnt)
            corner_positions.append(position)
        crnrs_crv = Node.create('nurbsCurve', corner_positions)
        crnrs_crv_shape = crnrs_crv.get_shapes()[0]
        blinkline_aim_loc = Node(cmds.spaceLocator()[0])
        
        # attach blinkline aim locator onto corner util curve with poci
        crnrs_poci = Node.create('pointOnCurveInfo')
        crnrs_crv_shape.worldSpace[0] >> crnrs_poci.inputCurve
        crnrs_poci.position >> blinkline_aim_loc.translate
        
        # create corners surface from 3-points for intersection
        crnr_in_jnt,crnr_out_jnt = self.eye_corner_joints
        crnr_in_crv = Node.create('nurbsCurve', (self.base_jnt, crnr_in_jnt))
        crnr_out_crv = Node.create('nurbsCurve', (self.base_jnt, crnr_out_jnt))
        crnr_surf = Node(cmds.loft(
                crnr_in_crv, crnr_out_crv,
                range=True, autoReverse=True, ch=False)[0]
            )
        crnr_surf_shape = crnr_surf.get_shapes()[0]
        cmds.delete(crnr_in_crv, crnr_out_crv)
        
        # create util distance node for closest cross pnts
        dist_node = Node.create('distanceBetween')
        self.base_jnt.worldMatrix[0] >> dist_node.inMatrix1

        # get blinkline curve position
        self.blinkline_curve_position=[]
        for profile_jnt in self.lid_profile_joints:
            # get base joint and it's correspondence superior/inferior joint
            base_jnt = Node(profile_jnt).get_parent()
            corr_desc = profile_jnt.get_attr('corr_desc')
            opposite_jnt = NodeName(profile_jnt, desc=corr_desc)
            
            # create lids surface from 3-points
            lid_crv_top = Node.create('nurbsCurve', (base_jnt, profile_jnt))
            lid_crv_bot = Node.create('nurbsCurve', (base_jnt, opposite_jnt))

            lids_surf = Node(cmds.loft(
                            lid_crv_top, lid_crv_bot, range=True,
                            autoReverse=True, ch=False )[0])
                            
            lids_surf_shape = lids_surf.get_shapes()[0]
            cmds.delete(lid_crv_top, lid_crv_bot)

            # create intersect curve on surface
            x_surf_crv, x_surf_node = cmds.intersect(
                    lids_surf_shape, crnr_surf_shape,
                    firstSurface=True
                )

            # get closest parameter on corners curve
            # create and move blinkline aim locator
            x_crv = Node(cmds.duplicateCurve(x_surf_crv, ch=False)[0])
            pnt_num = x_crv.get_attr('spans') + x_crv.get_attr('degree')
            dist_list=[]
            for n in range(pnt_num):
                pnt_pos = cmds.xform(
                    '{0}.cv[{1}]'.format(x_crv, n),
                    q=True, ws=True, t=True ) 
                for ch,val in zip('XYZ', pnt_pos):
                    cmds.setAttr('{0}.point2{1}'.format(dist_node, ch), val)
                distance = cmds.getAttr('{}.distance'.format(dist_node))
                dist_list.append(distance)
                
            x_close_ind = dist_list.index(max(dist_list))
            x_close_pnt = '{0}.cv[{1}]'.format(x_crv, x_close_ind)

            x_pnt_position = cmds.xform(x_close_pnt, q=True, ws=True, t=True)
            param = crnrs_crv_shape.closest_param(x_pnt_position)
            crnrs_poci.set_attr('parameter', param)
           
            # cleanup intersect surface setup
            cmds.delete(lids_surf, x_surf_crv, x_surf_node, x_crv)
            
            # aim base joint ctrl to blinkline locator
            # get profile joint position at blink
            base_ctrl = jutil.get_ctrl(base_jnt)
            
            aim_cns = base_ctrl.constrain(
                            'aim', blinkline_aim_loc,
                            maintainOffset=False,
                            aimVector = self.aim_vector,
                            upVector = self.up_vector,
                            worldUpType = 'vector'
                        )
            blinkline_position = cmds.xform(
                    profile_jnt,
                    q=True, ws=True, t=True
                )
            self.blinkline_curve_position.append(blinkline_position)
            
            # cleanup cns node, reset base ctrl 
            cmds.delete(aim_cns)
            base_ctrl.set_attr('rotate', (0.0, 0.0, 0.0))
            
        
        # cleanup util nodes    
        cmds.delete(
            crnrs_crv, blinkline_aim_loc,
            crnrs_poci, crnr_surf, dist_node )
        
        # create blinkline curve
        if not cmds.objExists(self.blinkline_curve):
            self.blinkline_curve = Node.create(
                    'nurbsCurve',
                    self.blinkline_curve_position,
                    name=self.blinkline_curve,
                    spans=2, rebuild=True
                )

        # get blinkline curve shape and rebuild curve
        self.blinkline_curve_shape = Node(self.blinkline_curve).get_shapes()[0]
        
        self.blinkline_curve_shape.rebuild(
                ch=False,
                replaceOriginal=True,
                rebuildType=0, endKnots=1,
                keepRange=0, spans=5
            )
            
        # parent blinkline curve to blinkline system node
        Node(self.blinkline_curve).set_parent(self.get_system_node())
        
        # get or create the profile curve
        if not cmds.objExists(self.profile_curve):
            self.profile_curve = Node.create(
                    'nurbsCurve',
                    self.aim_target_position,
                    name=self.profile_curve,
                    spans=2, rebuild=True
                )
            
            # get profile curve shape and rebuild curve
            self.profile_curve_shape = Node(self.profile_curve).get_shapes()[0]
            self.profile_curve_shape.rebuild(
                ch=False,
                replaceOriginal=True,
                rebuildType=0, endKnots=1,
                keepRange=0, spans=5
            )
            
            # parent profile curve to blinkline system node
            Node(self.profile_curve).set_parent(self.get_system_node())
        
        # pin aim target locator to profile curve
        for profile_jnt in self.lid_profile_joints:
            # get base joint and aim target
            base_jnt = Node(profile_jnt).get_parent()
            aim_target = Node(base_jnt.attr(self.aim_target_attr).value)
            
            # attach poci node to profile curve
            poci = Node.create(
                'pointOnCurveInfo',
                name=NodeName(base_jnt, ext='poci')
                )
            poci.set_attr('isHistoricallyInteresting', 0)
            
            # connect driver curve to poci
            self.profile_curve_shape.worldSpace[0] >> poci.inputCurve
        
            # set poci parameter
            param = self.profile_curve_shape.closest_param(profile_jnt)
            poci.set_attr('parameter', param)
            
            # connect poci to aim target locator
            poci.position >> aim_target.translate
            
            # constrain joint ctrl offset node to aim target locator
            # keep joint ctrl animate-able
            base_ctrl = jutil.get_ctrl(base_jnt)
            base_ctrl_offset = base_ctrl.offset_node
            
            base_ctrl_offset.constrain(
                'aim', aim_target,
                maintainOffset=True,
                aimVector = self.aim_vector,
                upVector = self.up_vector,
                worldUpType = self.world_up_type,
                worldUpObject = self.world_up_obj
                )
        
        # bind profile curve to curve joints
        self.curve_joints_bind()
        
        # set up auto blink
        blink_bs_attr = self.setup_auto_blink()
        blink_attr = self.add_blink_sys_attr()
        blink_attr >> blink_bs_attr
        
        # set up blinkline bend
        bend_jnt = self.setup_blinklind_bend()
        bend_attr = self.add_bend_sys_attr()
        bend_attr >> bend_jnt.translateY
        


    def curve_joints_bind(self):
        """ TODO doc """
        ctrl_crv = self.profile_curve
        crv_shape = self.profile_curve_shape
        crv_bnd_jnts = self.lid_crv_jnts
        #crnr_jnts = self.eye_corner_joints
        
        # set curve index pair
        cv_num = ctrl_crv.get_attr('spans') + ctrl_crv.get_attr('degree')
        index_list = list(range(0, cv_num))
        rng=2
        crv_index_pairs = [
                index_list[i:i + rng] for i in range(0, len(index_list), rng)
            ]
        crv_index_pairs.insert(0, [0])
        crv_index_pairs.insert(cv_num, [cv_num-1])

        # bind
        scls_name = self.curve_bind_scls
        crv_scls = Node.create(
            'skinCluster',
            crv_bnd_jnts[0],
            crv_shape,
            toSelectedBones=True,
            name=scls_name )
        for jnt in crv_bnd_jnts[1:]:
            crv_scls.add_influence(jnt)
        
        # set weights
        for inf,ind_pair in zip(crv_bnd_jnts, crv_index_pairs):
            for cv_ind in ind_pair:
                cmds.skinPercent(
                    crv_scls,
                    '{}.cv[{}]'.format(crv_shape, cv_ind),
                    transformValue=[(inf, 1.0)] )

        self.curve_bind_scls = crv_scls
        
        # constrain crnr joints
        
    
    
    def setup_auto_blink(self):
        """
        Setup auto blink by blending profile curve to blinkline curve
        
        Returns:
            BlendShape: A blend shape instance and blend attribute
            Weight Attribute: A blend shape weight attribute
        """
        base_crv = self.profile_curve
        target_crv = self.blinkline_curve
        bs_node_name = NodeName(base_crv, part='blink', ext='BLENDSHAPE')

        
        # create blend shape
        blink_bs_node = Node.create(
            'blendShape',
            target_crv,
            base_crv,
            origin='local',
            name=bs_node_name )
            
        return(blink_bs_node.attr(target_crv.name))
        

    def setup_blinklind_bend(self):
        """
        Bind target blinkline curve with joints to set up blinkline bend
        
        Returns:
            Joint: A bend ctrl joint instance.
        """
        blinkline_crv = self.blinkline_curve
        blinkline_crv_shape = self.blinkline_curve_shape
        root_jnt = self.face_root_jnt
        bend_jnt_name = NodeName(blinkline_crv, ext='BENDJNT')
        bend_jnt_prnt_name = NodeName(blinkline_crv, ext='BENDPARENT')
        scls_name = NodeName(blinkline_crv, part='bend', ext='SKINCLUSTER')

        # get bend joint position
        points_position = blinkline_crv_shape.get_points()
        cv_num = blinkline_crv.get_attr('spans') + blinkline_crv.get_attr('degree')
        i01 = int(cv_num/2)
        i02 = i01 - 1
        x1,y1,z1 = points_position[i01]
        x2,y2,z2 = points_position[i02]
        jnt_pos=[]
        for v1,v2 in zip([x1,y1,z1], [x2,y2,z2]):
            jnt_pos.append((v1+v2)/2)
        
        # add bend joint    
        bend_jnt = Node.create('joint', name=bend_jnt_name)
        cmds.move(jnt_pos[0], jnt_pos[1], jnt_pos[2], bend_jnt)
        bend_jnt_prnt = Node.create('transform', name=bend_jnt_prnt_name)
        bend_jnt_prnt.align(bend_jnt)
        bend_jnt.set_parent(bend_jnt_prnt)
        bend_jnt_prnt.set_parent(self.get_system_node(worldspace=False))
        
        # align bend joint
        tangent_cns = bend_jnt_prnt.constrain(
                    'tangent',
                    blinkline_crv )
        cmds.delete(tangent_cns)

        # bind bend joint
        bend_scls = Node.create(
            'skinCluster',
            root_jnt,
            blinkline_crv,
            toSelectedBones=True,
            name=scls_name )
        bend_scls.add_influence(bend_jnt)
        
        # set weight
        npoc = Node.create('nearestPointOnCurve')
        blinkline_crv_shape.worldSpace[0] >> npoc.inputCurve
        
        mult = 1.5
        weight_list=[]
        bend_scls.set_attr('normalizeWeights', 0)
        for n in list(range(cv_num)):
            position = points_position[n]
            npoc.set_attr('inPosition', position)
            var = npoc.get_attr('parameter')
            if var > 0.5:
                var = 1.0 - var
            weight = var * 2.0 * mult

            cmds.skinPercent(
                bend_scls,
                '{}.cv[{}]'.format(blinkline_crv_shape, n),
                transformValue=[(root_jnt, (1.0-weight)), (bend_jnt, weight)])
                
        #cmds.skinPercent(bend_scls, blinkline_crv, normalize=True)
        bend_scls.set_attr('normalizeWeights', 1)
        cmds.delete(npoc)
                
        # ensure mid, first and last cv weighted 0.0 or 1.0
        for n in [0, int(cv_num-1)]:
            cmds.skinPercent(
                bend_scls,
                '{}.cv[{}]'.format(blinkline_crv_shape, n),
                transformValue=[(root_jnt, 1.0)] )

        for n in [i01, i02]:
            cmds.skinPercent(
                bend_scls,
                '{}.cv[{}]'.format(blinkline_crv_shape, n),
                transformValue=[(bend_jnt, 1.0)] )
                
        return(bend_jnt)
    
    
    def get_system_node(self, worldspace=True):
        """Returns the system node. Create a new one if not exists."""

        sys_parent_name = 'BlinklineSystem_ws'
        root_node = self.ws_root
        if not worldspace:
            sys_parent_name = 'BlinklineSystem'
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
        
        #sys_vis_attr = system_node.attr('visibility')
        #sys_vis_attr.keyable = False
        system_node.v.keyable = False
        
        return system_node    
    

    def add_blink_sys_attr(self):
        sys_node = Node(self.get_system_node(worldspace=False))
        blink_attr = 'blink'
        
        if not sys_node.has_attr(blink_attr):
            sys_node.add_attr(
                'float', name=blink_attr,
                hasMaxValue=True, maxValue=1.0,
                hasMinValue=True, minValue=0.0,
                defaultValue=0.0, keyable=True )
        
        return sys_node.attr(blink_attr)
        
        
    def add_bend_sys_attr(self):
        sys_node = self.get_system_node(worldspace=False)
        bend_attr = 'bend'
        
        if not sys_node.has_attr(bend_attr):
            sys_node.add_attr(
                'float', name=bend_attr,
                hasMaxValue=True, maxValue=1.0,
                hasMinValue=True, minValue=-1.0,
                defaultValue=0.0, keyable=True )
        
        return sys_node.attr(bend_attr)
    

            
        
    
####
def get_interp_value(start, end, driven_nodes, mult=1.0):
    """
    Input a start and an end point,
    will output a bezier curve interpolation values based on the distance. 
    """
    max_dist = mmath.distance(start, end)
    output_dict = {}
    for driven in driven_nodes:
        current_dist = mmath.distance(start, driven)
        value = mmath.curve_interp(current_dist / max_dist)
        if value != 1.0:
            value = value * mult
        output_dict[driven] = value
    return output_dict


def intersect_points_on_two_curves(curve1, curve2, project_dir=(0, 0, 1)):
    result = cmds.curveIntersect(
        curve1, curve2,
        useDirection=True, direction=project_dir)
    if result:
        param_list = result.split(' ')
        return float(param_list[0]), float(param_list[1])
    else:
        raise RuntimeError('Returns None, check projection direction.')


def pair_blend_transforms(
        xform1, xform2=None, desc=None, driven=None,
        channels=['translate', 'rotate', 'scale'], axis='XYZ'):
    """TODO doc"""

    uv_ax_convert = {'U': 'X', 'V': 'Y'}
    if not desc:
        if xform2:
            desc = NodeName(xform1).desc + NodeName(xform2).desc
        else:
            desc = NodeName(xform1).desc

    xform1_str = xform1.name
    if '->' in xform1.name:
        xform1_str = xform1.name.split('->')[-1]

    nodename = NodeName(xform1_str, desc=desc, ext='pairBlend')

    pb_node = Node.create(
        #'pairBlend', n=NodeName(xform1, desc=desc, ext='pairBlend'))
        'pairBlend', n=nodename)

    for ch, ax in zip(channels, axis):
        pb_ax = ax
        if ax in 'UV':
            pb_ax = uv_ax_convert[ax]

        if xform1:
            xform1.attr(ch + ax) >> pb_node.attr('inTranslate{}1'.format(pb_ax))
        if xform2:
            xform2.attr(ch + ax) >> pb_node.attr('inTranslate{}2'.format(pb_ax))
        if driven:
            pb_node.attr('outTranslate' + pb_ax) >> driven.attr(ch + ax)

    return pb_node


def follicle_handle_attach(param_handle, flc, uv=(0, 0)):
    """TODO doc"""
    param_handle.attr('parameterU') >> flc.attr('parameterU')
    param_handle.attr('parameterV') >> flc.attr('parameterV')
    param_handle.parameterU.value = uv[0]
    param_handle.parameterV.value = uv[1]
