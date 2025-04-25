import os
import unittest
from parameterized import parameterized, parameterized_class

import mhy.python.core.compatible as compat
from mhy.protostar.lib import ActionLibrary as alib


def _class_name_func(cls, _, params_dict):
    """Returns parameterized TestCase class name."""
    return '{}_{}'.format(
        cls.__name__,
        parameterized.to_safe_name(params_dict['name']))


def _method_name_func(func, _, param):
    """Returns parameterized TestCase method name."""
    return '{}_{}'.format(
        func.__name__,
        parameterized.to_safe_name(param.args[0]))


@parameterized_class([
    {'name': 'marker_sys', 'use_skel': False},
    {'name': 'input_skel', 'use_skel': True},
], class_name_func=_class_name_func)
class TestLimbs(unittest.TestCase):
    """
    Test limb builds
    """

    WORKAREA_PATH = os.environ.get('MHY_MAYA_TEST_WORKAREA')
    PROJECT_NAME = 'rigs'
    CHAR_NAME = 'biped'

    def setUp(self):
        import mhy.maya.rig.constants as const
        import mhy.maya.rig.utils as utils
        import mhy.maya.rig.data as data
        import mhy.maya.rig.marker_system as marker
        import mhy.maya.rig.base_limb as bl
        compat.reload(const)
        compat.reload(data)
        compat.reload(utils)
        compat.reload(marker)
        compat.reload(bl)
        alib.refresh()

        self.rig = alib.create_graph(name='test_rig')

        alib.create_action('mhy:NewMayaScene', name='new_scene', graph=self.rig)

        self.config = alib.create_action(
            'mhy:AssetConfig', name='asset_config', graph=self.rig)
        self.config.workarea_path.value = self.WORKAREA_PATH
        self.config.project_name.value = self.PROJECT_NAME
        self.config.char_name.value = self.CHAR_NAME

        if self.use_skel:
            self.skel_import = alib.create_action(
                'mhy:ImportSkeleton', name='skel_import', graph=self.rig)
            self.skel_import.file_path.script = '{asset_config.skel_path}/skeleton.fbx'
        else:
            marker_import = alib.create_action(
                'mhy:ImportMarkerSystem', name='marker_system', graph=self.rig)
            self.config.marker_file >> marker_import.data_file

        self.world_offset = alib.create_action('mhy:WorldOffset', graph=self.rig)
        if self.use_skel:
            self.world_offset.input_skeleton.value = 'worldOffset_M_RIGJNT'

    def execute(self):
        ctrl_import = alib.create_action('mhy:ImportCtrlShapes', graph=self.rig)
        self.config.ctrl_file >> ctrl_import.data_file

        self.rig.execute()

    def test_fk_limb(self):
        limb = alib.create_action('mhy:FKLimb', graph=self.rig)
        limb.part.value = 'fk'
        limb.num_joints.value = 4
        limb.enable_scale.value = True
        limb.set_parent_limb(self.world_offset)

        if self.use_skel:
            limb.input_skeleton.value = ('spine_01_M_RIGJNT', 'spine_05_M_RIGJNT')
            limb.parent_joint.value = 'worldOffset_M_RIGJNT'

        self.execute()

    def test_fk_hier_limb(self):
        if not self.use_skel:
            return

        limb = alib.create_action('mhy:FKHierarchy', graph=self.rig)
        limb.part.value = 'fk'
        limb.enable_scale.value = True
        limb.set_parent_limb(self.world_offset)

        limb.input_skeleton.value = 'spine_01_M_RIGJNT'
        limb.parent_joint.value = 'worldOffset_M_RIGJNT'

        self.execute()

    def test_neck_limb(self):
        limb = alib.create_action('mhy:NeckHead', graph=self.rig)
        limb.part.value = 'neck'
        limb.set_parent_limb(self.world_offset)

        if self.use_skel:
            limb.input_skeleton.value = ('neck_00_M_RIGJNT', 'head_M_RIGJNT')
            limb.parent_joint.value = 'worldOffset_M_RIGJNT'

        self.execute()

    @parameterized.expand([
        ['Spline'],
        ['FK'],
        ['SingleFKIK'],
    ], name_func=_method_name_func)
    def test_spine_limb(self, name):
        hip = alib.create_action('mhy:Hip', graph=self.rig)
        hip.part.value = 'hip'
        hip.set_parent_limb(self.world_offset)

        limb = alib.create_action('mhy:{}Spine'.format(name), graph=self.rig)
        limb.part.value = 'spine'
        limb.set_parent_limb(hip)

        if self.use_skel:
            hip.input_skeleton.value = 'hip_M_RIGJNT'
            hip.parent_joint.value = 'worldOffset_M_RIGJNT'
            limb.input_skeleton.value = ('spine_00_M_RIGJNT', 'spine_05_M_RIGJNT')
            limb.parent_joint.value = 'hip_M_RIGJNT'

        self.execute()

    @parameterized.expand([
        ['DJIKFK'],
        ['IKFK'],
    ], name_func=_method_name_func)
    def test_leg_limb(self, name):
        if self.use_skel and name == 'DJIKFK':
            self.skel_import.file_path.script = '{asset_config.skel_path}/skeletonDJ.fbx'

        hip = alib.create_action('mhy:Hip', graph=self.rig)
        hip.part.value = 'hip'
        hip.set_parent_limb(self.world_offset)

        limb = alib.create_action('mhy:{}Leg'.format(name), graph=self.rig)
        limb.part.value = 'leg'
        limb.mirror.value = True
        limb.set_parent_limb(hip)

        if self.use_skel:
            hip.input_skeleton.value = 'hip_M_RIGJNT'
            hip.parent_joint.value = 'worldOffset_M_RIGJNT'
            limb.input_skeleton.value = ('leg_hip_L_RIGJNT', 'leg_ankle_L_RIGJNT')
            limb.parent_joint.value = 'hip_M_RIGJNT'

        self.execute()

    def test_foot_limb(self):
        leg = alib.create_action('mhy:IKFKLeg', graph=self.rig)
        leg.part.value = 'leg'
        leg.mirror.value = True
        leg.set_parent_limb(self.world_offset)

        limb = alib.create_action('mhy:IKFKFoot', graph=self.rig)
        limb.part.value = 'foot'
        limb.side.value = 'L'
        limb.mirror.value = True
        limb.set_parent_limb(leg)

        if self.use_skel:
            leg.input_skeleton.value = ('leg_hip_L_RIGJNT', 'leg_ankle_L_RIGJNT')
            leg.parent_joint.value = 'worldOffset_M_RIGJNT'
            limb.input_skeleton.value = ('foot_ankle_L_RIGJNT', 'foot_toe_L_RIGJNT')
            limb.parent_joint.value = 'leg_ankle_L_RIGJNT'

        self.execute()

    @parameterized.expand([
        ['DJIKFK'],
        ['IKFK'],
    ], name_func=_method_name_func)
    def test_arm_limb(self, name):
        if self.use_skel and name == 'DJIKFK':
            self.skel_import.file_path.script = '{asset_config.skel_path}/skeletonDJ.fbx'

        clavicle = alib.create_action(
            'mhy:IKFKClavicle', name='l_clavicle', graph=self.rig)
        clavicle.part.value = 'clavicle'
        clavicle.mirror.value = True
        clavicle.set_parent_limb(self.world_offset)

        limb = alib.create_action('mhy:{}Arm'.format(name), graph=self.rig)
        limb.part.value = 'arm'
        limb.mirror.value = True
        limb.set_parent_limb(clavicle)

        if self.use_skel:
            clavicle.input_skeleton.value = ('clavicle_L_RIGJNT', 'clavicle_end_L_RIGJNT')
            clavicle.parent_joint.value = 'worldOffset_M_RIGJNT'
            limb.input_skeleton.value = ('arm_shldr_L_RIGJNT', 'arm_wrist_L_RIGJNT')
            limb.parent_joint.value = 'clavicle_end_L_RIGJNT'

        self.execute()

    def test_hand_limb(self):
        arm = alib.create_action('mhy:IKFKArm', graph=self.rig)
        arm.part.value = 'arm'
        arm.mirror.value = True
        arm.set_parent_limb(self.world_offset)

        limb = alib.create_action('mhy:Hand', graph=self.rig)
        limb.part.value = 'hand'
        limb.mirror.value = True
        limb.set_parent_limb(arm)

        if self.use_skel:
            arm.input_skeleton.value = ('arm_shldr_L_RIGJNT', 'arm_wrist_L_RIGJNT')
            arm.parent_joint.value = 'worldOffset_M_RIGJNT'
            limb.input_skeleton.value = 'hand_L_RIGJNT'
            limb.parent_joint.value = 'arm_wrist_L_RIGJNT'

        self.execute()


if __name__ == '__main__':
    suite = unittest.TestSuite()

    # suite.addTest(TestLimbs_marker_sys('test_fk_limb'))
    suite.addTest(TestLimbs_marker_sys('test_neck_limb'))
    # suite.addTest(TestLimbs_marker_sys('test_spine_limb_Spline'))
    # suite.addTest(TestLimbs_marker_sys('test_spine_limb_FK'))
    # suite.addTest(TestLimbs_marker_sys('test_spine_limb_SingleFKIK'))
    # suite.addTest(TestLimbs_marker_sys('test_leg_limb_DJIKFK'))
    # suite.addTest(TestLimbs_marker_sys('test_leg_limb_IKFK'))
    # suite.addTest(TestLimbs_marker_sys('test_foot_limb'))
    # suite.addTest(TestLimbs_marker_sys('test_arm_limb_DJIKFK'))
    # suite.addTest(TestLimbs_marker_sys('test_arm_limb_IKFK'))
    # suite.addTest(TestLimbs_marker_sys('test_hand_limb'))

    # suite.addTest(TestLimbs_input_skel('test_fk_hier_limb'))
    # suite.addTest(TestLimbs_input_skel('test_fk_limb'))
    # suite.addTest(TestLimbs_input_skel('test_neck_limb'))
    # suite.addTest(TestLimbs_input_skel('test_spine_limb_Spline'))
    # suite.addTest(TestLimbs_input_skel('test_spine_limb_FK'))
    # suite.addTest(TestLimbs_input_skel('test_spine_limb_SingleFKIK'))
    # suite.addTest(TestLimbs_input_skel('test_leg_limb_DJIKFK'))
    # suite.addTest(TestLimbs_input_skel('test_leg_limb_IKFK'))
    # suite.addTest(TestLimbs_input_skel('test_foot_limb'))
    # suite.addTest(TestLimbs_input_skel('test_arm_limb_DJIKFK'))
    # suite.addTest(TestLimbs_input_skel('test_arm_limb_IKFK'))
    # suite.addTest(TestLimbs_input_skel('test_hand_limb'))

    unittest.TextTestRunner(failfast=True).run(suite)
