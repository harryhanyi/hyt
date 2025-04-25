import unittest
import maya.cmds as cmds
import random
from mhy.maya.anim.lib.node import Node


class TestAnimLib(unittest.TestCase):
    def random_key(self, node):
        rand_tx = random.uniform(-20, 20)
        rand_ty = random.uniform(-20, 20)
        rand_tz = random.uniform(-20, 20)
        rand_rx = random.uniform(-45, 45)
        rand_ry = random.uniform(-45, 45)
        rand_rz = random.uniform(-45, 45)
        rand_sx = random.uniform(0.1, 10)
        rand_sy = random.uniform(0.1, 10)
        rand_sz = random.uniform(0.1, 10)
        node.instance.translateX.value = rand_tx
        node.instance.translateY.value = rand_ty
        node.instance.translateZ.value = rand_tz
        node.instance.rotateX.value = rand_rx
        node.instance.rotateY.value = rand_ry
        node.instance.rotateZ.value = rand_rz
        node.instance.scaleX.value = rand_sx
        node.instance.scaleY.value = rand_sy
        node.instance.scaleZ.value = rand_sz
        cmds.setKeyframe(node.name)

    def test_export(self):
        cmds.file(new=True, force=True)
        cube = cmds.polyCube(depth=10, height=10, width=10, constructionHistory=False)[0]
        cube = Node(cube)
        cmds.currentTime(3)
        self.random_key(cube)
        cmds.currentTime(14)
        self.random_key(cube)
        cmds.currentTime(38)
        self.random_key(cube)
        cmds.currentTime(45)
        self.random_key(cube)
        pre_matrix_list = []
        post_matrix_list = []
        for i in range(1, 50):
            cmds.currentTime(i)
            mat = cmds.xform(cube.name, worldSpace=True, query=True, matrix=True)
            pre_matrix_list.append(mat)

        data = cube.export(static=False)

        cmds.delete(cmds.ls(type='animCurve'))

        cube.load(data)

        for i in range(1, 50):
            cmds.currentTime(i)
            mat = cmds.xform(cube.name, worldSpace=True, query=True, matrix=True)
            post_matrix_list.append(mat)
        self.assertVectorEqual(pre_matrix_list, post_matrix_list)

    def assertVectorEqual(self, v1, v2):
        for val1, val2 in zip(v1, v2):
            if isinstance(val1, (list, tuple)) and isinstance(val2, (list, tuple)):
                self.assertVectorEqual(val1, val2)
            else:
                self.assertAlmostEqual(val1, val2, 4)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAnimLib))
    unittest.TextTestRunner(failfast=True).run(suite)
