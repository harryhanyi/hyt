import unittest

from maya import cmds, OpenMaya

# import mhy.maya.nodezoo as nz
from mhy.maya.nodezoo.node import Node

# nz.refresh()


class TestCurve(unittest.TestCase):
    """
    Test the nurbsCurve node
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.curve = Node.create(
            'nurbsCurve',
            [(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9), (12, 10, 2)],
            name='curve',
            degree=3)
        self.xform = self.curve.get_parent()

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip((v1[0], v1[1], v1[2]),
                              (v2[0], v2[1], v2[2])):
            self.assertAlmostEqual(val1, val2, 5)

    def test_create_from_transform(self):
        cmds.file(newFile=True, force=True)

        points = ((0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9), (12, 10, 2))
        xforms = []
        for pos in points:
            xform = Node.create('transform')
            xform.set_translation(pos)
            xforms.append(xform)

        curve = Node.create('nurbsCurve', xforms, name='curve', degree=3)
        for i in range(len(points)):
            self.assertVectorEqual(
                cmds.xform('{}.cv[{}]'.format(curve, i), query=True, worldSpace=True, translation=True),
                points[i])

    def test_create_from_surface(self):
        cmds.file(newFile=True, force=True)

        plane = Node(cmds.nurbsPlane(ch=False)[0])
        curve = Node.create('nurbsCurve', plane, ((0, 0), (0, 1), (1, 1)), degree=1)
        self.assertVectorEqual(
            cmds.xform('{}.cv[0]'.format(curve), query=True, worldSpace=True, translation=True),
            (0, -.5, .5))
        self.assertVectorEqual(
            cmds.xform('{}.cv[1]'.format(curve), query=True, worldSpace=True, translation=True),
            (0, .5, .5))
        self.assertVectorEqual(
            cmds.xform('{}.cv[2]'.format(curve), query=True, worldSpace=True, translation=True),
            (0, .5, -.5))

        curve = Node.create('nurbsCurve', plane, ((0, 0), (0, 1), (1, 1)), degree=1, underworld=True)
        self.assertVectorEqual(
            cmds.xform('{}.cv[0]'.format(curve), query=True, worldSpace=True, translation=True),
            (0, 0, 0))
        self.assertVectorEqual(
            cmds.xform('{}.cv[1]'.format(curve), query=True, worldSpace=True, translation=True),
            (0, 1, 0))
        self.assertVectorEqual(
            cmds.xform('{}.cv[2]'.format(curve), query=True, worldSpace=True, translation=True),
            (1, 1, 0))

    def test_properties(self):
        self.setup()

        self.assertAlmostEqual(self.curve.max_param, 2)
        self.assertVectorEqual(self.curve.closest_point((0, 0, 0)), (0, 0, 0))
        self.assertAlmostEqual(self.curve.closest_param((0, 0, 0)), 0)
        self.assertVectorEqual(self.curve.point_at_param(2), (12, 10, 2))
        self.assertVectorEqual(self.curve.point_at_param(1, is_normalized=True), (12, 10, 2))

        points = self.curve.get_points()
        self.curve.set_points(points)

        xform = Node.create('transform')
        self.curve.closest_point(xform)
        self.curve.closest_normal(xform)
        self.curve.closest_tangent(xform)


class TestSurface(unittest.TestCase):
    """
    Test the nurbsSurface node
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        mesh = cmds.polyPlane(ch=False, sx=2, sy=2)[0]
        self.surface = Node.create(
            'nurbsSurface',
            '{}.e[0]'.format(mesh),
            '{}.e[10]'.format(mesh))
        self.xform = self.surface.get_parent()

    def assertVectorEqual(self, v1, v2):
        for i in range(len(v1)):
            self.assertAlmostEqual(v1[i], v2[i], 5)

    def test_properties(self):
        self.setup()

        self.assertAlmostEqual(self.surface.max_u, 1)
        self.assertAlmostEqual(self.surface.max_v, 2)
        self.assertVectorEqual(
            self.surface.point_at_param(1, 2),
            (0, 0, -.5))
        self.assertVectorEqual(
            self.surface.point_at_param(1, 1, is_normalized=True),
            (0, 0, -.5))

        point = (0, 0, 1)
        xform = Node.create('transform')
        self.assertVectorEqual(
            self.surface.closest_param(point),
            (0, 2.0))
        xform.set_translation(point)
        self.assertVectorEqual(
            self.surface.closest_param(xform),
            (0, 2.0))

        self.surface.closest_point(xform)
        self.surface.closest_normal(xform)
        self.surface.closest_tangent(xform)


class TestMesh(unittest.TestCase):
    """
    Test the mesh node
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        mesh = Node(cmds.polyPlane(ch=False, sx=2, sy=2)[0])
        self.mesh = mesh.get_shapes()[0]

    def test_properties(self):
        self.setup()

        self.assertEqual(
            sorted(self.mesh.get_polygon_vertices(0)), [0, 1, 3, 4])

        points = self.mesh.get_points()
        self.mesh.set_points(points)

        normals = self.mesh.get_vertex_normals()
        points = OpenMaya.MPointArray()
        for i in range(normals.length()):
            points.append(OpenMaya.MPoint(normals[i].x, normals[i].y, normals[i].z))
        self.mesh.set_points(points)


class TestFollicle(unittest.TestCase):
    """
    Test the follicle node
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.mesh = Node(cmds.polyPlane(ch=False, sx=2, sy=2)[0])
        self.mesh.set_attr('t', (0, 2, 0))

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip((v1[0], v1[1], v1[2]),
                              (v2[0], v2[1], v2[2])):
            self.assertAlmostEqual(val1, val2, 5)

    def test_create(self):
        self.setup()

        fol = Node.create('follicle', self.mesh)
        fol.parameterU.value = .5
        fol.parameterV.value = .5
        xform = fol.get_parent()
        self.assertVectorEqual(xform.get_attr('t'), (0, 2, 0))

        surface = Node.create(
            'nurbsSurface',
            '{}.e[0]'.format(self.mesh),
            '{}.e[10]'.format(self.mesh), keep_history=False)
        surface.get_parent().set_attr('t', (0, 2, 0))

        fol = Node.create('follicle', surface)
        fol.parameterU.value = .5
        fol.parameterV.value = .5
        xform = fol.get_parent()
        self.assertVectorEqual(xform.get_attr('t'), (-.25, 4, 0))

    def test_create_from_edges(self):
        self.setup()

        parent = Node.create('transform')
        loc = Node.create(
            'follicle',
            '{}.e[0]'.format(self.mesh),
            '{}.e[10]'.format(self.mesh),
            parent=parent)

        self.assertVectorEqual(loc.get_attr('t'), (-.25, 2, 0))

    def test_create_from_faces(self):
        self.setup()

        parent = Node.create('transform')
        locators = Node.create(
            'follicle',
            sorted(cmds.ls('{}.f[*]'.format(self.mesh), flatten=True)),
            parent=parent)

        self.assertEqual(len(locators), 4)
        self.assertVectorEqual(locators[0].get_attr('t'), (-.25, 2, .25))
        self.assertVectorEqual(locators[1].get_attr('t'), (.25, 2, .25))
        self.assertVectorEqual(locators[2].get_attr('t'), (-.25, 2, -.25))
        self.assertVectorEqual(locators[3].get_attr('t'), (.25, 2, -.25))
        self.assertEqual(locators[0].get_parent(level=2), parent)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCurve))
    suite.addTest(unittest.makeSuite(TestSurface))
    suite.addTest(unittest.makeSuite(TestMesh))
    suite.addTest(unittest.makeSuite(TestFollicle))
    unittest.TextTestRunner(failfast=True).run(suite)
