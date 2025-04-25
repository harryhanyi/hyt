"""
The Influence class represents the pose drivens.
"""
import json
from maya import cmds

from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.rig import constants
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.attribute import Attribute


class Influence(object):
    """
    The influence class manage all the influence information.
    """
    ctrl = 'FKCTRL'
    pose = 'POSE'
    pose_driven_attr = constants.POSE_DRIVEN_ATTR
    attributes = {'tx': {'neutral': 0.0}, 'ty': {'neutral': 0.0},
                  'tz': {'neutral': 0.0}, 'rx': {'neutral': 0.0},
                  'ry': {'neutral': 0.0}, 'rz': {'neutral': 0.0}}

    def __init__(self, node_name, pose):
        """

        Args:
            node_name(str): The name of this node
            pose(Pose): Pose instance
        """
        self.name = Node(node_name).name
        if '_LIMB' in node_name:
            self.is_limb = True
            split_names = node_name.split("_LIMB")
            self.name = split_names[0]+"_LIMB"
        else:
            self.is_limb = False
        self.pose = pose
        node_name = self.get_maya_node_name()
        self.attributes = self.get_pose_driven_attributes(node_name)

    def __repr__(self):
        return "<0>.{1}: '{2}'> at <{3}>".format(
            self.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self))
        )

    @property
    def symmetry(self):
        """
        Get the mirror name.
        """
        if '_L_' in self.name:
            return Symmetry.LEFT

        elif '_R_' in self.name:
            return Symmetry.RIGHT
        return Symmetry.CENTER

    @classmethod
    def get_neutral_values(cls):
        return {attr: neutral.get('neutral', 0) for attr, neutral in cls.attributes.items()}

    @staticmethod
    def get_pose_driven_attributes(node_name):
        """
        Get pose driven attribute information. If a dictionary override found
        in attribute named 'poseDrivenAttributes', return its value is driven
        attributes and neutral values
        Args:
            node_name(str): The name of the driven node

        Returns:
            dict: The influence attributes

        """
        driven_node = Node(node_name)
        if driven_node.has_attr(Influence.pose_driven_attr):
            pose_driven_attr_info_str = driven_node.get_attr(Influence.pose_driven_attr)
            try:
                pose_driven_attr_info = json.loads(pose_driven_attr_info_str)
                return pose_driven_attr_info
            except Exception:
                attributes = pose_driven_attr_info_str.split(' ')
                pose_driven_attr_info = dict()
                for attribute in attributes:
                    attribute = attribute.strip('\n')
                    if cmds.attributeQuery(attribute, node=node_name, exists=True):
                        pose_driven_attr_info[attribute] = {'neutral': 0.0}
                if pose_driven_attr_info:
                    return pose_driven_attr_info
        return Influence.attributes

    def get_anim_curve(self, attr_name):
        """
        get the animCurve which affect this influence.
        """
        node = self.get_maya_node_name()
        attr_full_name = '{}.{}'.format(node, attr_name)
        if not cmds.objExists(attr_full_name):
            return

        attr_inst = Attribute(attr_full_name)
        source_node = attr_inst.source_node
        if not source_node:
            return
        if source_node.type_name.startswith('animCurve'):
            return source_node.name
        elif source_node.type_name == 'blendWeighted':
            for i in source_node.input:
                input_source = i.source_node
                if input_source.type_name.startswith('animCurve'):
                    s = input_source.input.source
                    if s and s.is_element and s.index == Attribute(self.pose.output_attribute_full_name).index:
                        return input_source.name
        return None

    def get_attribute(self, attribute, default=None):
        try:
            node_obj = Node(self.get_maya_node_name())
            return node_obj.get_attr(attribute)
        except ValueError:
            return default

    def get_maya_node_name(self, suffix=None):
        """

        convenient function to get node name with suffix.

        """
        if self.is_limb:
            return self.name + "Shape"

        node_name = self.name
        if suffix:
            node_name = '{}_{}'.format(self.name, suffix)

        if not cmds.objExists(node_name):
            raise(RuntimeError("Can't find the influence node {}.".format(node_name)))
        return node_name

    def add_key(self, driver_name, weight=None):
        """

        save the pose driven keys

        """

        driven = self.get_maya_node_name()
        if weight is None:
            weight = cmds.getAttr(driver_name)
        for attribute in self.attributes:
            driven_attribute = '{}.{}'.format(driven, attribute)
            cmds.setDrivenKeyframe(
                driven_attribute,
                inTangentType="linear",
                outTangentType="linear",
                currentDriver=driver_name,
                driverValue=weight)

    def reset(self):
        """
        delete all the input nodes affect influence by the pose.
        """
        # clean up history.
        anim_curves = []
        for attr in self.attributes.keys():
            anim_curve = self.get_anim_curve(attr)
            if anim_curve:
                anim_curves.append(anim_curve)
        if anim_curves:
            cmds.delete(anim_curves)
        self.reset_neutral_position()

    def add_neutral_key(self, driver_name):
        """
        add the key for neutral pose.
        Args:
            driver_name:

        Returns:

        """

        pose_node_name = self.get_maya_node_name()

        for attribute, info in self.attributes.items():
            attr_name = '{}.{}'.format(pose_node_name, attribute)
            if not cmds.objExists(attr_name):
                continue
            ctrl_attr = Attribute(attr_name)
            if not ctrl_attr.is_free_to_change:
                continue
            neutral_val = info.get('neutral', 0)

            cmds.setDrivenKeyframe(
                attr_name,
                inTangentType="linear",
                outTangentType="linear",
                currentDriver=driver_name,
                driverValue=0,
                value=neutral_val
            )

    def reset_neutral_position(self):
        """
        reset the pose to neutral.
        """
        ctrl_node_name = self.get_maya_node_name()
        for attribute, info in self.attributes.items():
            ctrl_attr = Attribute(ctrl_node_name+"."+attribute)
            if ctrl_attr and ctrl_attr.is_free_to_change:
                ctrl_attr.value = info['neutral']

    def get_mirror_name(self):
        """
        Get the mirror name.
        """
        if '_L_' in self.name:
            return self.name.replace('_L_', '_R_')

        elif '_R_' in self.name:
            return self.name.replace('_R_', '_L_')
        return self.name

    @property
    def main_name(self):
        return self.name.replace('_L_', '').replace('_R_', '').replace('_M_', '')


def _is_influence_node(name, match_str_list, index=-1, split='_'):
    """
    Check if object is valid influence object.
    Args:
        name:
        match_str_list:
        index:
        split:

    Returns:

    """
    if '_LIMB' in name:
        return True
    split_names = name.split(split)
    for match_str in match_str_list:
        if match_str == split_names[index]:
            return True

    obj = Node(name)
    if obj.has_attr(Influence.pose_driven_attr):
        return True
    return False


def get_influence_names(objects=None):
    """
        Get the poses related to selected objects.
    Args:
        objects(list): Override selected object list

    Returns:
        set: Influence object names
    """
    if objects is None:
        objects = cmds.ls(selection=True)
    if not objects:
        return None
    influences = set([node for node in objects
                      if _is_influence_node(node, match_str_list=[Influence.ctrl, Influence.pose])])
    return influences


