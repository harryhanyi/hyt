import unittest

from maya import cmds

from mhy.maya.nodezoo.node import Node
import mhy.maya.rigtools.pose_editor.api.target as target_api
import random


class TestTarget(unittest.TestCase):
    """
    Test Target setup
    """
    def set_up(self):
        cmds.file(force=True, newFile=True)
        self.cube = cmds.polyCube(
            depth=10, height=10, width=10,
            subdivisionsX=4, subdivisionsY=4, subdivisionsZ=4,
            constructionHistory=False)[0]

        target1 = cmds.polyCube(
            depth=10, height=10, width=10,
            subdivisionsX=4, subdivisionsY=4, subdivisionsZ=4,
            constructionHistory=False)[0]

        mesh1 = Node(target1).get_shapes()[0]
        vtx_num = mesh1.num_vertices
        for i in range(vtx_num):
            rd_x = random.uniform(-15, 15)
            rd_y = random.uniform(-15, 15)
            rd_z = random.uniform(-15, 15)
            cmds.xform('{}.vtx[{}]'.format(target1, i), ws=False, t=(rd_x, rd_y, rd_z))

        target2 = cmds.polyCube(
            depth=10, height=10, width=10,
            subdivisionsX=4, subdivisionsY=4, subdivisionsZ=4,
            constructionHistory=False)[0]

        mesh2 = Node(target2).get_shapes()[0]
        vtx_num = mesh2.num_vertices
        for i in range(vtx_num):
            rd_x = random.uniform(-15, 15)
            rd_y = random.uniform(-15, 15)
            rd_z = random.uniform(-15, 15)
            cmds.xform('{}.vtx[{}]'.format(target2, i), ws=False, t=(rd_x, rd_y, rd_z))
        self.bs = Node.create('blendShape', target1, self.cube)
        self.inbetween_attr = self.bs.add_in_between(0, target=target2, value=0.4)
        self.inbetween_attr2 = self.bs.add_in_between(0, target=None, value=0.6)
        cmds.delete(target1)
        cmds.delete(target2)

    def test_basic_api(self):
        self.set_up()
        weight_attr = self.bs.weight[0]
        self.in_between_target1 = target_api.PoseTarget(weight_attr, weight=0.4, pose=None)
        self.in_between_target2 = target_api.PoseTarget(weight_attr, weight=0.6, pose=None)

        self.in_between_target1.mirror()
        self.in_between_target2.mirror()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestTarget('test_basic_api'))
    unittest.TextTestRunner(failfast=True).run(suite)
