import maya.cmds as cmds

import mhy.protostar.core.parameter as pa

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.rig.base_limb as bl
import mhy.maya.rig.constants as const


class Hand(bl.BaseLimb):
    """Hand limb class.

    :limb type: hand
    """

    _LIMB_TYPE = 'hand'
    _DEFAULT_SIDE = 'L'
    _INPUT_SKEL_TYPE = const.InputSkelType.single_joint
    _REPLACE_BIND_SOCKET = True

    _UI_ICON = 'hand'

    # --- input parameters

    @pa.bool_param(default=True)
    def enable_scale(self):
        """If True, enable scale constraint."""

    @pa.bool_param(default=False)
    def ctrl_on_end_joint(self):
        """If True, build a ctrl on each finger end joint."""

    @pa.int_param(default=0, min_value=0)
    def finger_start_index(self):
        """The start joint index of each finger."""

    # --- end of parameter definition

    @property
    def arm_parent_limb(self):
        """Returns the arm parent limb. if any."""
        parent_limb = self.get_parent_limb()
        if parent_limb and parent_limb.limb_type == 'arm':
            return parent_limb

    def marker_data(self):
        """Marker system definition."""
        part = self.part.value
        side = self.side.enum_value
        base_name = NodeName(
            part=part, side=side, num=None, ext=const.EXT_MARKER)

        data = []

        # hand joint
        main_chain = {
            'aim_axis': 'x',
            'up_axis': 'y',
            'markers': [{
                'name': base_name,
                'position': (68.7, 139.8, 1.8),
                'rotation': None,
                'override': False}
            ]}
        data.append(main_chain)

        # fingers
        for desc, positions in zip(
                ('index', 'middle', 'ring', 'pinky', 'thumb'),
                (((72, 139.8, 3.1),
                  (76.6, 139.8, 4.1), (80.7, 139.9, 4.1), (83.1, 139.8, 4.1),
                  (85.0, 139.8, 4.1)),
                 ((72, 139.8, 2.1),
                  (76.8, 139.8, 2.5), (80.8, 139.9, 2.5), (83.2, 139.8, 2.5),
                  (85.5, 139.8, 2.5)),
                 ((72, 139.8, 1.2),
                  (76.5, 139.8, 0.9), (80.4, 139.9, 0.9), (82.8, 139.8, 0.9),
                  (85.1, 139.8, 0.9)),
                 ((72, 139.8, 0.4),
                  (75.9, 139.8, -0.9), (79.1, 139.9, -0.9), (81.1, 139.8, -0.9),
                  (83.0, 139.8, -0.9)),
                 ((70.9, 139.8, 4.8),
                  (70.9, 139.8, 7), (70.6, 139.8, 9.0), (70.9, 139.8, 11)))

        ):
            chain = {
                'aim_axis': 'x',
                'up_axis': 'y',
                'parent': main_chain['markers'][0]['name'],
                'plane_ids': (1, -1),
                'markers': []}
            for i, pos in enumerate(positions):
                if i == 0:
                    rot = None
                elif i == len(positions) - 1:
                    rot = 'parent' 
                else:
                    rot = 'aim'
                up = (0, 1, 0)
                if i > 0:
                    up = 'plane'
                name = NodeName(base_name, desc=desc, num=i)
                chain['markers'].append({
                    'name': name,
                    'position': pos,
                    'rotation': rot,
                    'up_type': up})

            data.append(chain)

        return data

    def resolve_input_skeleton(self):
        """Re-implemented to find finger joint chains
        from the main hand joint."""
        super(Hand, self).resolve_input_skeleton()
        skel = self.rig_skeleton
        finger_dict = {}
        part = NodeName(skel[0][0]).part
        for each in skel[0][0].get_hierarchy(skip_self=True):
            name = NodeName(each)
            if name.part != part:
                continue
            finger_dict.setdefault(name.desc, [])
            finger_dict[name.desc].append(each)
        for _, joints in finger_dict.items():
            skel.append(joints)
        self._set_rig_skeleton(skel)

    def connect_marker_system(self, parent_limb):
        """Connects this marker system to the parent marker system.
        Use "follow" connection mode if the parent is an arm or leg
        (to avoid overlapping markers).
        """
        parent_ms = parent_limb.marker_system
        if parent_ms:
            pmarker = parent_ms.get_marker(0, -1)
            mode = const.MarkerConnectMode.none
            if parent_limb.limb_type in ('arm', 'leg'):
                mode = const.MarkerConnectMode.follow
            self.marker_system.set_parent_marker(pmarker, mode=mode)

    def _reset_private_vars(self):
        """Resets private variables."""
        super(Hand, self)._reset_private_vars()
        self.__finger_chains = []

    def run(self):
        """Builds the limb ctrl rig."""
        hand_joint = self.rig_skeleton[0][0]

        # if connected to arm, hand ctrl will be replaced by wrist ctrl
        if self.arm_parent_limb:
            hand_ctrl = Node.create(
                'transform',
                name=NodeName(hand_joint, ext='REF'),
                parent=self.ctrl_root)
            self.add_constraint(
                'parent', hand_joint, hand_ctrl, maintainOffset=True)
            self.add_constraint(
                'scale', hand_joint, hand_ctrl, maintainOffset=True)
        else:

            hand_ctrl = self.add_ctrl(
                xform=hand_joint,
                ext='FKCTRL',
                shape='circle',
                scale=(2, 2, 2),
                rot_order=0,
                rot=(0, 0, 90))

            # add constraints
            self.add_constraint(
                'parent', hand_ctrl, hand_joint, maintainOffset=True)
            if self.enable_scale.value:
                self.add_constraint(
                    'scale', hand_ctrl, hand_joint, maintainOffset=True)

        self.ctrl_leaf_parent = hand_ctrl

        finger_start_index = self.finger_start_index.value
        for chain in self.rig_skeleton[1:]:
            finger_chain = None
            for i, joint in enumerate(chain):
                if not self.ctrl_on_end_joint.value and \
                   not joint.get_children(exact_type='joint'):
                    continue

                if i == finger_start_index:
                    finger_chain = FingerChain(
                        finger_name=NodeName(joint).desc, limb=self)
                    self.__finger_chains.append(finger_chain)

                if i == finger_start_index:
                    parent_name = hand_ctrl
                else:
                    parent_name = NodeName(joint.get_parent(), ext='FKCTRL')
                    if not cmds.objExists(parent_name):
                        parent_name = hand_ctrl

                ctrl = self.add_ctrl(
                    xform=joint,
                    parent=parent_name,
                    ext='FKCTRL',
                    rot=(0, 0, 90),
                    scale=(0.1, 0.1, 0.1),
                    shape='circle',
                    rot_order=0)

                if finger_chain and i >= finger_start_index:
                    finger_chain.add_finger(ctrl)
                target = ctrl.target
                if target:
                    self.add_constraint('parent', ctrl, target, maintainOffset=True)
                ctrl.lock('sv')

        # self.add_curl_spread()

    def set_bind_skeleton(self):
        """Sets the bind skeleton.
        Bind skeleton = rig skeleton - tip joints.
        """
        self.tag_bind_joint(self.rig_skeleton[0][0])
        if len(self.rig_skeleton) > 1:
            for i in range(1, len(self.rig_skeleton), 1):
                for j, joint in enumerate(self.rig_skeleton[i][:-1]):
                    if j == 0:
                        parent = self.rig_skeleton[0][0]
                    else:
                        parent = self.rig_skeleton[i][j - 1]
                    self.tag_bind_joint(joint, parent=parent)

    def add_curl_spread(self):
        """TODO add doc."""
        if not self.__finger_chains:
            self.warn('No finger chains found. Skip adding curl spread')
            return
        limb_root = self.limb_root.value

        # 1) Add Separate Curl Attributes
        limb_root.add_separator_attr(name='Curl_Part')
        all_curl_attr = self.add_limb_attr(
            'float', name='All_Curl', keyable=True,
            defaultValue=0, minValue=-10, maxValue=10)
        for fingers in self.__finger_chains:
            fingers.limb = self
            fingers.add_sep_curl()

        # 2) Add Separate Spread Attributes
        limb_root.add_separator_attr(name='Spread_Part')
        all_spread_attr = self.add_limb_attr(
            'float', name='All_Spread', k=True,
            defaultValue=0, minValue=-10, maxValue=10)
        for fingers in self.__finger_chains:
            fingers.limb = self
            fingers.add_sep_spread()

            # 3) Add All Curl Attributes
            # In order to optimize performance and reduce the number of nodes,
            # Curl and spread share some nodes
            #fingers.add_all_curl(all_curl_attr)

            # 4) Add All Spread Attributes
            #fingers.add_all_spread(all_spread_attr)


class FingerChain(object):
    """Finger chain class.

    Used to query data from each finger ctrl.
    """

    def __init__(self, limb=None, finger_name=''):
        """TODO doc."""
        self.limb = limb
        self.finger_name = finger_name

        self.__ctrls = []
        self.__pma_node = None
        self.__md_node = None
        self.__cp_node = None
        self.__st_node = None
        self.__cd_node = None

        # self.parentList = ['offsetNode', 'sdkNode']

    def __str__(self):
        """String represntation.

        example:
            thumb:[thumb_main_00_L_FKCTRL, thumb_main_01_L_FKCTRL]
        """
        if self.__ctrls:
            return '{}:{}'.format(self.finger_name, str(self.__ctrls))

    __repr__ = __str__

    @property
    def pma_node(self):
        """TODO doc."""
        return self.__pma_node

    @pma_node.setter
    def pma_node(self, node):
        """TODO doc."""
        self.__pma_node = node

    @property
    def md_node(self):
        """TODO doc."""
        return self.__md_node

    @md_node.setter
    def md_node(self, node):
        """TODO doc."""
        self.__md_node = node

    @property
    def cp_node(self):
        """TODO doc."""
        return self.__cp_node

    @cp_node.setter
    def cp_node(self, node):
        """TODO doc."""
        self.__cp_node = node

    @property
    def st_node(self):
        """TODO doc."""
        return self.__st_node

    @st_node.setter
    def st_node(self, node):
        """TODO doc."""
        self.__st_node = node

    @property
    def cd_node(self):
        """TODO doc."""
        return self.__cd_node

    @cd_node.setter
    def cd_node(self, node):
        """TODO doc."""
        self.__cd_node = node

    def _add_utility_node(self, index=0):
        """TODO doc."""
        name = NodeName(
            part=self.finger_name, desc='curlSpread', num=index, ext='MDNODE')
        self.md_node = Node.create('multiplyDivide', name=name)

        name = NodeName(name, ext='STNODE')
        self.st_node = Node.create('setRange', name=name)

        name = NodeName(name, ext='CDNODE')
        self.cd_node = Node.create('condition', name=name)

    def add_finger(self, ctrl):
        """TODO doc."""
        self.__ctrls.append(ctrl)

    def add_sep_curl(self):
        """TODO doc."""
        if not self.md_node:
            self._add_utility_node(index=0)

        anim_attr = self.limb.add_limb_attr(
            'float', name='{}_{}'.format(self.finger_name, 'Curl'),
            keyable=True, defaultValue=0, minValue=-10, maxValue=10)
        self.create_curl_connection(anim_attr, 'offset_node', order=2)

    def add_all_curl(self, all_curl_attr):
        """TODO doc."""
        self._add_utility_node(index=1)
        self.create_curl_connection(all_curl_attr, 'sdk_node', order=2)

    def add_sep_spread(self, **kwargs):
        """TODO doc."""
        anim_attr = self.limb.add_limb_attr(
            'float', name='{}_{}'.format(self.finger_name, 'Spread'),
            keyable=True, defaultValue=0, minValue=-10, maxValue=10)
        self.create_spread_connection(anim_attr, 'offset_node')

    def add_all_spread(self, all_spread_attr):
        """TODO doc."""
        inverse_attr = self.limb.add_nonkeyable_attr(
            'bool', name='{}_{}'.format(self.finger_name, 'SpreadInverse'))
        max_attr = self.limb.add_nonkeyable_attr(
            'float', defaultValue=0,
            name='{}_{}'.format(self.finger_name, 'SpreadMax'))
        min_attr = self.limb.add_nonkeyable_attr(
            'float', defaultValue=0,
            name='{}_{}'.format(self.finger_name, 'SpreadMin'))
        self.create_spread_connection(
            all_spread_attr, 'sdk_node',
            inverse_attr=inverse_attr,
            max_attr=max_attr,
            min_attr=min_attr)

    def add_curl_spread(self, all_curl_attr=None, all_spread_attr=None):
        """TODO doc."""
        if not self.md_node:
            self._add_utility_node(index=0)

        anim_attr = self.limb.add_limb_attr(
            'float', name='{}_{}'.format(self.finger_name, 'Curl'),
            keyable=True, defaultValue=0, minValue=-10, maxValue=10)
        self.create_curl_connection(anim_attr, 'offset_node', order=2)

        anim_attr = self.limb.add_limb_attr(
            'float', name='{}_{}'.format(self.finger_name, 'Spread'),
            keyable=True, defaultValue=0, minValue=-10, maxValue=10)
        self.create_spread_connection(anim_attr, 'offset_node')

        if all_curl_attr and all_spread_attr:
            self._add_utility_node(index=1)
            self.create_curl_connection(all_curl_attr, 'sdk_node', order=2)

            inverse_attr = self.limb.add_nonkeyable_attr(
                'bool', name='{}_{}'.format(self.finger_name, 'SpreadInverse'))
            max_attr = self.limb.add_nonkeyable_attr(
                'float', defaultValue=0,
                name='{}_{}'.format(self.finger_name, 'SpreadMax'))
            min_attr = self.limb.add_nonkeyable_attr(
                'float', defaultValue=0,
                name='{}_{}'.format(self.finger_name, 'SpreadMin'))
            self.create_spread_connection(
                all_spread_attr, 'sdk_node',
                inverse_attr=inverse_attr,
                max_attr=max_attr,
                min_attr=min_attr)

    def create_curl_connection(self, master, slave, order=0):
        """TODO doc."""
        master >> self.md_node.input1Z
        self.md_node.input2Z.value = -9

        self.st_node.maxZ.value = 20
        self.st_node.oldMaxZ.value = 90
        self.md_node.outputZ >> self.st_node.valueZ

        self.cd_node.operation.value = 5
        self.md_node.outputZ >> self.cd_node.firstTerm
        self.md_node.outputZ >> self.cd_node.colorIfTrueB
        self.st_node.outValueZ >> self.cd_node.colorIfFalseB

        for ctrl in self.__ctrls:
            parent_grp = getattr(ctrl, slave)
            parent_grp.set_rotate_order(order)
            self.cd_node.outColorB >> parent_grp.rotateZ

    def create_spread_connection(
            self, master, slave,
            inverse_attr=None, max_attr=None, min_attr=None):
        """TODO doc."""
        # TODO: Not sure if using floatConstant Node is a good idea here.
        #
        # It requires lookdev plugin to be loaded which is sometimes not the
        # case for riggers or animators.

        if inverse_attr:
            master >> self.md_node.input1Y
            self.md_node.input2Y.value = 4.5

            # negative
            min_attr >> self.st_node.minX
            self.st_node.maxX.value = 0
            self.st_node.oldMinX.value = -45
            self.st_node.oldMaxX.value = 0

            # positive
            self.st_node.minY.value = 0
            max_attr >> self.st_node.maxY
            self.st_node.oldMinY.value = 0
            self.st_node.oldMaxY.value = 45

            self.md_node.outputY >> self.st_node.valueX
            self.md_node.outputY >> self.st_node.valueY

            name = NodeName(
                part=self.finger_name, desc='spreadAll', num=0, ext='MDNODE')
            inverse_md_node = Node.create('multiplyDivide', name=name)

            ch_node = Node.create('choice', name=name.replace_ext('CHNODE'))

            name = name.replace_ext('FCNODE')
            p_fc_node = Node.create('floatConstant', name=name)
            p_fc_node.inFloat.value = 1
            p_fc_node.outFloat >> ch_node.attr('input[0]')

            name = name.replace_num(1)
            n_fc_node = Node.create('floatConstant', name=name)
            n_fc_node.inFloat.value = -1
            n_fc_node.outFloat >> ch_node.attr('input[1]')

            inverse_attr >> ch_node.selector
            ch_node.output >> inverse_md_node.input1X
            ch_node.output >> inverse_md_node.input1Y
            self.st_node.outValueX >> inverse_md_node.input2X
            self.st_node.outValueY >> inverse_md_node.input2Y

            name = NodeName(name, num=0, ext='CDNODE')
            cd_node = Node.create('condition', name=name)
            cd_node.operation.value = 5
            self.md_node.outputY >> cd_node.firstTerm
            inverse_md_node.outputX >> cd_node.colorIfTrueG
            inverse_md_node.outputY >> cd_node.colorIfFalseG

            parent_grp = getattr(self.__ctrls[0], slave)
            cd_node.outColorG >> parent_grp.ry

        else:
            master >> self.md_node.input1Y
            self.md_node.input2Y.value = 4.5

            self.st_node.maxY.value = 45
            self.st_node.minY.value = -45
            self.st_node.oldMaxY.value = 45
            self.st_node.oldMinY.value = -45
            self.md_node.outputY >> self.st_node.valueY

            parent_grp = getattr(self.__ctrls[0], slave)
            self.st_node.outValueY >> parent_grp.ry
