import os
import unittest

import mhy.python.core.compatible as compat
from mhy.protostar.lib import ActionLibrary as alib


class TestGameFace(unittest.TestCase):
    """
    Test in-game face builds
    """

    WORKAREA_PATH = os.environ.get('MHY_MAYA_TEST_WORKAREA')
    PROJECT_NAME = 'rigs'
    CHAR_NAME = 'game_face'

    def setUp(self):
        import mhy.maya.rig.joint_utils as jutil
        import mhy.maya.rig.base_limb as bl
        import mhy.maya.rig.face.blinkline_system as bls
        import mhy.maya.rig.face.curve_driver_system as cds
        import mhy.maya.rig.face.parameter_driver_system as pds
        import mhy.maya.rig.face.tracer as tracer
        import mhy.maya.rig.face.weighted_transform_system as wts
        compat.reload(jutil)
        compat.reload(bl)
        compat.reload(wts)
        compat.reload(bls)
        compat.reload(cds)
        compat.reload(pds)
        compat.reload(tracer)
        alib.refresh()

    def test_face_build(self):
        rig = alib.create_graph(name='test_gameface_limb')

        # --- make a new maya scene

        alib.create_action('mhy:NewMayaScene', name='new_scene', graph=rig)

        # --- config asset resource file path

        config = alib.create_action(
            'mhy:AssetConfig', name='asset_config', graph=rig)
        config.workarea_path.value = self.WORKAREA_PATH
        config.project_name.value = self.PROJECT_NAME
        config.char_name.value = self.CHAR_NAME
        config.rig_type.value = 'face'

        # --- import rig mesh

        mesh_graph = alib.create_graph(name='mesh_graph', graph=rig)
        root_path = mesh_graph.add_dynamic_param('dir', name='root_path')
        config.rigmesh_path >> root_path
        file_iter = mesh_graph.add_dynamic_param(
            'iter', item_type='str', name='file_name')
        file_iter.value = [
            'face.fbx',
            'eyes.fbx',
            # 'eyewater.fbx',
            # 'chew.fbx',
            'teethTongue.fbx']

        import_mesh = alib.create_action('mhy:ImportRigMesh', graph=mesh_graph)
        import_mesh.mesh_type.value = 'rigmesh'
        import_mesh.mesh_file.script = '{mesh_graph.root_path}/{mesh_graph.file_name}'

        # --- import rig skel

        skel = alib.create_action('mhy:ImportSkeleton', graph=rig)
        skel.file_path.script = '{asset_config.skel_path}/skeleton.fbx'

        # --- build motion system (limbs)

        world_offset = alib.create_action('mhy:WorldOffset', graph=rig)
        world_offset.input_skeleton.value = 'worldOffset_M_RIGJNT'

        face = alib.create_action('mhy:GameFace', graph=rig)
        face.part.value = 'face'
        face.face_mesh.value = 'Face'
        face.input_skeleton.value = 'face_root_00_M_RIGJNT'
        face.parent_joint.value = 'worldOffset_M_RIGJNT'
        face.set_parent_limb(world_offset)

        eye = alib.create_action('mhy:EyeWithAim', graph=rig)
        eye.part.value = 'eye'
        eye.face_mesh.value = 'Face'
        eye.input_skeleton.value = ('eye_00_L_RIGJNT', 'eye_00_R_RIGJNT')
        eye.parent_joint.value = 'face_root_00_M_RIGJNT'
        eye.set_parent_limb(face)

        # --- import ctrl shapes

        ctrl_import = alib.create_action('mhy:ImportCtrlShapes', graph=rig)
        config.ctrl_file >> ctrl_import.data_file

        # --- create bind skeleton

        alib.create_action('mhy:CreateBindSkeleton', graph=rig)

        # --- import deformers

        weights = alib.create_action('mhy:ImportDeformers', graph=rig)
        config.deformer_path >> weights.data_path

        # --- import pose data
        poses = alib.create_action('mhy:ImportPoseData', graph=rig)
        poses.build_anim_rig.value = True
        config.pose_path >> poses.data_path

        # driver_texture = alib.create_action('mhy:TextureDriver', graph=rig)
        # poses.created_pose_nodes >> driver_texture.pose_nodes
        # config.texture_driver_data_path >> driver_texture.shader_data_file
        # driver_texture.mesh_object.value = 'Face'

        # config.texture_driver_shader_data_path >> driver_texture.
        rig.execute()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestGameFace('test_face_build'))
    unittest.TextTestRunner(failfast=True).run(suite)
