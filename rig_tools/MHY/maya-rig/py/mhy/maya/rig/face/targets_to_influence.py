"""
This module has some functions to place pose controls to match target shapes
"""
from mhy.maya.nodezoo.node import Node
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
source_joint = 'result:face_mouthUpper_02_R_JNT'
target_joint = 'face_mouthUpper_02_R_JNT'


class TracerHierarchy(object):
    def __init__(self, jnt):
        self.joint = Node(jnt)

    def get_fk_ctrl(self):
        return self.joint.search_node('.*FKCTRL')

    def get_tracer(self):
        fk_ctrl = self.get_fk_ctrl()
        if not fk_ctrl:
            return
        transport_group = fk_ctrl.search_hierarchy('.*TRANSPORT', True)
        if not transport_group:
            return
        return transport_group.search_node('.*_TRACER')

    def get_patch_nurbs(self):
        fk_ctrl = self.get_fk_ctrl()
        if not fk_ctrl:
            return
        transport_group = fk_ctrl.search_hierarchy('.*TRANSPORT', True)
        if not transport_group:
            return
        return transport_group.search_node(
            '.*SKULLShape',
            type_filter=OpenMaya.MFn.kNurbsSurface)

    def match_to_target_joint(self, jnt, offset_fk_ctrl=True):
        patch = self.get_patch_nurbs()
        if not patch:
            OpenMaya.MGlobal.displayWarning("Failed to find associated patch surface from {}".format(self.joint))
            return

        jnt = Node(jnt)
        pos = jnt.get_translation(space='world')
        param_u, param_v = patch.closest_param(pos)

        tracer = self.get_tracer()
        if not tracer:
            OpenMaya.MGlobal.displayWarning("Failed to find associated tracer from {}".format(self.joint))
            return

        orig_u = tracer.originU.value
        orig_v = tracer.originV.value

        tracer.set_attr('parameterU', param_u-orig_u)
        tracer.set_attr('parameterV', param_v-orig_v)

        if offset_fk_ctrl:
            fk_ctrl = self.get_fk_ctrl()
            if not fk_ctrl:
                OpenMaya.MGlobal.displayWarning("Failed to find fk control from {}".format(self.joint))
                return

            world_matrix = cmds.xform(jnt, q=True, matrix=True, ws=True)
            cmds.xform(fk_ctrl, matrix=world_matrix, ws=True)
