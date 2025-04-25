from mhy.maya.nodezoo.node import Node, SkinCluster
from mhy.maya.nodezoo.constant import SurfaceAssociation
import mhy.maya.nodezoo.node.blend_shape as bs
import unittest
import random

import maya.cmds as cmds


class TestSkinCluster(unittest.TestCase):
    def set_up(self):
        cmds.file(new=True, force=True)
        self.cube = cmds.polyCube(
            depth=10, height=10, width=10,
            subdivisionsX=10, subdivisionsY=10, subdivisionsZ=10,
            constructionHistory=False)[0]
        self.jnts = []
        cmds.currentTime(1)
        for i in range(15):
            cmds.select(cl=True)
            rd_x = random.uniform(-5, 5)
            rd_y = random.uniform(-5, 5)
            rd_z = random.uniform(-5, 5)
            jnt = cmds.joint(p=(rd_x, rd_y, rd_z))
            self.jnts.append(jnt)

        self.skin = Node.create('skinCluster', self.jnts, self.cube, toSelectedBones=True)
        self.skin.smooth_weights(tolerance=0.5)
        self.assertTrue(self.skin, "Failed to create node instance from skin")

    def test_export(self):
        self.set_up()

        data = self.skin.export()
        self.assertTrue(data, "Failed to export data from skin")
        for jnt in self.jnts:
            cmds.setKeyframe(jnt)
            rd_tx = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='tx', v=rd_tx)
            rd_ty = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='ty', v=rd_ty)
            rd_tz = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='tz', v=rd_tz)
            rd_rx = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='rx', v=rd_rx)
            rd_ry = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='ry', v=rd_ry)
            rd_rz = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='rz', v=rd_rz)
            rd_sx = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='sx', v=rd_sx)
            rd_sy = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='st', v=rd_sy)
            rd_sz = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='sz', v=rd_sz)

        cmds.currentTime(2)
        vtx_count = cmds.polyEvaluate(self.cube, vertex=True)
        pre_vtx_positions = []
        for i in range(vtx_count):
            pre_vtx_positions.append(
                round_list(
                    cmds.xform("{}.vtx[{}]".format(self.cube, i), t=True, q=True, ws=True)
                ))

        for sa in SurfaceAssociation.items():
            cmds.currentTime(1)
            self.skin.delete()
            # Import back the data
            self.skin = Node.load_data(data, surface_association=sa)
            cmds.currentTime(2)
            post_vtx_positions = []
            for i in range(vtx_count):
                post_vtx_positions.append(
                    round_list(cmds.xform("{}.vtx[{}]".format(self.cube, i),
                                          t=True,
                                          q=True,
                                          ws=True)))
            pre_vtx_positions = [[round(i[0], 0), round(i[1], 0), round(i[2], 0)] for i in pre_vtx_positions]
            post_vtx_positions = [[round(i[0], 0), round(i[1], 0), round(i[2], 0)] for i in post_vtx_positions]

            self.assertEqual(pre_vtx_positions, post_vtx_positions,
                             "Deformation is changed after export and import skin data with {} association".format(sa))


class TestCluster(unittest.TestCase):
    condition = int(cmds.about(version=True)) >= 2022

    def set_up(self):
        cmds.file(new=True, force=True)
        self.cube = cmds.polyCube(
            depth=5, height=5, width=5,
            subdivisionsX=5, subdivisionsY=5, subdivisionsZ=5,
            constructionHistory=False)[0]

        self.cluster, self.handle = Node.create('cluster', "{}.vtx[0:7]".format(self.cube))
        self.assertTrue(self.cluster, "Failed to create node instance from skin")

        cmds.select("{}.vtx[0:3]".format(self.cube))

        cmds.percent(self.cluster.name, v=0.7)

        cmds.currentTime(1)
        cmds.setKeyframe(self.handle.name)
        cmds.currentTime(2)
        cmds.setAttr('{}.tx'.format(self.handle.name), 12)
        cmds.setKeyframe(self.handle.name)
        cmds.currentTime(1)

    @unittest.skipIf(condition, "Copy deformer weight maya command unresolved bug")
    def test_export(self):
        self.set_up()
        data = self.cluster.export()
        vtx_count = 5 * 5 * 5
        cmds.currentTime(2)

        pre_vtx_positions = []
        for i in range(vtx_count):
            pre_vtx_positions.append(cmds.xform("{}.vtx[{}]".format(self.cube, i), t=True, q=True, ws=True))

        cmds.setKeyframe(self.handle.name)
        for sa in SurfaceAssociation.items():
            self.cluster.delete()
            cmds.currentTime(1)
            self.cluster = Node.load_data(data, surface_association=sa)
            self.handle = self.cluster.get_handle().get_parent()
            cmds.setKeyframe(self.handle.name)
            cmds.setAttr('{}.tx'.format(self.handle.name), 12)
            post_vtx_positions = []
            for i in range(vtx_count):
                post_vtx_positions.append(
                    cmds.xform("{}.vtx[{}]".format(self.cube, i),
                               t=True,
                               q=True,
                               ws=True))
            pre_vtx_positions = [[round(i[0], 0), round(i[1], 0), round(i[2], 0)] for i in pre_vtx_positions]
            post_vtx_positions = [[round(i[0], 0), round(i[1], 0), round(i[2], 0)] for i in post_vtx_positions]
            self.assertEqual(
                pre_vtx_positions,
                post_vtx_positions,
                "Deformation is changed after export and import skin data with {} association".format(sa))


class TestBlendShape(unittest.TestCase):
    def set_up(self):
        cmds.file(new=True, force=True)
        self.cube1 = cmds.polyCube(depth=10, height=10, width=10,
                                   subdivisionsX=10, subdivisionsY=10, subdivisionsZ=10,
                                   constructionHistory=False)[0]
        self.cube2 = cmds.polyCube(depth=10, height=10, width=10,
                                   subdivisionsX=10, subdivisionsY=10, subdivisionsZ=10,
                                   constructionHistory=False)[0]
        self.cube3 = cmds.polyCube(depth=10, height=10, width=10,
                                   subdivisionsX=10, subdivisionsY=10, subdivisionsZ=10,
                                   constructionHistory=False)[0]
        self.bs = bs.BlendShape.create(self.cube1, self.cube2, self.cube3)

    def test_export(self):
        self.set_up()
        data1 = self.bs.export()
        self.bs.load(data1)
        data2 = self.bs.export()
        self.assertTrue(data1 == data2)

    def test_decompose_pose_space_delta(self):
        self.set_up()
        cmds.select(cl=True)
        root = cmds.joint()
        end_jnt = cmds.joint(position=[4, 4, 4])
        self.jnts = [root, end_jnt]
        Node.create('skinCluster', self.cube3, self.jnts)

        cmds.currentTime(1)
        cmds.setKeyframe(root)
        cmds.setKeyframe(end_jnt)

        for jnt in self.jnts:
            cmds.setKeyframe(jnt)
            rd_tx = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='tx', v=rd_tx)
            rd_ty = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='ty', v=rd_ty)
            rd_tz = random.uniform(-15, 15)
            cmds.setKeyframe(jnt, t=2, at='tz', v=rd_tz)
            rd_rx = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='rx', v=rd_rx)
            rd_ry = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='ry', v=rd_ry)
            rd_rz = random.uniform(-90, 90)
            cmds.setKeyframe(jnt, t=2, at='rz', v=rd_rz)
            rd_sx = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='sx', v=rd_sx)
            rd_sy = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='st', v=rd_sy)
            rd_sz = random.uniform(0.5, 3)
            cmds.setKeyframe(jnt, t=2, at='sz', v=rd_sz)
        self.bs.set_target_weight('pCube1', 1)
        cmds.currentTime(2)
        cube4 = cmds.duplicate(self.cube3)[0]
        mesh4 = Node(cube4).get_shapes()[0]
        vtx_num = mesh4.num_vertices
        for i in range(vtx_num):
            rd_x = random.uniform(-15, 15)
            rd_y = random.uniform(-15, 15)
            rd_z = random.uniform(-15, 15)
            cmds.xform('{}.vtx[{}]'.format(cube4, i), ws=False, t=(rd_x, rd_y, rd_z))

        points = mesh4.get_points(space='object')
        self.bs.decompose_pose_space_delta(points, 0, inbetween_val=6000, threshold=0.001)
        pre_vtx_positions = []
        for i in range(vtx_num):
            pre_vtx_positions.append(
                round_list(
                    cmds.xform("{}.vtx[{}]".format(cube4, i), t=True, q=True, ws=True)
                ))

        pre_vtx_positions = [[round(i[0], 3), round(i[1], 3), round(i[2], 3)] for i in pre_vtx_positions]
        post_vtx_positions = []
        for i in range(vtx_num):
            post_vtx_positions.append(
                round_list(
                    cmds.xform("{}.vtx[{}]".format(self.cube3, i), t=True, q=True, ws=True)
                ))
        post_vtx_positions = [[round(i[0], 3), round(i[1], 3), round(i[2], 3)] for i in post_vtx_positions]

        for pre, post in zip(pre_vtx_positions, post_vtx_positions):
            self.assertLess(abs(pre[0] - post[0]), 1)
            self.assertLess(abs(pre[1] - post[1]), 1)
            self.assertLess(abs(pre[2] - post[2]), 1)

        for i in range(vtx_num):
            rd_x = random.uniform(-15, 15)
            rd_y = random.uniform(-15, 15)
            rd_z = random.uniform(-15, 15)
            cmds.xform('{}.vtx[{}]'.format(cube4, i), ws=False, t=(rd_x, rd_y, rd_z))
        self.bs.set_target_weight('pCube1', 0.6)
        points = mesh4.get_points(space='object')
        self.bs.decompose_pose_space_delta(points, 0, inbetween_val=5600, threshold=0.001)
        pre_vtx_positions = []
        for i in range(vtx_num):
            pre_vtx_positions.append(
                round_list(
                    cmds.xform("{}.vtx[{}]".format(cube4, i), t=True, q=True, ws=True)
                ))
        pre_vtx_positions = [[round(i[0], 3), round(i[1], 3), round(i[2], 3)] for i in pre_vtx_positions]
        post_vtx_positions = []
        for i in range(vtx_num):
            post_vtx_positions.append(
                round_list(
                    cmds.xform("{}.vtx[{}]".format(self.cube3, i), t=True, q=True, ws=True)
                ))
        post_vtx_positions = [[round(i[0], 3), round(i[1], 3), round(i[2], 3)] for i in post_vtx_positions]

        for pre, post in zip(pre_vtx_positions, post_vtx_positions):
            self.assertLess(abs(pre[0] - post[0]), 1)
            self.assertLess(abs(pre[1] - post[1]), 1)
            self.assertLess(abs(pre[2] - post[2]), 1)


def round_list(t, d=3):
    t = [round(i, d) for i in t]
    return t


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(TestBlendShape('test_decompose_pose_space_delta'))
    suite.addTest(unittest.makeSuite(TestSkinCluster))
    suite.addTest(unittest.makeSuite(TestCluster))
    suite.addTest(unittest.makeSuite(TestBlendShape))
    unittest.TextTestRunner(failfast=True).run(suite)
