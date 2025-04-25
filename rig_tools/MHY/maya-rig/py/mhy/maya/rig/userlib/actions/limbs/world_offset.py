from maya import cmds

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName

import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const


class WorldOffset(bl.BaseLimb):
    """World offset limb.

    It creates root offset hierarchy for a character rig.

    :limb type: world_offset
    """

    _LIMB_TYPE = 'world_offset'
    _REQUIRE_WS_ROOT = False
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint

    _UI_ICON = 'world_offset'

    def __init__(self, *args, **kwargs):
        """Initializes a new limb object."""
        super(WorldOffset, self).__init__(*args, **kwargs)
        # lock and hide a few unused parameters
        for name in ('part', 'side', 'parent_limb'):
            self.param(name).ui_visible = False
            self.param(name).editable = False

    def marker_data(self):
        """Marker system definition."""
        return

    def build_marker_skeleton(self):
        """Re-implemented to build the root joint at origin."""
        if not cmds.objExists(const.RIG_SKEL_ROOT):
            Node.create('transform', name=const.RIG_SKEL_ROOT)
        if cmds.objExists(const.ROOT_JOINT):
            raise RuntimeError(
                'Root joint {} already exists'.format(const.ROOT_JOINT))
        joint = Node.create(
            'joint', name=const.ROOT_JOINT, clear_selection=True)
        joint.set_parent(const.RIG_SKEL_ROOT)
        self._set_rig_skeleton([[joint]])

    def _setup_ctrl_vis(self):
        """No ctrl vis hook up."""
        return

    def start(self):
        """Re-implemented to parent this limb to the rig global root."""
        super(WorldOffset, self).start()
        if cmds.objExists(const.LIMB_ROOT):
            self.limb_root.value.set_parent(const.LIMB_ROOT)

    def run(self):
        """Builds the limb ctrl rig."""
        ctrl_scale = (2, 2, 2)
        name = NodeName(self.ctrl_root, desc=None, ext='CTRL')

        layout_ctrl = self.add_ctrl(
            name=name,
            scale=ctrl_scale,
            group_exts=None)

        name = name.replace_num(1)
        offset01 = self.add_ctrl(
            name=name,
            parent=layout_ctrl,
            scale=[i * .8 for i in ctrl_scale],
            color=(0, 0.5, 0.5),
            group_exts=None)

        name = name.replace_num(2)
        ctrl = self.add_ctrl(
            name=name,
            parent=offset01,
            scale=[i * .6 for i in ctrl_scale],
            color=(0.5, 0.5, 1),
            group_exts=None)

        self.rig_skeleton[0][0].constrain('parent', ctrl, maintainOffset=True)
