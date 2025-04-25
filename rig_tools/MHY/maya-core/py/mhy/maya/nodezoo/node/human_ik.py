"""
This modules contains api for HIKCharacterNode node
"""
import re
from contextlib import contextmanager

from maya import cmds, mel, OpenMaya

from mhy.maya.nodezoo.node import Node, DependencyNode
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath


def _load_plugins():
    """Loads humanIK required plugins."""
    for plugin in ('mayaHIK', 'mayaCharacterization', 'OneClick'):
        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            cmds.loadPlugin(plugin, quiet=True)


@contextmanager
def in_hik_ui():
    """A contextmanager that allows an operation to be done
    with huamIK tool UI opened.
    This is important as some huamIk operations rely on the UI...
    """
    has_ui = 'hikCharacterControlsDock' in cmds.lsUI(dumpWidgets=True)
    if not has_ui:
        mel.eval('HIKCharacterControlsTool()')
    mel.eval('hikUpdateCharacterList()')
    mel.eval('hikUpdateSourceList()')
    yield
    if not has_ui:
        cmds.deleteUI('hikCharacterControlsDock')


def _mirror_hik_element_data(data):
    """Given a dict data with (hik element: node) pairs,
    Makes a mirrored copy of each pair, if it doesn't already exists.
    (The original data is preserved as well)

    Returns:
        dict: The mirrored data
    """
    m_data = {}
    for key, val in data.items():
        m_data[key] = val

        if key.startswith('Left'):
            m_key = key.replace('Left', 'Right', 1)
        elif key.startswith('Right'):
            m_key = key.replace('Right', 'Left', 1)
        else:
            continue

        if m_key not in data:
            m_val = NodeName.flip_node_name(val)
            m_data[m_key] = m_val

    return m_data


class HIKCharacterNode(DependencyNode):
    """
    HumanIK character Node
    """

    __NODETYPE__ = 'HIKCharacterNode'

    _ELEMENT_DICT = {}

    @classmethod
    def create(cls, name='Character1', skeleton=False):
        """Creates a new humanIK character.

        Args:
            name (str): Name of the character node.
            skeleteon (bool): If True, creates a default skeleton.

        Returns:
            HumanIK: The HIKCharacterNode object.
        """
        _load_plugins()

        if skeleton:
            mel.eval('hikCreateSkeleton()')
            char_node = cls(mel.eval('hikGetCurrentCharacter()'))
            char_node.rename(name)
            char_node.set_current()
            return char_node
        else:
            char_node = cls(mel.eval('hikCreateCharacter("{}")'.format(name)))
            char_node.set_current()
            return char_node

    # --- helpers

    @property
    def skeleton_generator_node(self):
        """The skeleton generator node."""
        if self.has_attr('SkeletonGenerator'):
            gen = self.list_connections(
                attr='SkeletonGenerator',
                source=True, destination=False, plugs=False)
            if gen:
                return gen[0]

    @property
    def custom_rig_node(self):
        """The custom rig retargeter node."""
        node = self.list_connections(
            attr='message',
            source=False, destination=True,
            plugs=False, type='CustomRigRetargeterNode')
        if node:
            return node[0]

    @property
    def element_dict(self):
        """Returns the custom rig element dict."""
        if not self.__class__._ELEMENT_DICT:
            self.__cache_rig_elements()
        return self.__class__._ELEMENT_DICT

    @property
    def skeleton_locked(self):
        """The skeleton locked state."""
        return mel.eval('hikIsDefinitionLocked("{}")'.format(self))

    @skeleton_locked.setter
    def skeleton_locked(self, locked):
        """Sets the skeleton locked state."""
        if self.skeleton_locked != locked:
            self.set_current()
            mel.eval('hikToggleLockDefinition()')

    # --- helpers

    def __cache_rig_elements(self):
        """Caches {rig element name: id} pairs."""
        self.__class__._ELEMENT_DICT = {}
        e = None
        i = 0
        while True:
            e = mel.eval(
                'hikCustomRigElementNameFromId("{}", {});'.format(self, i))
            if e:
                self.__class__._ELEMENT_DICT[e] = i
                i += 1
            else:
                break

    def element_id_from_name(self, element_name):
        """Returns the rig element id associated with a element name."""
        return self.element_dict.get(element_name, -1)

    def __set_option_widget_value(self, name, value):
        """Sets a humanIK option widget value."""
        with in_hik_ui():
            for widget in cmds.lsUI(long=True, type='optionMenuGrp') or []:
                if name in widget:
                    cmds.optionMenuGrp(widget, edit=True, value=value)
                    return

    def set_current(self):
        """Sets this character as the current character."""
        mel.eval('hikSetCurrentCharacter("{}")'.format(self))

    # --- global operations

    def rename(self, new_name):
        """Renames this HumanIK character.

        Args:
            new_name (str): The new character name.

        Returns:
            None
        """
        old_name = self.name
        if old_name == new_name:
            return
        self.name = new_name
        new_name = self.name
        mel.eval('hikSetCurrentCharacter("{}")'.format(new_name))
        mel.eval(
            'hikRenameConnectedNodes("{}", "{}")'.format(new_name, old_name))

    def validate_skeleton(self):
        """Validates the skeleton.

        Returns:
            bool
        """
        return bool(mel.eval('hikValidateSkeleton("{}");'.format(self)))

    def set_source(self, source):
        """Sets the source human ik character.
        TODO this method only works for skel to skel connections.

        Args:
            source (str or HIKCharacterNode): The source character.
                or None.

        Returns:
            None
        """
        source = str(source).strip()

        # validate source
        if source.lower() not in ('none', 'stance'):
            if not cmds.objExists(source):
                cmds.warning('Source HIK character not found: {}'.format(source))
                return
            if cmds.nodeType(source) != self.type_name:
                cmds.warning('{} is not a HIK character node.'.format(source))
                return

        # source name needs a whitespace prefix
        source = ' ' + source

        # TODO is there a better way than setting the hik UI directly??
        self.set_current()
        self.__set_option_widget_value('hikSourceList', source)
        mel.eval('hikUpdateCurrentSourceFromUI()')
        mel.eval('hikUpdateContextualUI()')

    # --- skeleton generator

    def set_skeleton_attr(self, **kwargs):
        """Sets the result skeleton by updating the skeleton generator.

        Args:
            kwargs: generator attribute and its new value.
                e.g. self.set_skeleton_attr(SpineCount=3)
        """
        if not kwargs:
            return

        gen = self.skeleton_generator_node
        if not gen:
            cmds.warning(
                'HumanIK character {} has no skeleton generator.'.format(self))

        for attr, val in kwargs.items():
            gen.attr(attr).value = val

        with in_hik_ui():
            self.set_current()
            mel.eval('hikSyncSkeletonGeneratorFromUI();')

    # --- skeleton definition

    def get_joint(self, element_name):
        """Returns the joint associated with an element.

        Args:
            element_name (str): A humanIK element name.

        Returns:
            Joint
        """
        if self.has_attr(element_name):
            node = self.list_connections(
                attr=element_name,
                source=True, destination=False, plugs=False)
            if node:
                return node[0]

    def set_joint(self, element_name, joint, mirror=False):
        """Sets a joint node.

        Args:
            element_name (str): A humanIK element name.
            joint (str or node): The joint node.
            mirror (bool): Sets the mirrored joint too?

        Returns:
            None
        """
        # validate args
        if not self.has_attr(element_name):
            cmds.warning('Invalid joint element name: {}'.format(element_name))
            return
        if not cmds.objExists(joint):
            cmds.warning('Joint not found: {}'.format(joint))
            return

        element_id = self.element_id_from_name(element_name)
        mel.eval('hikSetCharacterObject("{}", "{}", {}, 0)'.format(
            joint, self, element_id))

        # make connection
        # joint = Node(joint)
        # if not joint.has_attr('Character'):
        #     joint.add_attr('message', name='Character')
        # joint.Character >> self.attr(element_name)
        # for attr in ('MinRLimit', 'MaxRLimit'):
        #     for ax in 'xyz':
        #         self.attr(element_name + attr + ax).value = 0

        # do mirror
        if mirror:
            if element_name.startswith('Left'):
                m_element = element_name.replace('Left', 'Right', 1)
            elif element_name.startswith('Right'):
                m_element = element_name.replace('Right', 'Left', 1)
            else:
                return

            m_joint = NodeName.flip_node_name(joint)
            if cmds.objExists(m_joint):
                self.set_joint(m_element, m_joint, mirror=False)

    def load_joint_data(self, joint_dict, mirror=False):
        """Loads joint data from a dict.

        Args:
            joint_dict (dict): A dict containing {element_name: joint} pairs.
            mirror (bool): Sets the mirrored joint too?

        Returns:
            None
        """
        if mirror:
            data = _mirror_hik_element_data(joint_dict)
        else:
            data = joint_dict
        for element_name, joint in data.items():
            self.set_joint(element_name, joint, mirror=False)

    def load_joint_data_to_generator(self, joint_dict, fit=True, attach=True):
        """Gather skeleton attrs from a joint dict and applies
        them to the result skeleton.

        Args:
            joint_dict (dict): A dict containing {element_name: joint} pairs.
            fit (bool): If True, fit the HIK joint.
            attach (bool): If True, attach the HIK joint.

        Returns:
            None
        """
        joint_dict = _mirror_hik_element_data(joint_dict)

        attr_dict = {
            'SpineCount': 0,
            'NeckCount': 0,
            'ShoulderCount': 0,
            'NbLowerArmRollBones': 0,
            'NbUpperArmRollBones': 0,
            'NbLowerLegRollBones': 0,
            'NbUpperLegRollBones': 0,
            'FingerJointCount': 0,

            'WantIndexFinger': False,
            'WantMiddleFinger': False,
            'WantRingFinger': False,
            'WantPinkyFinger': False,
            'WantThumb': False,
            'WantExtraFinger': False,

            'WantInHandJoint': False,
            'WantFingerBase': False,

            'WantIndexToe': False,
            'WantMiddleToe': False,
            'WantRingToe': False,
            'WantPinkyToe': False,
            'WantFootThumb': False,
            'WantBigToe': False,

            'WantInFootJoint': False,
            'WantToeBase': False,

            'WantHipsTranslation': False,
        }

        # gather generator attributes
        processed = set()
        for element_name, joint in joint_dict.items():
            if not joint:
                continue

            element_name = element_name.replace('Left', '').replace('Right', '')
            if element_name in processed:
                continue
            processed.add(element_name)

            if element_name.startswith('Spine'):
                attr_dict['SpineCount'] += 1
            elif element_name.startswith('Neck'):
                attr_dict['NeckCount'] += 1
            elif re.search(r'.*Shoulder.*', element_name):
                attr_dict['ShoulderCount'] += 1
            elif re.search(r'.*HipsTranslation.*', element_name):
                attr_dict['WantHipsTranslation'] = True

            elif re.search(r'.*ForeArmRoll.*', element_name):
                attr_dict['NbLowerArmRollBones'] += 1
            elif re.search(r'.*ArmRoll.*', element_name):
                attr_dict['NbUpperArmRollBones'] += 1

            elif re.search(r'.*UpperLegRoll.*', element_name):
                attr_dict['NbUpperLegRollBones'] += 1
            elif re.search(r'.*LegRoll.*', element_name):
                attr_dict['NbLowerLegRollBones'] += 1

            elif re.search(r'.*InHand.*', element_name):
                attr_dict['WantInHandJoint'] = True
            elif re.search(r'.*FingerBase.*', element_name):
                attr_dict['WantFingerBase'] = True
            elif re.search(r'.*HandIndex.*', element_name):
                attr_dict['WantIndexFinger'] = True
                attr_dict['FingerJointCount'] += 1
            elif re.search(r'.*HandMiddle.*', element_name):
                attr_dict['WantMiddleFinger'] = True
            elif re.search(r'.*HandRing.*', element_name):
                attr_dict['WantRingFinger'] = True
            elif re.search(r'.*HandPinky.*', element_name):
                attr_dict['WantPinkyFinger'] = True
            elif re.search(r'.*HandThumb.*', element_name):
                attr_dict['WantThumb'] = True
            elif re.search(r'.*HandExtraFinger.*', element_name):
                attr_dict['WantExtraFinger'] = True

            elif re.search(r'.*InFoot.*', element_name):
                attr_dict['WantInFootJoint'] = True
            elif re.search(r'.*ToeBase.*', element_name):
                attr_dict['WantToeBase'] = True
            elif re.search(r'.*FootIndex.*', element_name):
                attr_dict['WantIndexToe'] = True
                attr_dict['ToeJointCount'] += 1
            elif re.search(r'.*FootMiddle.*', element_name):
                attr_dict['WantMiddleToe'] = True
            elif re.search(r'.*FootRing.*', element_name):
                attr_dict['WantRingToe'] = True
            elif re.search(r'.*FootPinky.*', element_name):
                attr_dict['WantPinkyToe'] = True
            elif re.search(r'.*FootThumb.*', element_name):
                attr_dict['WantFootThumb'] = True
            elif re.search(r'.*FootExtraFinger.*', element_name):
                attr_dict['WantBigToe'] = True

        # gather generated skeleton
        self.set_skeleton_attr(**attr_dict)

        # fit the generated skeleton
        if fit:
            for element_name, joint in joint_dict.items():
                if not joint or not cmds.objExists(joint):
                    continue

                hik_joint = self.get_joint(element_name)
                if not hik_joint:
                    continue

                children = hik_joint.get_children(type_='transform')
                for c in children:
                    c.set_parent(None)

                mtx = Node(joint).get_matrix(space='world')
                hik_joint.set_matrix(mtx, space='world')

                for c in children:
                    c.set_parent(hik_joint)

            ref = self.get_joint('Reference')
            ref.make_identity(
                translate=False, rotate=True, scale=True, apply=True)

        # attach the generated skeleton
        if attach:
            for element_name, joint in joint_dict.items():
                if not joint or not cmds.objExists(joint):
                    continue

                hik_joint = self.get_joint(element_name)
                if not hik_joint:
                    continue

                hik_joint.constrain('parent', joint, maintainOffset=False)

    def flatten_arm_joints(self):
        """Flattens the arm joints."""

        for side, ref_vec in zip(
                ('Left', 'Right'),
                (OpenMaya.MVector(1, 0, 0), OpenMaya.MVector(-1, 0, 0))):
            joints = []
            for name in ('Arm', 'ForeArm', 'Hand'):
                joint = self.get_joint(side + name)
                if not joint:
                    cmds.warning('{} has no {} joint.'.format(self, name))
                    break
                joints.append(joint)

            if len(joints) != 3:
                continue

            for i in (0, 1):
                long_axis = joints[i].long_axis
                vec = joints[i + 1].get_translation(
                    space='world', as_tuple=False)
                vec = vec - joints[i].get_translation(
                    space='world', as_tuple=False)
                long_axis = mmath.closest_axis_to_vector(joints[i], vec)

                old_vec = mmath.axis_to_vector(joints[i], long_axis)
                quat = OpenMaya.MQuaternion(old_vec, ref_vec)
                mtx = joints[i].get_matrix(
                    space='world', as_transform=True, as_tuple=False)
                mtx.rotateBy(quat, OpenMaya.MSpace.kWorld)
                joints[i].set_matrix(mtx, space='world')

            joints[0].make_identity(
                translate=False, rotate=True, scale=True, apply=True)

    # --- custom ctrl rig definition

    def create_custom_rig(self):
        """Creates a custom rig setup. Or returns the existing one."""
        if not self.custom_rig_node:
            mel.eval('hikCreateCustomRig("{}")'.format(self))
        return self.custom_rig_node

    def set_custom_ctrl(self, element_name, ctrl, mirror=False):
        """Sets a ctrl node.

        Args:
            element_name (str): A humanIK custom rig element name.
            ctrl (str): The custom rig ctrl.
            mirror (bool): Sets the mirrored ctrl too?

        Returns:

            None
        """
        if not cmds.objExists(ctrl):
            cmds.warning('Custom ctrl not found: {}'.format(ctrl))
            return

        # get open xform channels
        ctrl = Node(ctrl)
        open_attrs = ctrl.get_open_xform_attrs()
        if not open_attrs:
            cmds.warning('Custom ctrl has no open channels: {}'.format(ctrl))
            return

        # get element id
        element_id = self.element_id_from_name(element_name)
        if element_id == -1:
            cmds.warning('Invalid rig element: {}'.format(element_name))
            return

        # create default mappings
        self.create_custom_rig()
        mel.eval('hikCustomRigClearMapping({})'.format(element_id))
        retargeter = mel.eval('RetargeterGetName("{}")'.format(self))
        for ch in 'tr':
            if ch not in open_attrs:
                continue
            mel.eval(
                'RetargeterAddMapping("{}", "{}", "{}", "{}", {});'.format(
                    retargeter, element_name, ch.upper(), ctrl, element_id))
        # do mirror
        if mirror:
            if element_name.startswith('Left'):
                m_element = element_name.replace('Left', 'Right', 1)
            elif element_name.startswith('Right'):
                m_element = element_name.replace('Right', 'Left', 1)
            else:
                return

            m_ctrl = NodeName.flip_node_name(ctrl)
            if cmds.objExists(m_ctrl):
                self.set_custom_ctrl(m_element, m_ctrl, mirror=False)

    def load_custom_ctrl_data(self, ctrl_dict, mirror=False):
        """Loads custom ctrl data from a dict.

        Args:
            ctrl_dict (dict): A dict containing {element_name: ctrl} pairs.
            mirror (bool): Sets the mirrored ctrl too?

        Returns:
            None
        """
        if mirror:
            data = _mirror_hik_element_data(ctrl_dict)
        else:
            data = ctrl_dict
        for element_name, ctrl in data.items():
            self.set_custom_ctrl(element_name, ctrl, mirror=False)
