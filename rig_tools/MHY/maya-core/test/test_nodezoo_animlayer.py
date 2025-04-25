import unittest

from maya import cmds

from mhy.maya.nodezoo.node import Node
import mhy.maya.scene as sutil


class TestAnimLayer(unittest.TestCase):
    """
    Test the AnimLayer class
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.nodeA = Node.create('transform', name='nodeA')
        self.nodeB = Node.create('joint', name='nodeB')
        self.nodeC = Node.create('transform', name='nodeC')

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip(v1, v2):
            self.assertAlmostEqual(val1, val2, 4)

    def test_basic_property(self):
        self.setup()

        self.assertEqual(sutil.get_anim_layers(), [])

        layer_a = Node.create('animLayer', name='a')
        self.assertFalse(layer_a.is_base_layer)

        base_layer = layer_a.get_base_layer()
        self.assertEqual(base_layer.name, 'BaseAnimation')

        layer_b = Node.create('animLayer', name='b')
        self.assertFalse(layer_b.is_base_layer)

        self.assertEqual(
            sutil.get_anim_layers(include_base=True),
            [base_layer, layer_a, layer_b])

        layer_a.name = 'aaa'
        self.assertEqual(layer_a.name, 'aaa')
        base_layer.name = 'ccc'
        self.assertEqual(base_layer.name, 'ccc')

        self.assertEqual(
            base_layer.get_children(recursive=True),
            [layer_a, layer_b])
        self.assertEqual(
            base_layer.get_children(recursive=False),
            [layer_a, layer_b])
        self.assertEqual(
            layer_a.get_children(recursive=False), [])

        self.assertEqual(layer_a.get_parent(), base_layer)
        self.assertEqual(layer_b.get_parent(), base_layer)

        layer_a.isolate()
        self.assertTrue(layer_a.preferred.value)
        self.assertFalse(layer_b.preferred.value)
        self.assertFalse(base_layer.solo.value)

    def test_membership(self):
        self.setup()

        layer = Node.create('animLayer', name='a')
        self.assertEqual(layer.members, [])
        self.assertEqual(layer.get_attributes(), [])

        layer.add_member(self.nodeA)
        layer.add_member(self.nodeB)
        self.assertEqual(layer.members, [self.nodeA, self.nodeB])
        attrs = layer.get_attributes()

        for attr in 'trsv':
            if attr == 'v':
                self.assertTrue(self.nodeA.attr(attr) in attrs)
                continue

            for ax in 'xyz':
                a = attr + ax
                self.assertTrue(self.nodeA.attr(a) in attrs)

        layer.remove_member(self.nodeA)
        attrs = layer.get_attributes()

        for attr in 'trsv':
            if attr == 'v':
                self.assertFalse(self.nodeA.attr(attr) in attrs)
                self.assertTrue(self.nodeB.attr(attr) in attrs)
                continue

            for ax in 'xyz':
                a = attr + ax
                self.assertFalse(self.nodeA.attr(a) in attrs)
                self.assertTrue(self.nodeB.attr(a) in attrs)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAnimLayer))
    unittest.TextTestRunner(failfast=True).run(suite)
