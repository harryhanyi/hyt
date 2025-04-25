import unittest
from maya import cmds
from mhy.maya.nodezoo.node import Node
import mhy.maya.rigtools.pose_editor.api.pose_controller as pose_controller
from mhy.maya.rig.utils import add_influence_tag_attribute
from mhy.maya.rigtools.pose_editor.api.influence import get_influence_names

class TestPose(unittest.TestCase):
    """
    Test Influence setup
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)
        self.mesh = cmds.polyCube(name='testCube', ch=False)[0]
        self.pc = pose_controller.PoseController.create(name='test_pose', out_mesh=self.mesh)
        self.l_pose = self.pc.add_pose('test_pose_L')
        self.r_pose = self.pc.add_pose('test_pose_R')

    def test_pose_influence(self):
        self.setUp()
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]

        add_influence_tag_attribute(loc1)
        add_influence_tag_attribute(loc2)

        self.l_pose.add_influence(loc1)

        # Test using selection
        cmds.select([loc1, loc2])
        sel = get_influence_names()
        self.l_pose.add_influences(sel)
        self.r_pose.add_influence(loc2)

        self.assertEqual(len(self.l_pose.influences), 2)
        self.assertEqual(len(self.r_pose.influences), 1)

        self.l_pose.delete_influence(loc2)
        self.assertEqual(len(self.l_pose.influences), 1)

        # Check refresh cache
        self.l_pose.refresh_cache(False)
        self.assertEqual(len(self.l_pose.influences), 1)

        self.l_pose.add_neutral_key()
        self.l_pose.weight = 10
        Node(loc1).ty.value = 10
        Node(loc1).rx.value = 30
        self.l_pose.add_key()

        self.l_pose.weight = 5
        self.assertAlmostEqual(Node(loc1).ty.value, 5, delta=0.1)
        self.assertAlmostEqual(Node(loc1).rx.value, 15, delta=0.1)

        # Test rename
        new_name = 'New_name_M'
        self.l_pose.name = new_name

        alias = cmds.aliasAttr(self.l_pose.output_attribute_full_name, query=True)
        self.assertEqual(alias, new_name)

        data = self.pc.get_data()
        self.pc.reset()

        self.pc.set_data(data)

        pose = self.pc.find_pose(new_name)
        self.assertTrue(pose)
        pose.weight = 5
        self.assertAlmostEqual(Node(loc1).ty.value, 5, delta=0.1)
        self.assertAlmostEqual(Node(loc1).rx.value, 15, delta=0.1)

    def test_multiple_pc(self):
        self.setUp()
        self.pc2 = pose_controller.PoseController.create(name='test_pose2', out_mesh=self.mesh)
        self.l_pose2 = self.pc.add_pose('test_pose_L')
        self.r_pose2 = self.pc.add_pose('test_pose_R')


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPose))
    unittest.TextTestRunner(failfast=True).run(suite)
