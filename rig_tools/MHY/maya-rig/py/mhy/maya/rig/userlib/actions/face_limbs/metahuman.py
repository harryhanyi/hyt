from maya import cmds
import maya.mel as mel

import mhy.protostar.core.parameter as pa
from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
import mhy.maya.rig.utils as util
from mhy.maya.nodezoo.node.blend_shape import BlendShape

import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const

import mhy.python.core.compatible as compat
compat.reload(const)


class MetahumanToFace(bl.BaseLimb):
    """
    Use Metahuman face rig as a core.

    :limb type: face
    """
    _LIMB_TYPE = 'metahuman'

    # -- input parameters
    @pa.str_param()
    def face_mesh(self):
        """
        1. Usually the latest published face mesh.
        2. Used for hi face corrective blending.
        """

    @pa.str_param(default=None)
    def body_mesh(self):
        """
        1. Usually the latest published body mesh.
        2. Used for hi body corrective blending.
        """
    
    @pa.str_param()
    def mh_face_mesh(self):
        """The actual face mesh in MH,
            usually get the name of the mesh from ImportMetahuman."""
        
    @pa.str_param(default=None)
    def mh_body_mesh(self):
        """The actual body mesh in MH,
            usually get the name of the mesh from ImportMetahuman."""
        
    @pa.bool_param(default=False)
    def add_previz_mesh(self):
        """Add previz mesh and blend shape network for visulization."""
        
    @pa.str_param(default='hiFace')
    def hiface_alias_attr(self):
        """The alias attr for the hires face mesh on the blend shape node."""

    @pa.str_param(default='metahuman')
    def mh_face_alias_attr(self):
        """The alias attr for the metahuman face mesh on the blend shape node."""

    @pa.str_param(default='CTRL_expressions')
    def mh_expression_node(self):
        """Metahuman custom expression node which carries all pose names."""

    @pa.list_param(item_type='str')
    def sculpt_meshes(self):
        """A mesh list containing the pose sculpt/modification meshes."""

    @pa.list_param(item_type='str')
    def eye_meshes(self):
        """Usually the latest published eye meshes."""

    @pa.list_param(item_type='str')
    def eyeWater_meshes(self):
        """Usually the latest published eyeEdge and cartilage meshes."""

    @pa.list_param(item_type='str')
    def mh_eye_meshes(self):
        """Usually the latest published metahuman eye meshes."""

    @pa.list_param(item_type='str')
    def mh_eyeWater_meshes(self):
        """Usually the latest published metahuman eyeEdge and cartilage meshes."""

    @pa.bool_param(default=True)
    def z_up_mh(self):
        """Confirm the input Metahuman is a Z-up rig."""

    # --- end of parameter definition

    def marker_data(self):
        """Skip marker data as this limb depends on a pre-existing
        joint hierarchy."""
        return

    def run(self):
        """Wrap on the top of existing Metahuman rig."""
        
        self._z_up_mh = self.z_up_mh.value
        self._face_mesh = self.face_mesh.value
        self._body_mesh = self.body_mesh.value
        self._mh_face_mesh = self.mh_face_mesh.value
        self._mh_body_mesh = self.mh_body_mesh.value
        self._eye_meshes = self.eye_meshes.value
        self._eyeWater_meshes = self.eyeWater_meshes.value
        self._mh_eye_meshes = self.mh_eye_meshes.value
        self._mh_eyeWater_meshes = self.mh_eyeWater_meshes.value

        self._face_shape = self._get_shape(self._face_mesh)
        self._mh_face_shape = self._get_shape(self._mh_face_mesh)

        self._hiface_alias_attr = self.hiface_alias_attr.value
        self._mh_face_alias_attr = self.mh_face_alias_attr.value
        self._mh_expression_node = self.mh_expression_node.value
        self._is_previz = self.add_previz_mesh.value

        self._previz_mesh = None
        self._previz_bs_node = None
        self._mh_bs_node = None
        
        # sync-up head meshes Y to Z before blending
        if self._z_up_mh:
            self._yup_to_zup(const.BLENDMESH_ROOT)
            if self._mh_body_mesh:
                self._yup_to_zup(const.BODYMESH_ROOT)

        # create previz mesh and blend shape network
        # or add hi face to metahuman blend shape node
        if self._is_previz:
            self._create_previz_mesh()
            self._build_previz_bs_network()
        else:
            self._add_hiface_to_mh_bs()
            self._add_eye_to_mh_bs()
            self._add_eyeWater_to_mh_bs()
            if self._mh_body_mesh:
                self._add_body_to_mh_bs()

        # setup sculpt meshes if there is inpput
        self._sculpt_meshes = self.sculpt_meshes.value
        if self._sculpt_meshes:
            self.pose_target_dict={}
            self._prep_sculpt_meshes()
            # sync-up sculpt meshes Y to Z before blending
            if self._z_up_mh:
                self._yup_to_zup(const.TARGETMESH_ROOT)

            rig_ctrl = "global_ctrl"
            if not cmds.objExists(rig_ctrl):
                rig_ctrl = "root_drv"

            Node(rig_ctrl).set_attr('rx', 0)
            self._apply_sculpts_to_bs()

            # revert if mh is z-up
            if self._z_up_mh:
                Node(rig_ctrl).set_attr('rx', -90)

        else:
            print("Sculpt meshes input is empty, \
                  expecting loadind blend shape in deformer loading.")

        # set blend shape target weights for non pre-viz build
        if not self._is_previz:
            hi_face = self._face_mesh
            mh_face = self._mh_face_mesh
            posename = self._hiface_alias_attr
            blend_shape = self._get_bs_node_from_mesh(mh_face)
            blend_shape.set_target_weight(hi_face, 1.0)
            blend_shape.attr(hi_face).alias = posename

            if self._eye_meshes and self._mh_eye_meshes:
                for eye, mh_eye in zip(
                            self._eye_meshes,
                            self._mh_eye_meshes):
                    blend_shape = self._get_bs_node_from_mesh(mh_eye)
                    blend_shape.set_target_weight(eye, 1.0)

        # retain base limb ctrl hierarchy structure
        bl.BaseLimb.ctrl_leaf_parent = bl.BaseLimb.ctrl_root

        # pre-load textures shaders and lights
        cmds.displayPref(materialLoadingMode = "parallel")
        mel.eval("DisplayShadedAndTextured")
        mel.eval("DisplayLight")

        # reset scene up axis to y for anim rig
        cmds.upAxis(axis='y', rotateView=True)
        cmds.viewSet('persp', home=True )



    def _get_shape(self, mesh):
        if not mesh:
            raise TypeError("Need a mesh name as input.")

        if cmds.objExists(mesh):
            shape = Node(mesh).get_shapes(exact_type='mesh')
            shape = shape[0] if shape else None
            if shape:
                return shape
            else:
                raise RuntimeError(
                    "Shape node not found on the input mesh: [{}]".format(mesh))
        else:
            raise RuntimeError("Input mesh not exists: [{}]".format(mesh))
        

    def _create_previz_mesh(self):
        """
        Create previz mesh by dulicate the base metahuman face mesh.
        """
        base_mesh = self._mh_face_mesh
        try:
            previz_mesh_nm = NodeName(base_mesh, part='viz')
        except:
            previz_mesh_nm = base_mesh.replace(
                base_mesh.split('_')[0], 'viz')

        if not cmds.objExists(previz_mesh_nm):
            self._previz_mesh = Node(base_mesh).duplicate(name=previz_mesh_nm)
        else:
            self._previz_mesh = Node(previz_mesh_nm)

        
    def _build_previz_bs_network(self):
        """
        1. Create a blend shape node onto the pre-viz mesh.
        2. Add metahuman as the first targte.
        3. Add the detailed hi face as the second target.
        4. Expecting pose based modification targets when needed.
        """
        base_mesh = self._previz_mesh
        metahuman_mesh = self._mh_face_mesh
        hi_face = self._face_mesh

        try:
            bs_nm = NodeName(base_mesh, ext='BLENDSHAPE')
        except:
            bs_nm = base_mesh.replace(
                base_mesh.split('_')[-1], 'BLENDSHAPE')

        if not cmds.objExists(bs_nm):
            self._previz_bs_node = Node.create(
                'blendShape',
                metahuman_mesh, hi_face,
                base_mesh,
                name=bs_nm )
        else:
            self._previz_bs_node = Node(bs_nm)

        # confirm target weights
        blend_shape = self._previz_bs_node
        for target in [metahuman_mesh, hi_face]:
            blend_shape.set_target_weight(target, 1.0)

        # update alias attributes
        blend_shape.attr(metahuman_mesh).alias = self._mh_face_alias_attr
        blend_shape.attr(hi_face).alias = self._hiface_alias_attr

        # hide metahuman face mesh
        mesh = Node(metahuman_mesh)
        mesh.v.value = False
        mesh.lock('trs')

    def _get_bs_node_from_mesh(self, mesh=None):
        """Get the blend shape node on given mesh"""
        if not mesh:
            raise RuntimeError("Need to provide a mesh name.")
        
        if not isinstance(mesh, str):
            mesh = mesh.name

        blend_shape_node = None
        shape = self._get_shape(mesh)
        history = cmds.ls(cmds.listHistory(shape, levels=2), type='blendShape')
        if history and cmds.nodeType(history[0])=='blendShape':
            blend_shape_node = Node(history[0])

        return blend_shape_node

    def _create_target_mesh(self, sculpt_mesh):
        base_mesh = self._mh_face_mesh
        hi_face = self._face_mesh

        # turn off hi face bs weights
        blend_shape = self._get_bs_node_from_mesh(base_mesh)
        orig_wt = blend_shape.get_attr(hi_face)
        blend_shape.set_target_weight(hi_face, 0.0)

        target_mesh_nm = NodeName(sculpt_mesh).desc
        target_mesh = Node(base_mesh).duplicate(name=target_mesh_nm)[0]
        target_mesh.unlock('trs')
        target_mesh.set_parent(const.TARGETMESH_ROOT)

        # revert hi face bs weights
        blend_shape.set_target_weight(hi_face, orig_wt)
        
        return target_mesh

    def _get_pose_driver_node_attr(self, posename):
        exp_node = Node(self._mh_expression_node)
        exp_attr_ls = [
            a.name for a in exp_node.list_attr(ud=True)]
        pose_attr = exp_node.attr(posename)

        if not posename in exp_attr_ls:
            raise RuntimeError(
                "Cannot find pose attr: [{}].".format(pose_attr))

        if pose_attr.isConnected:
            driver_plug = pose_attr.source_node.list_connections(
                source=True,
                plugs=True,
                destination=False,
                skipConversionNodes=True)[0]
            driver_node = driver_plug.node
            driver_attr = driver_plug.name
        else:
            raise AttributeError("{} is not connected.".format(pose_attr))
        
        return driver_node, driver_attr


    def _prep_sculpt_meshes(self, mesh_list=None):
        """
        Get a clean delta mesh as a bs target by
        removing delta from metahuman and the hi face
        """
        if not mesh_list:
            mesh_list = self._sculpt_meshes

        for sculpt_mesh in mesh_list:
            # create pose target mesh and define pose name
            sculpt_mesh = Node(sculpt_mesh)
            target_mesh = self._create_target_mesh(sculpt_mesh)
            posename = target_mesh.name

            # get pose driver node and attr
            driver_node, driver_attr = self._get_pose_driver_node_attr(posename)
            # archive to data dict
            data = {}
            data['sculpt'] = sculpt_mesh
            data['target'] = target_mesh
            data['driver'] = driver_node
            data['attr'] = driver_attr
            self.pose_target_dict[posename] = data

    def _get_mh_points_at_pose(self, driver_node, driver_attr):
        mh_face_sh = self._mh_face_shape
        driver_node.set_attr(driver_attr, 1.0)
        mh_pnts_at_pose = mh_face_sh.get_points(space='object')
        driver_node.set_attr(driver_attr, 0.0)

        return mh_pnts_at_pose

    def _remove_static_points(self, base_points, target_points, threshold=None):
        """Compare between two point array,
        remove the points not changing position.
        Args:
            base_points: points array from the base mesh.
            target_points: points array from the modified mesh.
        
        Returns: a list of point index numbers of the moved points.
        """
        if not threshold:
            threshold = 0.0001

        changed_pnts_id_ls = []
        for id, pnts_tuple in enumerate(zip(base_points, target_points)):
            try:
                dist = pow(sum([(a - b)*(a - b) for a, b in zip(pnts_tuple[0], pnts_tuple[1])]), 0.5)
                if dist > threshold:
                    changed_pnts_id_ls.append(id)
            except:
                continue
        
        return changed_pnts_id_ls


    def _get_points_delta(self, base_points, target_points):
        """
        Retuns: a dictionary of [point index]:[delta data]
        """
        point_delta_vectors = {}
        # get vtx id list
        pnt_id_ls = self._remove_static_points(base_points, target_points)
        # get delta data
        # tar - hiface - base
        for i in pnt_id_ls:
            delta = [tp-bp for tp, bp in zip(target_points[i], base_points[i])]
            point_delta_vectors[i] = delta

        return point_delta_vectors


    def _get_real_sculpted_points(self, sculpt_mesh):
        hi_pnts = self._face_shape.get_points(space='object')
        sculpt_pnts = self._get_shape(sculpt_mesh).get_points(space='object')
        real_sclpt_pnts = self._get_points_delta(hi_pnts, sculpt_pnts)
        
        return real_sclpt_pnts


    def _get_changed_sculpted_points_delta(self, sculpt_mesh, driver_node, driver_attr):
        mh_pnts_at_ps = self._get_mh_points_at_pose(driver_node, driver_attr)
        sculpt_pnts = self._get_shape(sculpt_mesh).get_points(space='object')
        sculpted_point_delta = self._get_points_delta(mh_pnts_at_ps, sculpt_pnts)

        return sculpted_point_delta


    def _update_delta_data(self, mesh, delta_data):
        # replace new delta vector in target mesh points array
        mesh_points = self._get_shape(mesh).get_points(space='object')
        for id, delta in delta_data.items():
            new_vector = [dt+tp for dt,tp in zip(delta, mesh_points[id])]
            mesh_points[id] = new_vector

        # set target mesh points
        self._get_shape(mesh).set_points(mesh_points, space='object')


    def _set_posename_alias(self, blendshape, target_attr, posename):
        if posename not in cmds.aliasAttr(blendshape, q=True) and \
            cmds.objExists('{}.{}'.format(blendshape, target_attr)):
            blendshape.attr(target_attr).alias = posename
        else:
            pass

    def _yup_to_zup(self, root_node):
        """
        1. Rotate root node of meshes from Y-up to Z-up,
            then freeze the rotate channels
        2. Mainly used on hi meshes and scuplt meshes,
            they need to be in Z-up enable to be belnded onto the final mh meshes.
        """
        root = Node(root_node)
        root.set_attr('rx', 90)
        root.make_identity(apply=True, rotate=True)

    def _apply_sculpts_to_bs(self, pose_target_dict=None):
        """
        """
        if not pose_target_dict:
            pose_target_dict = self.pose_target_dict

        for posename, data in pose_target_dict.items():
            # get data
            sculpt_mesh = data['sculpt']
            target_mesh = data['target']
            driver_node = data['driver']
            driver_attr = data['attr']

            # get changed points delta
            point_delta_vectors = self._get_changed_sculpted_points_delta(
                sculpt_mesh, driver_node, driver_attr)

            # update target mesh points
            self._update_delta_data(target_mesh, point_delta_vectors)

            # set bs node
            if self._previz_mesh:
                blend_shape = self._previz_bs_node
            else:
                self._mh_bs_node = self._get_bs_node_from_mesh(self._mh_face_mesh)
                blend_shape = self._mh_bs_node
            # add to blend shape node on mesh
            blend_shape.add_target(target_mesh)

            # connect driver attr
            #driver_attr_node = driver_node.attr(driver_attr)
            driver_attr_node = Node(self._mh_expression_node).attr(posename)
            bs_attr_node = blend_shape.attr(posename)
            driver_attr_node >> bs_attr_node

            # if blink target, apply again
            #   to fix orig mh rig eye blink not shut issue
            if 'Blink' in target_mesh.name:
                blink_extra_delta = self._get_changed_sculpted_points_delta(
                    sculpt_mesh, driver_node, driver_attr)
                self._update_delta_data(target_mesh, blink_extra_delta)

            # clean up sculpt meshes?
            #cmds.delete(sculpt_mesh)


    def _add_hiface_to_mh_bs(self):
        if not self._mh_bs_node:
            self._mh_bs_node = self._get_bs_node_from_mesh(self._mh_face_mesh)

        hi_face = self._face_mesh
        blend_shape = self._mh_bs_node
        blend_shape.add_target(hi_face)
        blend_shape.set_target_weight(hi_face, 1.0)

    def _add_eye_to_mh_bs(self):
        if self._eye_meshes and self._mh_eye_meshes:
            for eye, mh_eye in zip(self._eye_meshes, self._mh_eye_meshes):
                blend_shape = self._get_bs_node_from_mesh(mh_eye)
                blend_shape.add_target(eye)

    def _add_eyeWater_to_mh_bs(self):
        if self._eyeWater_meshes and self._mh_eyeWater_meshes:
            for water, mh_water in zip(self._eyeWater_meshes, self._mh_eyeWater_meshes):
                blend_shape = self._get_bs_node_from_mesh(mh_water)
                if blend_shape:
                    blend_shape.add_target(water)
                else:
                    bs_nm = NodeName(mh_water, ext='BLENDSHAPE')
                    blend_shape = Node.create(
                        'blendShape',
                        water, mh_water,
                        frontOfChain=True,
                        name=bs_nm )
                blend_shape.set_target_weight(water, 1.0)

    def _add_body_to_mh_bs(self):
        if self._body_mesh and self._mh_body_mesh:
            bs_name = '{}_BlendShapes'.format(self._mh_body_mesh)
            blend_shape = BlendShape.create(
                                self._body_mesh,
                                self._mh_body_mesh,
                                frontOfChain=True,
                                name=bs_name
                            )
            blend_shape.set_target_weight(self._body_mesh, 1.0)
