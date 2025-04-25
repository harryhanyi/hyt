import maya.OpenMayaAnim as OpenMayaAnim

from mhy.maya.nodezoo.node import DagNode


class Lattice(DagNode):
    __NODETYPE__ = 'lattice'
    __FNCLS__ = OpenMayaAnim.MFnLattice

    @property
    def is_deformable(self):
        return True
