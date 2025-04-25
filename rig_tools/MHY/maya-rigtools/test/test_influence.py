import unittest

from maya import cmds

from mhy.maya.nodezoo.node import Node
import mhy.maya.rigtools.pose_editor.api.influence as influence
from mhy.maya.rig.utils import add_influence_tag_attribute


class TestInfluence(unittest.TestCase):
    """
    Test Influence setup
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)
        self.node = Node.create('script')

    def test_custom_influence_node(self):
        self.setUp()
        attr = add_influence_tag_attribute(self.node, {"script": {'before': "Test"}})

        self.assertEqual(attr,  influence.Influence.pose_driven_attr)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInfluence))
    unittest.TextTestRunner(failfast=True).run(suite)
