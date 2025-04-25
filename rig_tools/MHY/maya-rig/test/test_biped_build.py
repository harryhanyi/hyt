import os
import unittest
from parameterized import parameterized, parameterized_class

import mhy.python.core.compatible as compat
from mhy.protostar.lib import ActionLibrary as alib


"""
Temp rig limb(motion system) hierarchy switch:
    + "flat": all limbs parented under world offset.
    + "nested": each limb is parented under its parent's ctrl_leaf.
"""
os.environ['MHY_RIG_HIER'] = 'flat'


def _class_name_func(cls, _, params_dict):
    """Returns parameterized TestCase class name."""
    return '{}_{}'.format(
        cls.__name__,
        parameterized.to_safe_name(params_dict['name']))


@parameterized_class([
    {'name': 'marker_sys', 'use_skel': False},
    {'name': 'input_skel', 'use_skel': True},
], class_name_func=_class_name_func)
class TestBiped(unittest.TestCase):
    """
    Test limb builds
    """

    WORKAREA_PATH = os.environ.get('MHY_MAYA_TEST_WORKAREA')
    PROJECT_NAME = 'rigs'
    CHAR_NAME = 'biped'

    def setUp(self):
        import mhy.maya.rig.data as data
        import mhy.maya.rig.utils as utils
        import mhy.maya.rig.joint_utils as jutil
        import mhy.maya.rig.marker_system as marker
        import mhy.maya.rig.base_limb as bl
        compat.reload(data)
        compat.reload(utils)
        compat.reload(jutil)
        compat.reload(marker)
        compat.reload(bl)
        alib.refresh()

    def test_biped_build(self):
        rig = alib.create_graph(name='test_biped')

        # --- make a new maya scene

        alib.create_action('mhy:NewMayaScene', name='new_scene', graph=rig)

        # --- config asset resource file path

        config = alib.create_action(
            'mhy:AssetConfig', name='asset_config', graph=rig)
        config.workarea_path.value = self.WORKAREA_PATH
        config.project_name.value = self.PROJECT_NAME
        config.char_name.value = self.CHAR_NAME

        # --- build marker system or import pre-built skeleton

        if self.use_skel:
            skel_import = alib.create_action(
                'mhy:ImportSkeleton', name='skel_import', graph=rig)
            skel_import.file_path.script = '{asset_config.skel_path}/skeleton.fbx'
        else:
            marker_import = alib.create_action(
                'mhy:ImportMarkerSystem', name='marker_system', graph=rig)
            config.marker_file >> marker_import.data_file

        # --- build motion system (limbs)

        world_offset = alib.create_action(
            'mhy:WorldOffset', name='world_offset', graph=rig)
        if self.use_skel:
            world_offset.input_skeleton.value = 'worldOffset_M_RIGJNT'

        hip = alib.create_action('mhy:Hip', graph=rig, name='hip')
        hip.part.value = 'hip'
        hip.set_parent_limb(world_offset)
        if self.use_skel:
            hip.input_skeleton.value = 'hip_M_RIGJNT'
            hip.parent_joint.value = 'worldOffset_M_RIGJNT'

        spine = alib.create_action('mhy:SingleFKIKSpine', name='spine', graph=rig)
        spine.part.value = 'spine'
        spine.set_parent_limb(hip)
        if self.use_skel:
            spine.input_skeleton.value = ('spine_00_M_RIGJNT', 'spine_05_M_RIGJNT')
            spine.parent_joint.value = 'hip_M_RIGJNT'

        breath = alib.create_action('mhy:Breath', graph=rig)
        breath.part.value = 'breath'
        breath.set_parent_limb(spine)
        if self.use_skel:
            breath.input_skeleton.value = 'breath_M_RIGJNT'
            breath.parent_joint.value = 'spine_05_M_RIGJNT'

        clavicle = alib.create_action('mhy:IKFKClavicle', name='l_clavicle', graph=rig)
        clavicle.part.value = 'clavicle'
        clavicle.mirror.value = True
        clavicle.set_parent_limb(spine)
        if self.use_skel:
            clavicle.input_skeleton.value = ('clavicle_L_RIGJNT', 'clavicle_end_L_RIGJNT')
            clavicle.parent_joint.value = 'spine_05_M_RIGJNT'

        arm = alib.create_action('mhy:IKFKArm', name='l_arm', graph=rig)
        arm.part.value = 'arm'
        arm.side.value = 'L'
        arm.mirror.value = True
        arm.set_parent_limb(clavicle)
        if self.use_skel:
            arm.input_skeleton.value = ('arm_shldr_L_RIGJNT', 'arm_wrist_L_RIGJNT')
            arm.parent_joint.value = 'clavicle_end_L_RIGJNT'

        leg = alib.create_action('mhy:IKFKLeg', graph=rig)
        leg.part.value = 'leg'
        leg.side.value = 'L'
        leg.mirror.value = True
        leg.set_parent_limb(hip)
        if self.use_skel:
            leg.input_skeleton.value = ('leg_hip_L_RIGJNT', 'leg_ankle_L_RIGJNT')
            leg.parent_joint.value = 'hip_M_RIGJNT'

        foot = alib.create_action('mhy:IKFKFoot', graph=rig)
        foot.part.value = 'foot'
        foot.side.value = 'L'
        foot.mirror.value = True
        foot.set_parent_limb(leg)
        if self.use_skel:
            foot.input_skeleton.value = ('foot_ankle_L_RIGJNT', 'foot_toe_L_RIGJNT')
            foot.parent_joint.value = 'leg_ankle_L_RIGJNT'

        hand = alib.create_action('mhy:Hand', name='l_hand', graph=rig)
        hand.part.value = 'hand'
        hand.side.value = 'L'
        hand.mirror.value = True
        hand.set_parent_limb(arm)
        if self.use_skel:
            hand.input_skeleton.value = 'hand_L_RIGJNT'
            hand.parent_joint.value = 'arm_wrist_L_RIGJNT'

        neck = alib.create_action('mhy:NeckHead', graph=rig)
        neck.part.value = 'neck'
        neck.set_parent_limb(spine)
        if self.use_skel:
            neck.input_skeleton.value = ('neck_00_M_RIGJNT', 'head_M_RIGJNT')
            neck.parent_joint.value = 'spine_05_M_RIGJNT'

        # --- import ctrl shapes

        ctrl_import = alib.create_action('mhy:ImportCtrlShapes', graph=rig)
        config.ctrl_file >> ctrl_import.data_file

        # --- create bind skeleton

        alib.create_action('mhy:CreateBindSkeleton', graph=rig)

        # --- import mesh and deformation system

        mesh_import = alib.create_action('mhy:ImportRigMesh', graph=rig)
        mesh_import.mesh_type.value = 'cutmesh'
        mesh_import.mesh_file.script = '{asset_config.rigmesh_path}/cutmesh2.fbx'

        deformer_import = alib.create_action('mhy:ImportDeformers', graph=rig)
        deformer_import.import_method.value = 'vertexId'
        config.deformer_path >> deformer_import.data_path

        picker_import = alib.create_action('mhy:ImportPickerData', graph=rig)
        config.picker_path >> picker_import.data_path
        # this action runs various operations to clean up a rig.
        #
        # consider disabling it while working on the rig, as it locks nodes
        # and hides channelbox histories which makes debugging difficult.
        #
        # make sure to enable it when the rig is complete and ready for release.
        clean_up = alib.create_action('mhy:RigCleanUp', graph=rig)
        clean_up.clean_marker.value = False
        clean_up.lock_transforms.value = False
        clean_up.clean_channelbox_history.value = False

        rig.execute()
        # rig.execute(mode='step')


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestBiped_marker_sys('test_biped_build'))
    # suite.addTest(TestBiped_input_skel('test_biped_build'))
    unittest.TextTestRunner(failfast=True).run(suite)
