import os
import unittest

import mhy.python.core.compatible as compat
from mhy.protostar.lib import ActionLibrary as alib


class TestHiFace(unittest.TestCase):
    """
    Test limb builds
    """

    WORKAREA_PATH = os.environ.get('MHY_MAYA_TEST_WORKAREA')
    PROJECT_NAME = 'rigs'
    CHAR_NAME = 'hi_face'

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

    def test_hiface_build(self):
        rig = alib.create_graph(name='test_hiface_limb')

        alib.create_action('mhy:NewMayaScene', name='new_scene', graph=rig)

        config = alib.create_action(
            'mhy:AssetConfig', name='asset_config', graph=rig)
        config.workarea_path.value = self.WORKAREA_PATH
        config.project_name.value = self.PROJECT_NAME
        config.char_name.value = self.CHAR_NAME
        config.rig_type.value = 'face'

        skel = alib.create_action('mhy:ImportSkeleton', graph=rig)
        skel.file_path.script = '{asset_config.skel_path}/skeleton.fbx'
        skel.add_category.value = True

        pd_skel = alib.create_action('mhy:ImportSkeleton', graph=rig)
        pd_skel.file_path.script = '{asset_config.skel_path}/poseDriver_skeleton.fbx'
        pd_skel.add_category.value = True

        face_mesh = alib.create_action('mhy:ImportRigMesh', graph=rig)
        face_mesh.mesh_type.value = 'rigmesh'
        face_mesh.mesh_file.script = '{asset_config.rigmesh_path}/Face.fbx'

        eye_mesh = alib.create_action('mhy:ImportRigMesh', graph=rig)
        eye_mesh.mesh_type.value = 'rigmesh'
        eye_mesh.mesh_file.script = '{asset_config.rigmesh_path}/Eyes.fbx'

        pds_skulls = alib.create_action('mhy:ImportRigMesh', graph=rig)
        pds_skulls.mesh_type.value = 'param_patch'
        pds_skulls.vis.value = False
        pds_skulls.mesh_file.script = '{asset_config.rigmesh_path}/pds_skulls.fbx'

        world_offset = alib.create_action('mhy:WorldOffset', graph=rig)

        face = alib.create_action('mhy:HiFace', graph=rig)
        face.part.value = 'face'
        face.input_skeleton.value = 'face_root_00_M_JNT'
        face.is_pose_rig.value = True
        face.set_parent_limb(world_offset)

        pose_driver = alib.create_action('mhy:PoseDriver', graph=rig)
        pose_driver.part.value = 'posedriver'
        pose_driver.base_mesh.value = 'Face'
        pose_driver.input_skeleton.value = 'poseDriver_root_00_M_JNT'
        pose_driver.set_parent_limb(world_offset)

        eye = alib.create_action('mhy:EyeWithAim', graph=rig)
        eye.part.value = 'eye'
        eye.input_skeleton.value = ('eye_main_00_L_JNT', 'eye_main_00_R_JNT')
        eye.set_parent_limb(world_offset)

        weights = alib.create_action('mhy:ImportDeformers', graph=rig)
        config.deformer_path >> weights.data_path
        
        wts_weights = alib.create_action('mhy:ImportDeformers', graph=rig)
        config.wts_deformer_path >> wts_weights.data_path
        
        ctrl_import = alib.create_action('mhy:ImportCtrlShapes', graph=rig)
        config.ctrl_file >> ctrl_import.data_file

        rig.execute()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestHiFace('test_hiface_build'))
    unittest.TextTestRunner(failfast=True).run(suite)
