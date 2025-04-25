from maya import cmds

import mhy.protostar.core.parameter as pa

import mhy.maya.rig.base_limb as bl
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.constants as const


class FKLimb(bl.BaseLimb):
    """Generic FK limb class.

    Builds a number of FK ctrls based on the user specification.

    :limb type: fk
    """

    _LIMB_TYPE = 'fk'

    # --- input parameters

    @pa.int_param(default=1, min_value=1)
    def num_joints(self):
        """The number FK joints."""

    @pa.bool_param(default=True)
    def aim_to_child(self):
        """If True, aim each joint to its child."""

    @pa.bool_param(default=False)
    def enable_scale(self):
        """If True, enable scale constraint."""

    # --- end of parameter definition

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        base_name = NodeName(part=part, side=side, num=None, ext=const.EXT_MARKER)
        count = self.num_joints.value

        rot = up = None
        if self.aim_to_child.value and count > 1:
            rot = 'aim'
            up = 'ctrl'

        data = {
            'up_ctrl_position': (0, 8, 0),
            'markers': []
        }
        for i in range(count):
            name = base_name.replace_num(i) if count > 1 else base_name
            data['markers'].append({
                'name': name,
                'position': (0, 0, i * 6),
                'rotation': rot,
                'up_type': up})
        return data

    def run(self):
        """Core execution method."""
        ctrls = []
        for i, joint in enumerate(self.rig_skeleton[0]):
            # create fk ctrl
            ctrl = self.add_ctrl(
                xform=joint,
                ext='FKCTRL',
                shape='cube',
                scale=(1, 1, 1))

            if i > 0:
                ctrl.plc_node.set_parent(ctrls[-1])
            ctrls.append(ctrl)

            # add constraints
            # TODO: add an option for direct connection from ctrls to joints
            self.add_constraint(
                'parent', ctrl, joint, maintainOffset=True)
            if self.enable_scale.value:
                self.add_constraint('scale', ctrl, joint, maintainOffset=True)
            else:
                ctrl.lock('s')


class FKHierarchy(bl.BaseLimb):
    """FK Hierarchy limb class.

    This limb does **NOT** support marker system, user must
    supply a single joint into parameter "input_skeleton".
    Once executed, **ALL** joints under the input joint will be turned
    into FK ctrls.

    :limb type: fk_hier
    """

    _LIMB_TYPE = 'fk_hier'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    # --- input parameters

    @pa.bool_param(default=False)
    def enable_hierarchy(self):
        """If True, enable ctrl hierarchy."""

    @pa.bool_param(default=False)
    def enable_scale(self):
        """If True, enable scale constraint."""

    @pa.list_param(item_type='str', default=('PLC', 'SDK', 'OFFSET'))
    def group_exts(self):
        """Ctrl group extensions."""

    # --- end of parameter definition

    def marker_data(self):
        """Skip marker data as this limb depends on a pre-built
        joint hierarchy."""
        return

    def run(self):
        """Builds the limb ctrl rig."""
        group_exts = self.group_exts.value

        for joint in self.rig_skeleton[0][0].get_hierarchy():
            ctrl = self.add_ctrl(
                xform=joint,
                ext='FKCTRL',
                shape='cube',
                scale=(1, 1, 1),
                group_exts=group_exts)

            self.add_constraint('parent', ctrl, joint, maintainOffset=True)
            if self.enable_scale.value:
                self.add_constraint('scale', ctrl, joint, maintainOffset=True)

            parent = joint.get_parent()
            if parent:
                parent_ctrl = NodeName(parent, ext='FKCTRL')
                if cmds.objExists(parent_ctrl):
                    if self.enable_hierarchy.value:
                        ctrl.get_group(group_exts[0]).set_parent(parent_ctrl)
                    self.tag_bind_joint(joint, parent=parent)
                else:
                    self.tag_bind_joint(joint)
            else:
                self.tag_bind_joint(joint)
