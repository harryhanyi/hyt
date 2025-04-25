import maya.cmds as cmds
import maya.mel as mel

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp
from mhy.maya.rig.base_actions import BaseRigDataAction
import mhy.maya.rig.constants as const
from mhy.maya.nodezoo.node import Node


class ExportMetahumanToFBX(BaseRigDataAction):

    @pa.bool_param(default=True)
    def fbx_export(self):
        """Prep rig for fbx export."""

    @pa.str_param()
    def maya_scene_path(self):
        """
        the export dir path to the current rig workarea scenes folder
        only works when "fbx_export" is on
        """

    @pa.str_param()
    def fbx_file_name(self):
        """
        """

    @pa.list_param(item_type='str')
    def head_meshes(self):
        """The Metahuman retained lod head meshes name list input."""

    def run(self):
        """
        Executes this action.
        """
        if self.fbx_export.value:
            self._scene_path = self.maya_scene_path.value
            _fbx_file = self.fbx_file_name().value
            self._export_path = '{}/{}'.format(self._scene_path, _fbx_file)

            _fbx_preset = 'AME.fbxexportpreset'
            _fbx_dir_path = self._scene_path.replace('scenes', 'FBX')
            self._fbx_preset_path = '{}/{}'.format(_fbx_dir_path, _fbx_preset)
            
            self._head_meshes = self.head_meshes.value
            self._root_jnt = None

            self._fbx_export_prep()
            #self._export_rig()

        else:
            pass


    def _fbx_export_prep(self):
        """
        1. Revert back to Z-up.
        2. Temp solution for UE requested head and body are two separate assets.
        
        """
        # set rig back to Z-up
        for node in ['global_ctrl', 'headRig_grp', 'Lights']:
            Node(node).set_attr('rx', 0)

        # set scene back to Z-up
        cmds.upAxis(axis='z', rotateView=True)
        cmds.viewSet('persp', home=True )
        
        #
        for jnt_nm in ['root', 'pelvis', 'spine_01', 'spine_02', 'spine_03']:
            dup_bd_jnt = Node('DHIbody:' + jnt_nm).duplicate(
                        parentOnly=True, name=jnt_nm )[0]

            if dup_bd_jnt.name=='root':
                dup_bd_jnt.set_parent()
                self._root_jnt = dup_bd_jnt.name
            else:
                #dup_bd_jnt.set_parent(dup_jnts_ls[prnt_id])
                dup_bd_jnt.set_parent(parent_jnt)

            parent_jnt = dup_bd_jnt

            if dup_bd_jnt.name=='spine_03':
                head_root_jnt = Node('DHIhead:spine_04')
                head_root_jnt.set_parent(dup_bd_jnt)

        # strip from MHY nodes
        Node(const.RIGMESH_ROOT).delete()
        Node(const.MH_ROOT).set_parent('world')
        Node(const.RIG_ROOT).delete()


    def _export_rig(self):
        selection = self._head_meshes + [self._root_jnt]
        cmds.select(selection, r=True)
        
        mel.eval('FBXLoadExportPresetFile -f ' + '"{}"'.format(self._fbx_preset_path))
        cmds.file(
            self._export_path,
            exportSelected=True,
            type='FBX export',
            force=True
        )

