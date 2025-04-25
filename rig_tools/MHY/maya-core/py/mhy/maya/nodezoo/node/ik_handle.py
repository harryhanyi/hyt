import maya.OpenMayaAnim as OpenMayaAnim
import maya.cmds as cmds
from mhy.maya.nodezoo.node import Transform, Node


class IkHandle(Transform):
    __NODETYPE__ = 'ikHandle'
    __FNCLS__ = OpenMayaAnim.MFnIkHandle

    @classmethod
    def create(cls, *args, **kwargs):
        result = cmds.ikHandle(*args, **kwargs)
        if result:
            handle, effect = result
            return Node(handle), Node(effect)
