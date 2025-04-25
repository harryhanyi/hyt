from mhy.maya.standard.name import NodeName
import mhy.maya.rig.constants as const
import mhy.maya.rig.userlib.actions.limbs.ikfk_chain_limb as ch


class IKFKLeg(ch.IKFKChain):
    """IK leg limb class

    To create a three joints IK chain with pole vector ctrl and end ctrl.

    :limb type: leg
    """

    _LIMB_TYPE = 'leg'
    _DEFAULT_SIDE = 'L'
    _END_CTRL_NAME = 'foot'

    _UI_ICON = 'leg'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        data = {'aim_axis': 'x', 'up_axis': 'y', 'markers': []}
        if self.free_end_marker.value:
            ending = None
        else:
            ending = 'parent'
        for desc, pos, cns, up in zip(
                ('hip', 'knee', 'ankle'),
                ((9.4, 88.8, 0.9), (9.4, 52.4, -0.1), (9.4, 11, -4.4)),
                ('aim', 'aim', ending),
                ('plane', 'plane', 'parent')):
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
        super(IKFKLeg, self).run()
        #end_ctrl = self.ik_end_ctrl.value
        #self._ik_pole_vec_ctrl.add_space_switch(end_ctrl, space=self._END_CTRL_NAME)


class DJIKFKLeg(ch.DJIKFKChain):
    """Double joint IKFK leg limb class

    To create a three joints IK chain with pole vector ctrl and end ctrl.

    :limb type: leg
    """

    _LIMB_TYPE = 'leg'
    _DEFAULT_SIDE = 'L'
    _END_CTRL_NAME = 'foot'

    _UI_ICON = 'leg'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        data = {'aim_axis': 'x', 'up_axis': 'y', 'markers': []}
        if self.free_end_marker.value:
            ending = None
        else:
            ending = 'parent'

        for desc, pos, cns, up in zip(
                ('hip', 'knee', 'shin', 'ankle'),
                ((9.4, 88.8, 0.9), (9.4, 54, 0.77), (9.4, 48.35, 0.49), (9.4, 11, -4.4)),
                ('aim', 'aim', 'aim', ending),
                ('plane', 'plane', 'plane', 'parent')):
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
        super(DJIKFKLeg, self).run()
        #end_ctrl = self.ik_end_ctrl.value
        #self._ik_pole_vec_ctrl.add_space_switch(end_ctrl, space=self._END_CTRL_NAME)
