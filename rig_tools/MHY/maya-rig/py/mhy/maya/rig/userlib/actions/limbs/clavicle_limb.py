import maya.cmds as cmds

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const


class IKFKClavicle(bl.BaseLimb):
    """IK FK Clavicle limb class
    To create a one joint clavicle setup with ik fk setups.

    :limb type: clavicle
    """

    _LIMB_TYPE = 'clavicle'
    _DEFAULT_SIDE = 'L'

    _UI_ICON = 'clavicle'

    def marker_data(self):
        """Marker system definition."""
        part = self.param('part').value
        side = self.param('side').enum_value
        data = {'aim_axis': 'x', 'up_axis': 'y', 'markers': []}

        for desc, pos, cns, up in zip(
                (None, 'end'),
                ((.8, 137.3, 3.1), (13, 139.8, .7)),
                ('aim', 'parent'),
                ((0, 1, 0), None)):
            name = NodeName(
                part=part, desc=desc, side=side, num=None, ext=const.EXT_MARKER)
            data['markers'].append({
                'name': name,
                'position': pos,
                'rotation': cns,
                'up_type': up})

        return data

    def run(self):
        """Builds the limb ctrl rig."""
        start_joint, end_joint = self.rig_skeleton[0]

        # create clavicle root
        name = NodeName(start_joint, desc='FKRoot',ext='GRP')
        clavicle_root = Node.create(
            'transform',name=name, parent=self.limb_root.value)
        clavicle_root.parent_align(start_joint)

        # create ik joint chain
        name = NodeName(start_joint.name,ext='IKJNT')
        clavicle_ik_jnt = start_joint.duplicate(name=name, parentOnly=True)[0]
        clavicle_ik_jnt.v.value = False
        name = NodeName(end_joint.name,ext='IKJNT')
        shoulder_ik_jnt = end_joint.duplicate(name=name, parentOnly=True)[0]
        shoulder_ik_jnt.set_parent(clavicle_ik_jnt)
        self.add_constraint('parent', shoulder_ik_jnt, end_joint, maintainOffset=True)

        # Create IK Handle
        name = NodeName(clavicle_ik_jnt.name,desc='IKHANDLE',ext='HANDLE')
        ikHandle = cmds.ikHandle(
            startJoint=clavicle_ik_jnt,
            endEffector=shoulder_ik_jnt,
            name=name,
            solver='ikSCsolver')[0]
        ikHandle=Node(ikHandle)
        ikHandle.v.value = False

        # Create clavicle ik ctrl
        name = NodeName(clavicle_ik_jnt,desc='FK',ext='FKCTRL')     
        clavicle_fk_ctrl=self.add_ctrl(
            xform=clavicle_ik_jnt,
            name=name,
            parent=clavicle_root,
            ext='FKCTRL',
            shape='cube')
        clavicle_ik_jnt.set_parent(clavicle_fk_ctrl)
        name.replace_desc('IK')
        name.replace_ext('FKCTRL')
        clavicle_ik_ctrl = self.add_ctrl(
            xform=shoulder_ik_jnt,
            name=name,
            ext='IKCTRL',
            shape='circle',
            parent=clavicle_fk_ctrl)
        self.add_constraint('point',clavicle_ik_ctrl,ikHandle,mo=True)
        ikHandle.set_parent(clavicle_fk_ctrl)
        self.add_constraint('parent',clavicle_ik_jnt,start_joint,mo=True)
        self.add_constraint('scale',clavicle_ik_jnt,start_joint)

        # setup stretch
        dist_start_loc = Node.create('transform',name=NodeName(start_joint,desc='DistStart',ext='LOC'))
        dist_start_loc.set_parent(clavicle_root)
        self.add_constraint('point',clavicle_ik_jnt,dist_start_loc,maintainOffset=False)
        dist_end_loc = Node.create('transform', name=NodeName(start_joint,desc='DistEnd',ext='LOC'))
        dist_end_loc.set_parent(clavicle_root)
        self.add_constraint('point',clavicle_ik_ctrl,dist_end_loc,mo=False)
        name = NodeName(start_joint,desc='Dist',ext='DISTNODE')
        distNode = Node.create('distanceBetween', name=name)
        dist_start_loc.translate >> distNode.point1
        dist_end_loc.translate >> distNode.point2
        name = NodeName(start_joint,desc='Multi',ext='MDNODE')
        multiNode = Node.create('multiplyDivide', name=name)
        multiNode.operation.value = 1
        distNode.distance >> multiNode.input1X
        if self.param('side').enum_value=='R':           
            multiNode.input2X.value = -1
        else:
            multiNode.input2X.value = 1
        # setup limb stretch attr
        clavicle_stretch=self.add_limb_attr('float',name='stretch',defaultValue=0,keyable=True, minValue=0, maxValue=1)
        name = NodeName(start_joint, desc='stretch', ext='RMP')
        remap = Node.create('remapValue', name=name)
        clavicle_stretch >> remap.inputValue
        multiNode.outputX >> remap.outputMax
        remap.outputMin.value = shoulder_ik_jnt.tx.value
        remap.outValue >> shoulder_ik_jnt.tx

        leafParentNode = Node.create('transform',name=NodeName(clavicle_ik_jnt.name,desc='LeafParent',ext='LOC'))
        self.add_constraint('parent',shoulder_ik_jnt,leafParentNode,mo=False)
        leafParentNode.set_parent(clavicle_root)        
        self.ctrl_leaf_parent = leafParentNode

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        The bind skeleton only contains the base clavicle joint.
        """
        self.tag_bind_joint(self.rig_skeleton[0][0])
