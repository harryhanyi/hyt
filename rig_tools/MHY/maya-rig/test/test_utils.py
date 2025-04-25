import unittest

from maya import cmds

import mhy.maya.maya_math as math
from mhy.maya.nodezoo.node import Node
import mhy.maya.rig.utils as utils


class TestMathUtils(unittest.TestCase):
    """
    Test the math utility network setups
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)

        self.nodeA = Node.create('transform', name='nodeA')
        self.nodeB = Node.create('transform', name='nodeB')
        self.nodeA.set_attr('t', (1, 2, 3))
        self.nodeB.set_attr('t', (4, 5, 6))

    def test_sum(self):
        out = utils.create_sum(('nodeA.ty', 'nodeB.ty'), output_attr='nodeB.tz')
        self.assertEqual(out.value, 7)
        self.assertEqual(self.nodeB.get_attr('tz'), 7)

        u = utils.create_sum((self.nodeA.tx, self.nodeB.tx), output_attr='nodeB.tz')
        self.assertEqual(u.value, 5)
        self.assertEqual(self.nodeB.get_attr('tz'), 5)

    def test_connet_a(self):
        utils.xform_connect(self.nodeA, self.nodeB, extra_attrs='rotateOrder')
        self.assertEqual(self.nodeB.rotateOrder.value, self.nodeB.rotateOrder.value)
        self.assertTrue(self.nodeB.rotateOrder.locked)
        self.assertFalse(self.nodeB.ty.keyable)
        for attr in 'trs':
            for ax in 'xyz':
                at = attr + ax
                self.assertEqual(self.nodeB.attr(at).value, self.nodeA.attr(at).value)

    def test_connet_b(self):
        utils.xform_connect(self.nodeA, self.nodeB, inverse=True, attrs='r', lock=False)
        self.nodeA.r.value = (10, 20, 30)
        self.assertTrue(self.nodeB.ry.keyable)
        self.assertFalse(self.nodeB.ry.locked)
        for ax in 'xyz':
            self.assertEqual(self.nodeB.attr('r' + ax).value, -self.nodeA.attr('r' + ax).value)

    def test_condition(self):
        c = utils.create_condition(
            self.nodeA.tx, self.nodeB.tx, self.nodeA.ty, self.nodeB.ty, operation=2)
        self.assertEqual(c.value, self.nodeB.get_attr('ty'))

    def test_multiplyer(self):
        utils.create_multiplier(self.nodeA.tx, self.nodeB.tx, 2, offset=1)
        self.assertEqual(self.nodeB.tx.value, self.nodeA.tx.value * 2 + 1)

        utils.create_multiplier(self.nodeA.ty, self.nodeB.ty, 2, offset=-1, reverse=True)
        self.assertEqual(self.nodeB.ty.value, (1.0 - (1.0 - self.nodeA.ty.value) * 2) - 1)

        utils.create_multiplier(self.nodeA.ty, self.nodeB.ty, 2, reverse=True)
        self.assertEqual(self.nodeB.ty.value, 1.0 - (1.0 - self.nodeA.ty.value) * 2)

    def test_negation(self):
        self.nodeA.r.value = (10, 20, 30)
        self.nodeA.s.value = (7, 8, 9)
        utils.create_negation(self.nodeA, self.nodeB, attrs='trxrysz')
        self.assertAlmostEqual(self.nodeB.tx.value, -self.nodeA.tx.value)
        self.assertAlmostEqual(self.nodeB.ty.value, -self.nodeA.ty.value)
        self.assertAlmostEqual(self.nodeB.tz.value, -self.nodeA.tz.value)
        self.assertAlmostEqual(self.nodeB.rx.value, -self.nodeA.rx.value)
        self.assertAlmostEqual(self.nodeB.ry.value, -self.nodeA.ry.value)
        self.assertAlmostEqual(self.nodeB.rz.value, 0)
        self.assertAlmostEqual(self.nodeB.sx.value, 1)
        self.assertAlmostEqual(self.nodeB.sy.value, 1)
        self.assertAlmostEqual(self.nodeB.sz.value, 1.0 / self.nodeA.sz.value)

    def test_sdk(self):
        utils.set_driven_keys(self.nodeA.tx, self.nodeB.tx, [[3, 10], [5, 20]])
        self.nodeA.tx.value = 3
        self.assertAlmostEqual(self.nodeB.tx.value, 10)
        self.nodeA.tx.value = 5
        self.assertAlmostEqual(self.nodeB.tx.value, 20)


class TestCurveUtils(unittest.TestCase):
    """
    Test the curve utility functions
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)

        self.curve = Node.create(
            'nurbsCurve',
            [(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9), (12, 10, 2)],
            name='curve',
            degree=3)
        self.xform = self.curve.get_parent()

    def test_stretch_output_a(self):
        out = utils.create_curve_stretch_output(self.curve, as_ratio=True)
        lengthA = cmds.arclen(self.curve)
        cmds.xform('{}.cv[2]'.format(self.curve), ws=True, t=(30, 30, 30))
        lengthB = cmds.arclen(self.curve)
        self.assertAlmostEqual(out.value, lengthB / lengthA)

    def test_stretch_output_b(self):
        out = utils.create_curve_stretch_output(self.xform, as_ratio=False)
        lengthA = cmds.arclen(self.curve)
        cmds.xform('{}.cv[2]'.format(self.curve), ws=True, t=(30, 30, 30))
        lengthB = cmds.arclen(self.curve)
        self.assertAlmostEqual(out.value, lengthB - lengthA)


class TestJointUtils(unittest.TestCase):
    """
    Test the joint utility functions
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)

        self.jointA = Node.create('joint', name='part_00_L_JNT')
        self.jointB = Node.create('joint', name='part_01_L_JNT')
        self.jointC = Node.create('joint', name='part_02_L_JNT')
        # self.jointB.set_parent(self.jointA)
        # self.jointC.set_parent(self.jointB)
        self.jointA.set_translation((1, 2, 3), space='world')
        self.jointB.set_translation((4, 5, 6), space='world')
        self.jointC.set_translation((7, 8, 9), space='world')

    def test_stretchy(self):
        dist = math.distance(self.jointA, self.jointC)
        distB = math.distance(self.jointA, self.jointB)
        utils.create_stretchy_xforms((self.jointA, self.jointB, self.jointC))
        self.jointC.t = (10, 10, 10)
        self.assertAlmostEqual(distB / dist * self.jointC.tx.value, self.jointB.tx.value)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMathUtils))
    suite.addTest(unittest.makeSuite(TestCurveUtils))
    suite.addTest(unittest.makeSuite(TestJointUtils))
    unittest.TextTestRunner(failfast=True).run(suite)
