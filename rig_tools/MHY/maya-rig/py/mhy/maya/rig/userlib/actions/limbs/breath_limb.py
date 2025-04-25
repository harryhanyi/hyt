import maya.cmds as cmds

import mhy.protostar.core.parameter as pa

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.utils as utils
import mhy.maya.rig.constants as const


class Breath(bl.BaseLimb):
    """
    Breath class with marker data implementation.

    :limb type: breath
    """

    _LIMB_TYPE = 'breath'
    _LIMB_SIDE = 'M'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'breath'

    @pa.enum_param(items=const.ROT_ORDERS, default='xyz')
    def rotate_order(self):
        """The rotation order."""

    @pa.list_param(default=[0,0,0,0,0,0,1.2,1,1.2])
    def breath_data(self):
        """ breath joint pose"""

    # -- end of parameter definition

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        data = {
            'aim_axis': 'x',
            'up_axis': 'z',
            'up_ctrl_position': (0, 93.4, 8),
            'markers': []}

        name = NodeName(part=part, side=side, num=None, ext=const.EXT_MARKER)
        data['markers'].append({
            'name': name,
            'position': (0, 130.52, 2.6),
            'rotation': None})
        return data

    def run(self):
        """Builds the limb ctrl rig."""
        limb_root = self.limb_root.value
        data = self.breath_data.value
        breath_jnt = self.rig_skeleton[0][0]
        breath_ctrl = self.add_ctrl(
            xform=breath_jnt,
            ext='SLDCTRL',
            parent=limb_root,
            shape='sphere')
        name = NodeName(breath_jnt, ext='GRP')
        breath_grp = Node.create('transform', name=name, parent=limb_root)
        breath_grp.align(breath_jnt)
        name = name.replace_ext('LOC')
        breath_loc = Node.create('transform', name=name, parent=breath_grp)
        breath_loc.align(breath_jnt)
        breath_ctrl.lock(attrs='rs')
        breath_ctrl.ty.locked = True
        breath_ctrl.tz.locked = True
        breath_ctrl.set_transform_limits(translationX=(0,10), enableTranslationX=(True,True))    
        attrs = [breath_loc.tx, breath_loc.ty, breath_loc.tz, breath_loc.rx,
            breath_loc.ry, breath_loc.rz, breath_loc.sx, breath_loc.sy, breath_loc.sz]
        breath_scale = self.add_limb_attr('float', name='breathScale', min=0, keyable=True, defaultValue=1)
        for index in range(0,9):
            name = NodeName(breath_ctrl, desc='remap', num=index, ext='RVNODE' )
            rv_node = Node.create('remapValue', name=name)
            breath_ctrl.tx>>rv_node.inputValue
            rv_node.inputMin.value = 0
            rv_node.inputMax.value = 10
            if index < 6:
                rv_node.outputMin.value = 0.0
            else:
                rv_node.outputMin.value = 1.0
            rv_node.outputMax.value = data[index]
            breath_scale>>rv_node.value[1].value_FloatValue
            rv_node.outValue>>attrs[index]
        self.add_constraint('parent', breath_loc, breath_jnt, maintainOffset=True)
        self.add_constraint('scale', breath_loc, breath_jnt, maintainOffset=True)
            
                    






        


