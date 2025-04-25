import unittest

from maya import cmds

from mhy.maya.nodezoo.node import Node


class TestDagNode(unittest.TestCase):
    """
    Test Dag
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)
        cmds.polySphere(name='mesh', ch=False)
        self.mesh = Node('meshShape')

    def test_is_hidden(self):
        self.assertFalse(self.mesh.is_hidden())

        parent = self.mesh.get_parent()
        parent = Node(cmds.group(parent))
        parent.hide()
        self.assertTrue(self.mesh.is_hidden())

    def test_add_attr(self):
        attr = self.mesh.add_attr(
            'bool', name='test', keyable=False, lock=True, channelBox=True)
        self.assertTrue(attr.locked)
        self.assertTrue(attr.channelBox)
        self.assertFalse(attr.keyable)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDagNode))
    unittest.TextTestRunner(failfast=True).run(suite)
