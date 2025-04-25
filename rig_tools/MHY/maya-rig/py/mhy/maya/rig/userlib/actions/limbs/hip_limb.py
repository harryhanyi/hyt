from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const


class Hip(bl.BaseLimb):
    """Hip limb class.

    :limb type: hip
    """

    _LIMB_TYPE = 'hip'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'hip'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        name = NodeName(part=part, side=side, num=None, ext=const.EXT_MARKER)

        return {'aim_axis': 'x',
                'up_axis': 'z',
                'markers': [
                    {'name': name,
                     'position': (0.0, 90.8, 0.0),
                     'rotation': (0, 0, 90)}
                ]}

    def run(self):
        """Builds the limb ctrl rig."""
        ctrl_scale = (1, 1, 1)
        start_joint = self.rig_skeleton[0][0]

        # body ctrl
        name = NodeName(start_joint, part='body', ext='FKCTRL')
        body_ctrl = self.add_ctrl(
            name=name,
            shape='circle',
            scale=ctrl_scale,
            parent=self.limb_root.value,
            rot=(0, 0, 0))
        body_ctrl.plc_node.align(start_joint, skipRotate=True)

        # hip root ctrl
        ctrl_scale = tuple([0.5 * i for i in ctrl_scale])
        name = name.replace_part('hip')
        hip_ctrl = self.add_ctrl(
            name=name,
            xform=start_joint,
            shape='cube',
            scale=ctrl_scale,
            parent=body_ctrl,
            rot=(0, 0, 90))

        self.add_constraint('parent', hip_ctrl, start_joint)
        body_ctrl.lock(attrs='sv')
        hip_ctrl.lock(attrs='sv')
        self.ctrl_leaf_parent = body_ctrl
