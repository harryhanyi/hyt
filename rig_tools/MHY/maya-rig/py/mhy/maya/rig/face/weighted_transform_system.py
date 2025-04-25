"""
Create one single poly face onto each influence, then manipulate influences
position via a deformed mesh
"""

from maya import cmds

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.utils as utils


class WeightedTransformSystem():
    """
    TODO doc
    """

    def __init__(
            self,
            xforms,
            type_='wts',
            ctrl_ext='CTRL',
            ws_root=None,
            height=.2,
            width=.2,
            build_mesh_only=False,
            wts_grp_node='weightedTransformSystem',
            add_chew=True ):
        """TODO doc"""
        
        self.xforms = [Node(x) for x in xforms]
        self.type_ = type_
        self.ctrl_ext = ctrl_ext
        self.ws_root = ws_root
        self.height = height
        self.width = width
        self.build_mesh_only = build_mesh_only
        self.wts_grp_node = wts_grp_node
        self.add_chew = add_chew

        self.def_poly_list = []
        self.jnt_cls_wt_dict = {}
        self.wts_mesh = None
        self.chew_target = None

    def create(self):
        """TODO doc"""
        # create local poly faces on each transform
        for wts_xform in self.xforms:
            ft_pos = wts_xform.get_translation(space='world')
            d_poly = Node(cmds.polyPlane(
                width=.1, height=.1, subdivisionsX=1, subdivisionsY=1,
                axis=(0, 0, 1), constructionHistory=False)[0])      #width=.25, height=.25,axis=(0, 1, 0)
            cmds.move(ft_pos[0], ft_pos[1], ft_pos[2], d_poly)
            self.def_poly_list.append(d_poly)

        # combine poly faces to one mesh
        self.wts_mesh = self.wts_mesh_combine()
        if self.add_chew:
            name = NodeName(
                self.wts_mesh, desc='chew', ext='BLENDMESH')
            self.chew_target = self.wts_mesh.duplicate(name=name)[0]

        if not self.build_mesh_only:
            # get mesh uv dictionary
            def_mesh_shape = self.wts_mesh.get_shapes()[0]
            flc_u_pos_dict = self.wts_mesh_uv_layout()

            # build the mesh into a wts deformable mesh
            flc_shape_nodes = []
            flc_xform_nodes = []
            for wts_xform in self.xforms:
                name = NodeName(wts_xform, ext='wtsLOCUS')
                flc = Node.create('follicle', def_mesh_shape, name=name)
                flc.name = NodeName(wts_xform, ext='wtsFLC')
                flc_xform = flc.get_parent()
                flc_shape_nodes.append(flc)
                flc_xform_nodes.append(flc_xform)

            # position follicle to each joint
            v = 1.0 / float(len(self.xforms)) / 2.0
            for flc in flc_shape_nodes:
                wts_xform = Node(NodeName(flc, ext=self.ctrl_ext))
                if wts_xform in flc_u_pos_dict.keys():
                    u = flc_u_pos_dict[wts_xform]
                    flc.parameterU.value = u
                    flc.parameterV.value = v
                else:
                    raise RuntimeError(
                        ('{} not in position dictionary, '
                         'name does not match follicle node {}.').format(
                             wts_xform, flc))

            # insert flc transpot nodes to facial transform hierarchy
            self.wts_mesh_connect(flc_xform_nodes, self.wts_mesh)

            # cleanup
            follicle_grp = self.type_ + '_follicle'
            if not cmds.objExists(follicle_grp):
                follicle_grp = Node.create('transform', name=follicle_grp)
                follicle_grp.lock('trs')
                follicle_grp.v.value = False
            else:
                follicle_grp = Node(follicle_grp)

            if not cmds.objExists(self.wts_grp_node):
                self.wts_grp_node = Node.create(
                    'transform', name=self.wts_grp_node)
                self.wts_grp_node.lock('trs')

            cmds.parent(flc_xform_nodes, follicle_grp)
            cmds.parent(self.wts_mesh, follicle_grp, self.wts_grp_node)
            if self.add_chew:
                self.chew_target.set_parent(self.wts_grp_node)
            if self.ws_root:
                self.wts_grp_node.set_parent(self.ws_root)

        if self.add_chew:
            return self.wts_grp_node, self.wts_mesh, self.chew_target
        else:
            return self.wts_grp_node, self.wts_mesh

    def wts_mesh_combine(self):
        """Properly combine deformable poly faces to a one mesh"""
        deformable_poly_list = self.def_poly_list

        # combine mesh
        combine_mesh = deformable_poly_list[0]
        for i in range(len(deformable_poly_list)):
            if i < (len(deformable_poly_list) - 1):
                combine_mesh = cmds.polyUnite(
                    combine_mesh, deformable_poly_list[i + 1],
                    constructionHistory=False, mergeUVSets=True)[0]
        combine_mesh = Node(combine_mesh)
        combine_mesh.name = self.type_ + '_main_00_M_DEFMESH'
        combine_mesh.lock('trs')

        return combine_mesh

    def wts_mesh_uv_layout(self):
        """Layout deformable mesh based on input influences position
        then create follicle node for each faces.
        """
        cmds.polyMultiLayoutUV(
            self.wts_mesh, layoutMethod=1, scale=1, rotateForBestFit=0,
            flipReversed=True, percentageSpace=0, layout=1, prescale=0,
            sizeU=1, sizeV=1, offsetU=0, offsetV=0)

        u_positions = []
        unit = 0
        num_vert = self.wts_mesh.get_shapes()[0].num_vertices
        if len(self.xforms) == (num_vert / 4):
            unit = float(1) / float(len(self.xforms)) / float(2)
            # print 'Number of verts:', num_vert
            # print 'UV unit size =', unit
        else:
            raise RuntimeError(
                ('The numbers of facial joints and deformable '
                 'poly faces do not match.'))

        for i in range(len(self.xforms) * 2)[1::2]:
            uVal = unit * i
            u_positions.append(uVal)

        transforms_folicle_u_pos = dict(zip(self.xforms, u_positions))
        return transforms_folicle_u_pos

    def wts_mesh_connect(self, flc_xform_nodes, wts_mesh):
        """TODO doc"""
        for wts_xform in self.xforms:
            plc = wts_xform.plc_node
            if plc:
                parent_node = plc.get_parent()
                if not parent_node:
                    raise RuntimeError(
                        'Plc node: {} dose not have a parent.'.format(plc))
            else:
                raise TypeError(
                    'Plc node: {} does not exist in scene.'.format(plc))

            # find correct follicle shape node
            ids = []
            for i, node in enumerate(flc_xform_nodes):
                if wts_xform.name.replace(self.ctrl_ext, '') in node.name:
                    ids.append(i)
            if len(ids) == 1:
                name = NodeName(wts_xform, ext='wtsORIGIN')
                transport_orig = Node.create(
                    'transform', name=name, parent=parent_node)
                name = NodeName(wts_xform, ext='wtsTRANSPORT')
                transport_node = Node.create(
                    'transform', parent=transport_orig, name=name)

                # connect follicle to transport node
                for ch in ('translate', 'rotate'):
                    flc_xform_nodes[(ids[0])].attr(ch) >> transport_node.attr(ch)

                plc.set_parent(transport_node)
            else:
                print(wts_xform, ids)
                raise RuntimeError('Either find no match or more than one match')

    def add_wts_default_cluster(self):
        """TODO doc"""
        pass
        

    def get_wts_mesh_cluster_weight_dict(self):
        """TODO doc"""
        clusters = utils.getDeformers(self.wts_mesh, deformerTypes='cluster')
        shape = self.wts_mesh.get_shapes()[0]
        cpom = Node.create('closestPointOnMesh')
        shape.worldMesh >> cpom.inMesh
        self.jnt_cls_wt_dict = {}
        for ctrl in self.input_transforms:
            jnt = ctrl.search_node('.*JNT', upstream=False)
            pos = jnt.set_translation(space='world')
            cpom.set_attr('inPosition', pos)
            f_idx = cpom.closestFaceIndex.value
            face = '{}.f[{}]'.format(shape, f_idx)
            verts = cmds.polyListComponentConversion(
                face, fromFace=True, toVertex=True)
            cls_wt_dict = {}
            for cls in clusters:
                wt = cmds.percent(cls, verts[0], q=True, v=True)
                cls_wt_dict[cls] = wt[0]
            self.jnt_cls_wt_dict[jnt] = cls_wt_dict

        return self.jnt_cls_wt_dict

    def wts_mesh_non_prop_scale_setup(self, clusters=[]):
        """This setup allows non-proportional scale through
        weightedTransformMesh.
        """
        if not self.jnt_cls_wt_dict or not clusters:
            raise TypeError(
                ('Either joint cluster weight dictionary or '
                 'cluster name list is empty.'))

        for jnt, cls_dict in self.jnt_cls_wt_dict.items():
            cls_wt_list = []
            for cls in clusters:
                handle = cls.get_handle()
                ctrl = handle.search_node('.*CTRL', upstream=True)
                wt = cls_dict[cls]
                if wt:
                    cls_wt_list.append((ctrl, wt))

            driver_num = len(cls_wt_list)
            if driver_num > 1:
                pma = Node.create(
                    'plusMinusAverage', name=jnt.name + '_scale_pma')
                for i in range(driver_num):
                    ctrl, wt = cls_wt_list[i]
                    utils.create_multiplier(
                        ctrl.s, pma.attr('input3D[{}]'.format(i)),
                        wt, reverse=True)
                    utils.create_multiplier(
                        ctrl.s, pma.attr('input3D[{}]'.format(i)),
                        wt, reverse=True)

                for ax in 'xyz':
                    pma.set_attr(
                        'input3D[{}].input3D{}'.format(driver_num, ax), -1)
                pma.output3D >> jnt.s

            elif driver_num == 1:
                utils.create_multiplier(ctrl.s, jnt.s, wt, reverse=True)
