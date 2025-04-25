from mhy.maya.standard.name import NodeName

import mhy.maya.rig.constants as const
import mhy.maya.rig.userlib.actions.limbs.ikfk_chain_limb as ch


class IKFKArm(ch.IKFKChain):
    """IKFK arm class.

    :limb type: arm
    """

    _LIMB_TYPE = 'arm'
    _DEFAULT_SIDE = 'L'
    _END_CTRL_NAME = 'hand'

    _UI_ICON = 'arm'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value

        data = {
            'aim_axis': 'x',
            'up_axis': '-z',
            'markers': []}
        if self.free_end_marker.value:
            ending = None
        else:
            ending = 'parent'

        for desc, pos, cns, up in zip(
                ('shldr', 'elbow', 'wrist'),
                ((16, 139.8, .7), (42, 139.8, .5), (66, 139.8, 1.8)),
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


class DJIKFKArm(ch.DJIKFKChain):
    """Double joint IKFK arm class.

    :limb type: arm
    """

    _LIMB_TYPE = 'arm'
    _DEFAULT_SIDE = 'L'
    _END_CTRL_NAME = 'hand'

    _UI_ICON = 'arm'

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value

        data = {
            'aim_axis': 'x',
            'up_axis': '-z',
            'markers': []}
        if self.free_end_marker.value:
            ending = None
        else:
            ending = 'parent'

        for desc, num, pos, cns, up in zip(
                ('shldr', 'elbow', 'elbow', 'wrist'),
                (None, 0, 1, None),
                ((16, 139.8, .7), (39.2, 139.8, .5),
                 (41.4, 139.8, .5), (66, 139.8, 1.8)),
                ('aim', 'aim', 'aim', ending),
                ('plane', 'plane', 'plane', 'parent')):
            name = NodeName(
                part=part, desc=desc, side=side, num=num, ext=const.EXT_MARKER)
            data['markers'].append({
                'name': name,
                'position': pos,
                'rotation': cns,
                'up_type': up})

        return data
        
