import unittest

from maya import cmds

import mhy.maya.maya_math as math
from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName

import mhy.maya.rig.node
import mhy.maya.rig.joint_utils as jutil


class TestMHYLimbRoot(unittest.TestCase):
    """
    Test the MHYLimbRoot node
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)

        self.root = Node.create('MHYLimbRoot', name='part_abc_00_L_JNT')
        self.xform = Node.create('transform', name='part_abc_00_L_JNT')

    def test_limb(self):
        self.assertEqual(self.root.name, 'part_abc_00_L_LIMB')
        self.assertEqual(self.root.shape, self.root.get_children()[0])
        self.root.add_instance(self.xform)
        self.assertEqual(self.xform.get_shapes(), self.root.get_children())


class TestMHYCtrl(unittest.TestCase):
    """
    Test the MHYCtrl and joint utils
    """

    def setUp(self):
        cmds.file(newFile=True, force=True)

        self.jointA = Node.create('joint', name='part_00_L_JNT')
        self.jointB = Node.create('joint', name='part_01_L_JNT')
        self.jointC = Node.create('joint', name='part_02_L_JNT')
        self.jointB.set_parent(self.jointA)
        self.jointC.set_parent(self.jointB)
        self.jointA.set_translation((1, 2, 3), space='world')
        self.jointB.set_translation((4, 5, 6), space='world')
        self.jointC.set_translation((7, 8, 9), space='world')
        self.jointA.orient_chain()
        jutil.update_label(self.jointA, draw=True)
        jutil.add_category(self.jointB, 'test_cat')

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip((v1[0], v1[1], v1[2]),
                              (v2[0], v2[1], v2[2])):
            self.assertAlmostEqual(val1, val2, 5)

    def test_joint(self):
        self.assertEqual(self.jointA.get_attr('side'), 1)
        self.assertEqual(self.jointA.get_attr('type'), 18)
        self.assertEqual(self.jointA.get_attr('otherType'), 'part')

        c = jutil.get_joints_in_category('test_cat')
        self.assertEqual(c, [self.jointB])

        jutil.add_category(self.jointB, ['a', 'b'])
        self.assertEqual(jutil.get_category(self.jointB), ['a', 'b', 'test_cat'])
        jutil.add_category(self.jointB, ['a', 'b'], replace=True)
        self.assertEqual(jutil.get_category(self.jointB), ['a', 'b'])
        jutil.replace_category(self.jointB, 'a', ['c', 'd'])
        self.assertEqual(jutil.get_category(self.jointB), ['b', 'c', 'd'])
        self.assertFalse(jutil.has_category(self.jointB, 'a'))

        plane = cmds.polyPlane(subdivisionsX=1, subdivisionsY=1, ch=False)[0]
        pos = tuple(cmds.xform('{}.vtx[0]'.format(plane), q=True, ws=True, t=True))
        self.jointC.set_translation(pos, space='world')
        jutil.set_position_tag(self.jointC, plane)
        self.assertEqual(self.jointC.attr(jutil.TAG_POSITION).value, 'vtx[0]')
        self.jointC.set_translation((5, 5, 5), space='world')
        jutil.snap_to_position_tag(self.jointC, plane)
        self.assertVectorEqual(self.jointC.get_translation(space='world'), pos)

        m_joint = jutil.mirror_joint(self.jointC)
        self.assertEqual(m_joint.name, NodeName(self.jointC).flip())

    def test_ctrl(self):
        ctrl = Node.create(
            'MHYCtrl', name='a_02_R_IKCTRL', shape=9999,
            pos=(2, 2, 2), rot=(0, 10, 0), scale=(3, 3, 3))
        self.assertEqual(ctrl.api_type_str, "MHYCtrl")
        self.assertEqual(ctrl.name, 'a_02_R_IKCTRL')
        self.assertEqual(ctrl.type_name, 'transform')
        self.assertEqual(ctrl.custom_type_name, 'MHYCtrl')
        self.assertVectorEqual(ctrl.plc_node.get_translation(), (0, 0, 0))
        self.assertVectorEqual(ctrl.plc_node.get_attr('r'), (0, 0, 0))
        self.assertVectorEqual(ctrl.shape.shape_color, (1, 0, 0))
        self.assertVectorEqual(ctrl.shape.local_position, (2, 2, 2))
        self.assertVectorEqual(ctrl.shape.local_rotate, (0, 10, 0))
        self.assertVectorEqual(ctrl.shape.local_scale, (3, 3, 3))
        self.assertEqual(ctrl.target, None)

        prefix = self.jointA.name.replace('JNT', '')
        ctrl = Node.create(
            'MHYCtrl', name=None, xform=self.jointA, ext='CTRL', rot_order='yzx', shape='square')
        self.assertEqual(ctrl.shape.shape_type, 'square')
        self.assertEqual(ctrl.name, prefix + 'CTRL')
        self.assertVectorEqual(ctrl.get_translation(space='world'), (1, 2, 3))
        self.assertVectorEqual(ctrl.get_attr('r'), (0, 0, 0))
        self.assertVectorEqual(ctrl.shape.shape_color, (0, 0, 1))
        self.assertEqual(ctrl.get_attr('rotateOrder'), 1)
        self.assertEqual(ctrl.shape, ctrl.get_shapes()[0])
        self.assertEqual(ctrl.get_parent().name, prefix + 'OFFSET')
        self.assertEqual(ctrl.get_parent(level=2).name, prefix + 'SDK')
        self.assertEqual(ctrl.get_parent(level=3), ctrl.plc_node)
        self.assertEqual(ctrl.get_parent(), ctrl.get_group('OFFSET'), ctrl.offset_node)
        self.assertEqual(ctrl.get_parent(level=2), ctrl.get_group('SDK'), ctrl.sdk_node)
        self.assertEqual(ctrl.get_parent(level=3), ctrl.get_group('PLC'), ctrl.plc_node)
        self.assertEqual(ctrl.target, self.jointA)

    def test_joint_chain(self):
        chain = jutil.JointChain(self.jointA, end=self.jointC)
        self.assertTrue(self.jointB in chain)
        self.assertEqual(chain.long_axis, 'X')
        self.assertEqual(len(chain), 3)
        self.assertEqual(self.jointA, chain[0])
        self.assertEqual(self.jointB, chain[1])
        self.assertAlmostEqual(
            chain.chain_length,
            math.distance(self.jointA, self.jointB) + math.distance(self.jointC, self.jointB))

        chain.set_rotate_order('yzx')
        self.assertEqual(self.jointB.get_attr('rotateOrder'), 1)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMHYLimbRoot))
    suite.addTest(unittest.makeSuite(TestMHYCtrl))
    unittest.TextTestRunner(failfast=True).run(suite)
