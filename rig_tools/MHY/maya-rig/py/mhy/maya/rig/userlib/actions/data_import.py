import os
import maya.cmds as cmds
import maya.mel as mel

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.constant import SurfaceAssociation
from mhy.maya.scene import safe_open
import mhy.maya.nodezoo.utils as nutil

from mhy.maya.rig.base_actions import BaseRigDataAction
import mhy.maya.rig.constants as const
import mhy.maya.rig.data as dlib
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.utils as util

import mhy.python.core.compatible as compat
compat.reload(dlib)
from mhy.protostar.lib import ActionLibrary as alib
alib.refresh()

#TODO:
# ImportConstrains


class ImportMarkerSystem(BaseRigDataAction):
    """
    Builds the default marker system for each limb in the
    same graph as this action, then imports user data from
    a JSON file, if parameter `data_file` is not empty.
    """

    @pa.file_param(ext='json')
    def data_file(self):
        """The marker data file path."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If this action is not in a graph yet.
        """
        # finds the root graph
        graph = self.root_graph
        if not graph:
            raise exp.ActionError(self.name + ' is not in an action graph yet!')

        # delete current marker sytem
        if cmds.objExists(const.MARKER_ROOT):
            cmds.delete(const.MARKER_ROOT)

        # builds default markers for all limbs in the root graph
        graph.execute(exec_name='build_marker', no_break=True)

        # loads marker data
        path = self.data_file.value
        if path:
            dlib.import_marker_data(path)


class ImportCtrlShapes(BaseRigDataAction):
    """
    Imports MHYCtrl shape data from a JSON file.
    """

    @pa.file_param(ext='json')
    def data_file(self):
        """The ctrl shape data file path."""

    def run(self):
        """Executes this action."""
        path = self.data_file.value
        if path:
            dlib.import_ctrl_data(path)


class ImportExportSets(BaseRigDataAction):
    """
    Imports export set data from a JSON file.
    """

    @pa.file_param(ext='json')
    def data_file(self):
        """The export set data file path."""

    def run(self):
        """Executes this action."""
        path = self.data_file.value
        if path:
            dlib.import_set_data(path)


class ImportSkeleton(BaseRigDataAction):
    """
    Imports a skeleton from a given path. The skeleton can be either
    a rig skeleton or a bind skeleton (depends on the joint suffix).

    Action error is raised if the skeleton contains invalid joint
    suffixes, or mix joint suffixes.
    """

    @pa.file_param(ext=('ma', 'mb', 'fbx', 'obj'))
    def file_path(self):
        """The skeleton maya file path."""

    @pa.bool_param(default=False)
    def add_category(self):
        """If True, embed a category attribute on each joint.
        the category would be either "rig" or "bind"."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If the given skeleton file is not found.
            ActionError: If no joints are found in the skeleton file.
            ActionError: If joints with duplicated name exist.
            ActionError: If joints with invalid suffix exist.
        """
        # get input parameters
        file_path = self.file_path.value
        if not os.path.isfile(file_path):
            raise exp.ActionError(
                'Skeleton file not found: {}'.format(file_path))

        # import joints
        joints = safe_open(file_path, i=True, returnNewNodes=True)
        if joints:
            joints = nutil.ls(joints, type='joint')
        if not joints:
            raise exp.ActionError('No joints found in: {}'.format(file_path))

        joint_type = None
        for joint in joints:
            if len(cmds.ls(joint) or []) > 1:
                raise exp.ActionError(
                    'Duplicate joint found: {}'.format(joint))
            elif not NodeName.is_valid(joint):
                raise exp.ActionError(
                    'Joint not following naming convention: {}'.format(joint))

            ext = NodeName(joint).ext
            if ext == const.EXT_RIG_JOINT:
                joint_type = 'rig'
            elif ext == const.EXT_BIND_JOINT:
                joint_type = 'bind'
            else:
                joint_type = None
                raise exp.ActionError(
                    ('Invalid joint suffix: {} '
                        '(suffix must be {} or {})').format(
                        joint, const.EXT_RIG_JOINT, const.EXT_BIND_JOINT))

            # store transform data
            for attr, data_attr in zip(
                    ('jointOrient', 'translate', 'rotate'),
                    ('origJointOrient', 'origJointTranslate', 'origJointRotate')):
                if not joint.has_attr(data_attr):
                    data_attr = joint.add_attr('string', name=data_attr)
                    val = str(joint.get_attr(attr))
                    data_attr.value = val[1:-1]

            # add rig joint categories
            jutil.add_category(joint, joint_type)

        # ensures rig root groups exist
        util.init_rig_root_groups()
        group = const.RIG_SKEL_ROOT
        if joint_type == 'bind':
            group = const.BIND_SKEL_ROOT

        for joint in joints:
            if self.add_category.value:
                jutil.add_category(joint, joint_type)
            if not joint.get_parent():
                joint.set_parent(group)



class ImportPoseCtrlJoints(BaseRigDataAction):
    """Imports pose ctrl joints from a given path.

    # TODO test
    """

    @pa.file_param(ext=('ma', 'mb', 'fbx', 'obj'))
    def file_path(self):
        """The pase ctrl joint data file path."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If the given pose file is not found.
            ActionError: If no joints are found in the given file.
        """
        # get input parameters
        file_path = self.file_path.value
        if not os.path.isfile(file_path):
            raise exp.ActionError('Pose file not found: {}'.format(file_path))

        joints = safe_open(file_path, i=True, returnNewNodes=True)
        if joints:
            joints = nutil.ls(joints, type='joint')
        if not joints:
            raise exp.ActionError('No joints found in: {}'.format(file_path))

        # ensures rig root groups exist
        util.init_rig_root_groups()

        root_joints = [n for n in joints if not n.get_parent()][0]
        if cmds.objExists(const.RIG_SKEL_ROOT):
            cmds.parent(root_joints, const.RIG_SKEL_ROOT)
        cmds.hide(root_joints)


class ImportRigMesh(BaseRigDataAction):
    """Imports rig mesh from a given path."""

    @pa.file_param(ext=('ma', 'mb', 'fbx', 'obj'))
    def mesh_file(self):
        """The mesh maya file path."""

    @pa.enum_param(items=('mesh', 'cut_mesh', 'head_mesh', 'face_mesh', 'body_mesh', 'costume_mesh', 'utility_mesh', 'proxy_mesh', 'target_mesh', 'blend_mesh'))
    def mesh_type(self):
        """The mesh type."""

    @pa.bool_param(default=True)
    def add_vis_attr(self):
        """If True, adds a visibility attribute for toggling the mesh."""

    @pa.bool_param(default=True)
    def vis(self):
        """The default visibility state."""
        
    @pa.list_param(output=True)
    def imported_meshes(self):
        """The list of imported geometry names."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If the given pose file is not found.
            ActionError: If no joints are found in the given file.
        """
        # get input parameters
        mesh_type = self.mesh_type.enum_value
        mesh_grp = mesh_type.upper()
        defaul_vis = self.vis.value
        add_vis_attr = self.add_vis_attr.value
        file_path = self.mesh_file.value

        if not os.path.isfile(file_path):
            raise exp.ActionError('Mesh file not found: {}'.format(file_path))

        # import meshes
        imported_nodes = safe_open(file_path, i=True, returnNewNodes=True)
        meshes = None
        if imported_nodes:
            shapes = nutil.ls(imported_nodes, type='mesh') + nutil.ls(imported_nodes, type='nurbsSurface')      # nurbs surfaces are used in parameter driver system
            meshes = [shape.get_parent() for shape in shapes]
        if not meshes:
            raise exp.ActionError('No mesh found in: {}'.format(file_path))
        
        imp_mesh_ls = sorted([m.name for m in meshes])
        self.imported_meshes.value = imp_mesh_ls

        # ensures rig root groups exist
        util.init_rig_root_groups()

        # move meshes under mesh root
        if cmds.objExists(const.RIGMESH_ROOT):
            if not cmds.objExists(mesh_grp):
                mesh_grp = Node.create(
                    'transform', name=mesh_grp, parent=const.RIGMESH_ROOT)
            else:
                mesh_grp = Node(mesh_grp)
            cmds.parent(meshes, mesh_grp)
            
        # cleanup transform nodes
        transform_nodes = nutil.ls(imported_nodes, type='transform')
        delete_nodes = [n for n in transform_nodes if n not in meshes]
        cmds.delete(delete_nodes)

        # add reference attr on the rig root if requested
        if add_vis_attr and cmds.objExists(const.RIG_ROOT):
            root = Node(const.RIG_ROOT)
            attr_name = mesh_type.lower()
            if not root.has_attr(attr_name):
                ref_attr = root.add_attr(
                    'bool', name=attr_name,
                    defaultValue=defaul_vis, keyable=False)
                ref_attr.locked = False
                ref_attr.channelBox = True
            else:
                ref_attr = root.attr(attr_name)
            ref_attr >> mesh_grp.v

        self.info('imported rig mesh from {}'.format(file_path))


class ImportConnectionData(BaseRigDataAction):
    """Imports connection data from a given path."""

    @pa.file_param(ext='json')
    def data_file(self):
        """The connection data file path."""

    def run(self):
        """Executes this action."""
        dlib.import_connection_data(self.data_file.value)


class ImportDeformers(BaseRigDataAction):
    """Imports deformer data from a given JSON file."""

    @pa.dir_param()
    def data_path(self):
        """The deformer data directory path."""

    @pa.enum_param(items=SurfaceAssociation.items())
    def import_method(self):
        """The deformer import method."""

    @pa.bool_param(default=True)
    def clean_up(self):
        """If True, cleans up the imported deformers."""

    def run(self):
        """Executes this action."""
        dlib.import_rig_deformer_data(
            self.data_path.value,
            method=self.import_method.enum_value,
            clean_up=self.clean_up.value)


class ImportPoseData(BaseRigDataAction):
    """
    Imports pose data from a given JSON file
    """

    @pa.dir_param()
    def data_path(self):
        """The deformer data directory path."""

    @pa.bool_param(default=False)
    def build_anim_rig(self):
        """If True, pose connections will be set on parent group instead of controllers"""

    @pa.list_param(output=True)
    def created_pose_nodes(self):
        """The list of inserted pose nodes."""

    def run(self):
        """Core execution method."""
        pose_nodes = dlib.import_pose_data(self.data_path.value, self.build_anim_rig.value)
        pn_names = [i.ctrl_node.name for i in pose_nodes]
        self.created_pose_nodes.value = pn_names


class ImportPickerData(BaseRigDataAction):
    """
    Import picker data from a given JSON file
    """

    @pa.dir_param()
    def data_path(self):
        """The picker data directory path."""

    def run(self):
        """Executes this action."""
        dlib.import_picker_data(self.data_path.value)


class ImportShaders(BaseRigDataAction):
    """Import previously exported shader file, then assign to geos"""

    @pa.file_param(ext=('ma', 'mb', 'fbx'))
    def shader_file(self):
        """The maya shader file path."""
    
    @pa.file_param(ext='json')
    def data_file(self):
        """The shader json file path."""
        
    def run(self):
        """
        Executes ImportShaders.
        """
        shader_file = self.shader_file.value
        data_file = self.data_file.value
        
        if shader_file:
            safe_open(shader_file, i=True)
            
        dlib.import_shader_data(data_file)


class ImportAttributeSettings(BaseRigDataAction):
    """Import attributes setting file, and set values"""

    @pa.file_param(ext='json')
    def data_file(self):
        """The attrs json file path."""
        
    def run(self):
        """
        Executes ImportAttributes.
        """
        
        data_file = self.data_file.value
        dlib.import_attrs_data(data_file)


class ImportBSTargetsCreateConnect(BaseRigDataAction):
    """Import premade target shapes file"""

    @pa.file_param(ext=('ma', 'mb', 'fbx'))
    def target_file(self):
        """The path of the maya file contains bs target shapes."""
    
    @pa.file_param(ext='json')
    def data_file(self):
        """The targets and drivers data json file path."""
            
    @pa.str_param(default=(const.TARGETMESH_ROOT))
    def parent(self):
        """Set target meshes parent."""
        
    def run(self):
        """
        Executes ImportShaders.
        """
        target_file = self.target_file.value
        data_file = self.data_file.value
        
        safe_open(target_file, i=True)
        targets = dlib.import_bs_target_driver_data(data_file)
        
        if self.parent.value:
            cmds.parent(targets, self.parent.value)
            
        

class ImportMetahuman(BaseRigDataAction):
    """Imports MetaHuman from a given path."""

    @pa.dir_param()
    def dir_path(self):
        """The Published MetaHuman directory path."""
        
    @pa.str_param()
    def char_name(self):
        """The character name."""
        
    @pa.int_param(default=0)
    def lod(self):
        """The Metahuman retained face mesh lod number."""
        
    @pa.str_param()
    def mh_face_mesh(self):
        """The Metahuman retained face mesh name output."""
        
    @pa.str_param()
    def mh_body_mesh(self):
        """The Metahuman retained body mesh name output."""
        
    @pa.str_param()
    def mh_combined_mesh(self):
        """The Metahuman retained face/body combined mesh name output."""
        
    @pa.list_param()
    def mh_head_meshes(self):
        """TThe Metahuman retained lod head meshes name list output."""
        
    @pa.list_param()
    def mh_eye_meshes(self):
        """The Metahuman retained eye meshes name output."""
        
    @pa.list_param()
    def mh_eyeWater_meshes(self):
        """The Metahuman retained eyeEdge and cartilage meshes name output."""
    
    @pa.bool_param(default=True)
    def vis(self):
        """The default visibility state."""
        
    @pa.list_param()
    def ws_parents(self):
        """The worldspace parent nodes in standard MetaHuman rig."""
        
    @pa.list_param(default=None)
    def orient_nodes(self):
        """The nodes to be oriented to Y-up."""
        
    @pa.list_param(default=None)
    def hidden_nodes(self):
        """The nodes to be hidden from the standard MetaHuman rig."""
        
    @pa.list_param(default=None)
    def visible_nodes(self):
        """The nodes to be hidden from the standard MetaHuman rig."""
        
    @pa.list_param(default=None)
    def delete_nodes(self):
        """The nodes to be striped off from the standard MetaHuman rig."""
        
    @pa.bool_param(default=True)
    def body_rig(self):
        """Build body rig option."""
        
    @pa.list_param(default=['global_ctrl', 'body_offset_ctrl'])
    def mh_global_ctrls(self):
        """Modify the shape of input ctrl nodes."""

        

    def run(self):
        """
        Executes ImportMetahuman.
        """
        # get input parameters
        mh_dir_path = self.dir_path.value
        src_path = "{}/{}/SourceAssets".format(mh_dir_path, self.char_name.value )
        mh_rig_name = "{}_full_rig.ma".format(self.char_name.value )
        file_path = "{}/{}".format(src_path, mh_rig_name )
        if not os.path.isfile(file_path):
            file_path = "{}/{}".format(src_path, mh_rig_name.replace('.ma', '.mb') )
        
        lod = self.lod.value
        ws_parents = self.ws_parents.value
        orient_data = self.orient_nodes.value
        hidden_nodes = self.hidden_nodes.value
        visible_nodes = self.visible_nodes.value
        delete_nodes = self.delete_nodes.value
        build_body_rig = self.body_rig.value
        defaul_vis = self.vis.value
        global_ctrls = self.mh_global_ctrls.value

        if not os.path.isfile(file_path):
            raise exp.ActionError("Metahuman Rig file not found: {}".format(file_path))

        # import rig
        imported_nodes = safe_open(file_path, i=True, returnNewNodes=True)
        
        # From an input list:
        # - remove unwanted nodes in mh rig
        if delete_nodes:
            for node in delete_nodes:
                try:
                    print('Delete: {}'.format(node)),
                    cmds.delete(node)
                except:
                    cmds.warning("{} not deleted, it wasn't from imported metahuman.".format(node))
        
        # - set orientation on relative nodes (* not in use)
        if orient_data:
            for data_dict in orient_data:
                node = Node(data_dict['node'])
                ch = data_dict['channel']
                val = data_dict['value']
                node.set_attr(ch, val)
        
        # - hide nodes
        if hidden_nodes:
            for node in hidden_nodes:
                try:
                    Node(node).hide()
                except:
                    continue
                    
        # - show nodes
        if visible_nodes:
            for node in visible_nodes:
                try:
                    Node(node).show()
                except:
                    continue
        
        # From auto y-up rig ctrls:
        # - including body and face
        # - build body rig and ctrls
        if build_body_rig:
            import mhy.maya.rig.face.meta_body_ctrl as mbc
            mbc.BuildMetaHumansRigCtrls()
        
        # From lod input, search and clean up face mesh groups
        delete_lods = list(range(8))
        delete_lods.remove(lod)
        for del_ind in delete_lods:
            for part in ['head', 'body']:
                lod_grp = '{}_lod{}_grp'.format(part, del_ind)
                if cmds.objExists(lod_grp):
                    cmds.delete(lod_grp)
                else:
                    continue

        # Set retained mh meshes output names
        head_mesh_grp = Node('head_lod{}_grp'.format(lod))
        self.mh_head_meshes.value = [m.name for m in head_mesh_grp.list_relatives(c=True)]
        self.mh_face_mesh.value = 'head_lod{}_mesh'.format(lod)
        self.mh_body_mesh.value = 'f_tal_unw_body_lod{}_mesh'.format(lod)
        self.mh_combined_mesh.value = 'f_tal_unw_combined_lod{}_mesh'.format(lod)
        self.mh_eye_meshes.value = [
                'eyeLeft_lod{}_mesh'.format(lod),
                'eyeRight_lod{}_mesh'.format(lod)
            ]
        self.mh_eyeWater_meshes.value = [
                'eyeEdge_lod{}_mesh'.format(lod),
                'cartilage_lod{}_mesh'.format(lod)
            ]
        
        # set scene Y-up
        #   - assume 'persp' is the camera name
        cmds.upAxis(axis='y', rotateView=True)
        cmds.viewSet('persp', home=True )
        
        # ensures rig root groups exist
        util.init_rig_root_groups()
        
        # move mh rig to metahuman group under worldspace node
        if ws_parents:
            for node in ws_parents:
                try:
                    cmds.parent(node, const.MH_ROOT)
                except:
                    cmds.warning('{} cannot be parented to {}.'.format(node, const.MH_ROOT))
        else:
            raise exp.ActionError("MetaHuman root node not exist: {}".format(const.MH_ROOT))
        
        # delete all display layers
        layers = [l for l in cmds.ls(typ='displayLayer') if 'defaultLayer' not in l]
        try:
            cmds.delete(layers)
        except:
            pass
            
        # delete unused
        mel.eval('MLdeleteUnused;')
        
        ''' #pre-updated in gptc_full_rig.mb
        # update texture file path
        mh_textures = [tex for tex in imported_nodes
            if cmds.objExists(tex) and Node(tex).type_name=='file']
        for texture in mh_textures:
            t_node = Node(texture)
            path_orig = t_node.get_attr('fileTextureName')
            path_tail = path_orig.split('MetaHumans')[-1]
            new_path = mh_dir_path + path_tail
            t_node.set_attr('fileTextureName', new_path)
        '''
        
        # other custom setting
        
        

        self.info('Successfully imported metahuman: {}'.format(mh_rig_name))


class ImportCustomAssets(BaseRigDataAction):
    """
    Imports a custom rigging asset which could be anything ignore the standard rules.
    """

    @pa.file_param(ext=('ma', 'mb', 'fbx', 'obj'))
    def file_path(self):
        """The asset file path."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If the given file is not found.
        """
        # get input parameters
        file_path = self.file_path.value
        if not os.path.isfile(file_path):
            raise exp.ActionError(
                'Asset file not found: {}'.format(file_path))

        # import asset
        safe_open(file_path, i=True, returnNewNodes=True)
        
