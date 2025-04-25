import unittest

from maya import cmds

from mhy.maya.nodezoo.node import Node
import mhy.maya.maya_math as math


class TestMath(unittest.TestCase):
    """
    Test math utils.
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.nodeA = Node.create('transform', name='nodeA')
        self.nodeB = Node.create('joint', name='nodeB')
        self.nodeC = Node.create('transform', name='nodeC')
        self.mesh_xform = Node(cmds.polySphere(name='mesh', ch=False)[0])
        self.mesh = self.mesh_xform.get_shapes()[0]
        self.nodeB.set_parent(self.nodeA)
        self.nodeC.set_parent(self.nodeB)
        self.mesh_xform.set_parent(self.nodeC)
        self.nodeB.set_translation((1, 2, 3))
        self.nodeC.set_translation((3, 3, 3))

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip((v1[0], v1[1], v1[2]),
                              (v2[0], v2[1], v2[2])):
            self.assertAlmostEqual(val1, val2, 5)

    def test_distance(self):
        self.setup()

        dist = math.distance(self.nodeA, self.nodeC)
        self.assertAlmostEqual(dist, 8.774964387392122)
        t = self.nodeC.get_translation(space='world', as_tuple=True)
        self.assertAlmostEqual(math.distance(self.nodeA, t), dist)
        t = self.nodeC.get_translation(space='world', as_tuple=False)
        self.assertAlmostEqual(math.distance(self.nodeA, t), dist)
        self.assertAlmostEqual(math.distance(self.nodeA, self.nodeC.long_name), dist)

        p = math.intersect_line(
            (0, 1, 0), (1, 1, 0),
            (2, 0, 0), (2, 5, 0))
        self.assertVectorEqual(p, (2, 1, 0))
        p = math.intersect_line(
            (0, 1, 0), (1, 1, 0),
            (0, 2, 0), (2, 2, 0))
        self.assertEqual(p, None)

    def test_transform(self):
        self.setup()

        posA = self.nodeA.get_translation(space='world', as_tuple=False)
        posC = self.nodeC.get_translation(space='world', as_tuple=False)
        pos = math.get_fractional_position(posA, posC, fraction=.2, as_tuple=False)
        self.assertVectorEqual((posC - posA) * .2, (pos - posA))

        c1 = math.get_position_center((posA, posC))
        c2 = math.get_fractional_position(posA, posC, fraction=.5)
        self.assertVectorEqual(c1, c2)

        self.assertVectorEqual(math.get_bbx_center(self.nodeA), (4, 5, 6))
        self.assertVectorEqual(math.get_object_center(self.nodeA, bbx=True), (4, 5, 6))
        self.assertVectorEqual(math.get_object_center(self.nodeB, bbx=False), (1, 2, 3))

        self.assertEqual(
            self.nodeC,
            math.get_closest_transform((7, 8, 9), (self.nodeC, self.nodeA, self.nodeB)))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMath))
    unittest.TextTestRunner(failfast=True).run(suite)
