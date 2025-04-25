import unittest

from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node
import mhy.maya.maya_math as math


class TestTransform(unittest.TestCase):
    """
    Test DG, DAG, and transfrom
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.node = Node.create('transform', name='node')
        self.nodeA = Node.create('transform', name='nodeA')
        self.nodeB = Node.create('joint', name='nodeB')
        self.nodeC = Node.create('transform', name='nodeC')
        self.nodeC.help(verbose=True)  # Test help doc inspect
        self.mesh_xform = Node(cmds.polySphere(name='mesh', ch=False)[0])
        self.mesh = self.mesh_xform.get_shapes()[0]
        self.nodeB.set_parent(self.nodeA)
        self.nodeC.set_parent(self.nodeB)
        self.mesh_xform.set_parent(self.nodeC)

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip(v1, v2):
            self.assertAlmostEqual(val1, val2, 4)

    def test_basic_property(self):
        self.setup()

        # properties
        self.assertFalse(self.nodeB.is_shape)
        self.assertFalse(self.nodeC.is_shape)
        self.assertTrue(self.mesh.is_shape)
        self.assertEqual(self.node.type_name, 'transform')
        self.assertEqual(self.nodeB.type_name, 'joint')
        self.assertEqual(self.mesh.type_name, 'mesh')
        self.assertTrue(self.mesh.is_deformable)

        # name
        self.assertEqual(self.nodeC.name, 'nodeC')
        self.assertEqual(self.nodeC.long_name, '|nodeA|nodeB|nodeC')
        self.mesh.name = 'test'
        self.assertEqual(self.mesh.name, 'test')
        self.mesh.sync_shape_name()
        self.assertEqual(self.mesh.name, 'meshShape')
        self.assertEqual(self.mesh.long_name, '|nodeA|nodeB|nodeC|mesh|meshShape')

    def test_attribute(self):
        self.setup()

        # transform attrs
        self.node.set_attr('t', (1, 1, 1))
        self.node.set_attr('tx', 100)
        self.assertEqual(self.node.get_attr('tx'), 100.0)
        self.assertEqual(self.node.get_attr('t'), (100.0, 1.0, 1.0))

        # add float attr
        self.node.add_attr('float', name='test', defaultValue=12.5)
        self.assertTrue(self.node.has_attr('test'))
        self.assertEqual(self.node.get_attr('test'), 12.5)

        # add string attr
        self.node.add_attr('string', name='test_str', defaultValue='abc')
        self.assertEqual(self.node.attr('test_str').value, 'abc')
        self.node.attr('test_str').value = '123'
        self.assertEqual(self.node.get_attr('test_str'), '123')

        # tags
        with self.assertRaises(RuntimeError):
            self.node.add_tag('test', self.mesh)
        self.node.add_tag('test', self.mesh, force=True)
        self.assertEqual(self.node.get_tag('test'), self.mesh)
        self.node.add_tag('testb', self.nodeA)
        self.assertEqual(self.node.get_tag('testb'), self.nodeA)

        self.node.add_tag('test', 'abc', force=True)
        self.assertEqual(self.node.get_tag('test'), 'abc')

        # delete attr
        self.node.delete_attr('test')

        # connection
        self.node.tx >> self.nodeA.ty
        self.assertEqual(self.node.search_node('node.', upstream=False), self.nodeA)
        self.assertEqual(self.nodeA.search_node('node', upstream=True), self.node)

    def test_hierarchy(self):
        self.setup()

        # parent
        self.assertEqual(self.nodeC.get_parent(), self.nodeB)
        self.assertEqual(self.nodeC.get_parent(level=2), self.nodeA)
        self.assertEqual(self.nodeC.get_parent(level=3), None)
        self.assertEqual(self.nodeC.get_parent(level=4), None)
        self.assertEqual(self.nodeC.get_root_parent(), self.nodeA)
        self.assertEqual(self.mesh.get_root_parent(), self.nodeA)
        self.assertEqual(self.node.get_parent(), None)
        self.assertEqual(self.node.get_root_parent(), None)

        # child
        self.assertEqual(self.nodeC.get_children(), [self.mesh_xform])
        self.assertEqual(self.nodeC.get_children(type_='joint'), [])
        self.assertEqual(self.nodeA.get_children(type_='joint'), [self.nodeB])
        self.assertEqual(self.mesh_xform.get_children(type_='mesh'), [self.mesh])
        self.assertTrue(self.mesh_xform.is_child_of(self.nodeA))
        self.assertTrue(self.nodeA.is_parent_of(self.nodeC))

        # shape-xform
        self.assertEqual(self.mesh.get_xform(), self.mesh_xform)
        self.assertEqual(self.mesh_xform.get_xform(), self.mesh_xform)
        self.assertEqual(self.mesh.get_shapes(), [self.mesh])
        self.assertEqual(self.mesh_xform.get_shapes(), [self.mesh])
        self.assertEqual(self.mesh_xform.get_shapes(type_='nurbsSurface'), [])

        # add parent
        self.nodeB.set_translation((1, 2, 3), space='world')
        self.nodeC.set_translation((4, 5, 6), space='world')
        np = self.nodeC.add_parent('np')
        self.assertEqual(np.get_parent(), self.nodeB)
        self.assertEqual(self.nodeC.get_parent(), np)
        self.assertEqual(self.nodeC.get_translation(), (0, 0, 0))
        self.assertEqual(np.get_translation(), (3, 3, 3))

        self.nodeC.set_parent(self.nodeB)
        cmds.delete(np)
        np = self.nodeC.add_parent('np', attrs='txty')
        self.assertEqual(np.get_parent(), self.nodeB)
        self.assertEqual(self.nodeC.get_parent(), np)
        self.assertEqual(self.nodeC.get_translation(), (0, 0, 3))
        self.assertEqual(np.get_translation(), (3, 3, 0))

        # add child
        nc = self.nodeC.add_child('nc', align=True, insert=True)
        self.assertEqual(nc.get_parent(), self.nodeC)
        self.assertEqual(self.mesh_xform.get_parent(), nc)
        self.assertEqual(nc.get_translation(), (0, 0, 0))

        self.mesh_xform.set_parent(self.nodeC)
        cmds.delete(nc)
        nc = self.nodeC.add_child('nc', align=False, insert=False)
        self.assertEqual(nc.get_parent(), self.nodeC)
        self.assertEqual(self.mesh_xform.get_parent(), self.nodeC)
        self.assertEqual(nc.get_translation(), (-4, -5, -6))

        # test search
        result = self.nodeA.search_hierarchy(pattern=".*C", upstream=False)
        self.assertEqual(result.name, 'nodeC')
        result = self.nodeC.search_hierarchy(pattern=".*A", upstream=True)
        self.assertEqual(result.name, 'nodeA')


    def test_transform(self):
        self.setup()

        # translate
        self.nodeA.set_translation((1, 2, 3), space='world')
        self.nodeB.set_translation((4, 5, 6), space='world')
        self.assertEqual(self.nodeB.get_translation(space='object', as_tuple=True), (3, 3, 3))
        self.assertEqual(self.nodeB.get_translation(space='world', as_tuple=True), (4, 5, 6))
        self.assertEqual(self.nodeB.get_translation(space='object', as_tuple=False), OpenMaya.MVector(3, 3, 3))

        self.assertEqual(self.node.get_attr('rotateOrder'), 0)
        self.node.set_rotate_order('yzx')
        self.assertEqual(self.node.get_attr('rotateOrder'), 1)

        # reset
        self.nodeB.reset('tx')
        self.assertEqual(self.nodeB.get_translation(space='object', as_tuple=True), (0, 3, 3))
        self.nodeB.reset()
        self.assertEqual(self.nodeB.get_translation(space='object', as_tuple=True), (0, 0, 0))

        # rotate
        self.nodeA.set_rotation((10, 20, 30), space='world')
        self.nodeB.set_rotation((40, 50, 60), space='world')
        self.assertVectorEqual(self.nodeB.get_rotation(space='world', as_tuple=True), (40, 50, 60))
        self.assertVectorEqual(cmds.xform(self.nodeB, os=True, q=True, ro=True),
                               self.nodeB.get_rotation(space='object', as_tuple=True))
        self.assertVectorEqual(cmds.xform(self.nodeB, ws=True, q=True, ro=True), (40, 50, 60))
        self.nodeA.reset('r')
        self.nodeB.reset('r')

        # matrix
        self.assertEqual(self.nodeB.get_matrix(space='world', as_tuple=True),
                         cmds.xform(self.nodeB, q=True, ws=True, m=True))

        # lock
        self.node.lock('trxsy')
        self.assertFalse(self.node.attr('t').keyable)
        self.assertTrue(self.node.attr('t').locked)
        self.assertFalse(self.node.attr('tx').keyable)
        self.assertTrue(self.node.attr('tx').locked)
        self.assertFalse(self.node.attr('rx').keyable)
        self.assertTrue(self.node.attr('rx').locked)
        self.assertTrue(self.node.attr('sx').keyable)
        self.assertFalse(self.node.attr('sx').locked)

        # unlock
        self.node.unlock()
        self.assertTrue(self.node.attr('t').keyable)
        self.assertFalse(self.node.attr('t').locked)
        self.assertTrue(self.node.attr('tx').keyable)
        self.assertFalse(self.node.attr('tx').locked)

        # limit # TODO write and test getter
        self.node.set_limit(etx=(True, False), tx=(-10, 0))

        # duplicate
        dup = self.nodeA.duplicate(parentOnly=True)[0]
        self.assertEqual(dup.name, self.nodeA.name + 'Dup')
        self.assertEqual(len(dup.get_children()), 0)

        dup = self.nodeB.duplicate(parentOnly=False, name='dup', rotate_order='yzx')[0]
        self.assertEqual(dup.name, 'dup')
        self.assertEqual(dup.get_children()[0].name, self.nodeC.name + '1')
        self.assertEqual(dup.get_attr('rotateOrder'), 1)

        # align
        self.node.set_rotate_order('xyz')

        self.nodeB.set_translation((4, 5, 6), space='world')
        self.nodeB.set_attr('r', (10, 20, 30))
        self.node.align(self.nodeB)
        self.assertVectorEqual(self.node.get_translation(), (4, 5, 6))
        self.assertVectorEqual(self.node.get_attr('r'), (10, 20, 30))
        self.node.reset()
        self.node.align(self.nodeB, skipTranslate=True)
        self.assertVectorEqual(self.node.get_translation(), (0, 0, 0))
        self.assertVectorEqual(self.node.get_attr('r'), (10, 20, 30))
        self.node.reset()
        self.node.align(self.nodeB, skipTranslate='y')
        self.assertVectorEqual(self.node.get_translation(), (4, 0, 6))
        self.assertVectorEqual(self.node.get_attr('r'), (10, 20, 30))
        self.node.reset()
        self.node.align(self.nodeB, skipRotate=True)
        self.assertVectorEqual(self.node.get_translation(), (4, 5, 6))
        self.assertVectorEqual(self.node.get_attr('r'), (0, 0, 0))
        self.node.reset()
        self.node.align(self.nodeB, skipRotate='z')
        self.assertVectorEqual(self.node.get_translation(), (4, 5, 6))
        self.assertVectorEqual(self.node.get_attr('r'), (10, 20, 0))

        # parent align
        self.node.reset()
        self.node.parent_align(self.nodeB, keep_new_parent=False)
        self.assertVectorEqual(self.node.get_translation(), (4, 5, 6))
        self.assertVectorEqual(self.node.get_attr('r'), (10, 20, 30))
        self.assertEqual(self.node.get_parent(), None)
        self.node.reset()
        self.node.parent_align(self.nodeB, keep_new_parent=True)
        self.assertVectorEqual(self.node.get_translation(), (0, 0, 0))
        self.assertVectorEqual(self.node.get_attr('r'), (0, 0, 0))
        self.assertEqual(self.node.get_parent(), self.nodeB)

    def test_misc(self):
        self.setup()

        # color
        self.mesh_xform.set_color(10)
        self.assertEqual(self.mesh_xform.get_attr('overrideColor'), 10)
        self.assertFalse(self.mesh.get_attr('overrideEnabled'))
        self.mesh_xform.set_color(5, shape=True)
        self.assertEqual(self.mesh_xform.get_attr('overrideColor'), 10)
        self.assertEqual(self.mesh.get_attr('overrideColor'), 5)


class TestJoint(unittest.TestCase):
    """
    Test joint node
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.nodeA = Node.create('joint', name='nodeA')
        self.nodeB = Node.create('joint', name='nodeB')
        self.nodeC = Node.create('joint', name='nodeC')
        self.nodeB.set_parent(self.nodeA)
        self.nodeC.set_parent(self.nodeB)
        self.nodeB.set_translation((1, 2, 3))
        self.nodeC.set_translation((3, 3, 3))
        self.nodeA.orient_chain()

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip(v1, v2):
            self.assertAlmostEqual(val1, val2)

    def test_basic_property(self):
        self.setup()

        self.assertEqual(self.nodeB.long_axis, 'X')

    def test_chain(self):
        self.setup()

        self.assertAlmostEqual(
            self.nodeC.get_length(),
            math.distance(self.nodeB, self.nodeC))

        self.assertAlmostEqual(
            self.nodeA.get_chain_length(),
            math.distance(self.nodeA, self.nodeB) + math.distance(self.nodeC, self.nodeB))

    def test_misc(self):
        self.setup()

        dup = self.nodeA.duplicate(parentOnly=False, radius=3)[0]
        self.assertAlmostEqual(dup.get_children()[0].get_attr('radius'), 3)

        self.nodeA.set_segment_scale_compensate(False, hierarchy=True)
        self.assertFalse(self.nodeC.get_attr('segmentScaleCompensate'))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTransform))
    suite.addTest(unittest.makeSuite(TestJoint))
    unittest.TextTestRunner(failfast=True).run(suite)
