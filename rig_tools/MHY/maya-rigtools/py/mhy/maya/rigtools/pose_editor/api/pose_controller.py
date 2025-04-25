"""
The controller class manage all the information related to the pose.
"""
import json
import os
import six
import gzip

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
from mhy.python.core.utils import increment_name
from mhy.maya.rigtools.pose_editor.api.pose import Pose
from mhy.maya.rig.constants import POSE_MESH_MSG_ATTR
from mhy.maya.rigtools.pose_editor.api.influence import Influence
import mhy.maya.rigtools.pose_editor.api.utils as utils
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.attribute import Attribute


class PoseController(object):
    """
    The controller class manage all the information related to the pose controller.
    """
    LOCATOR_TYPE = 0
    RIG_POSE_TYPE = 1
    cached_controller_map = {}
    POSE_MESH_MSG_ATTR = 'POSE_BASE_MESH'

    @classmethod
    def get_controller(cls, node_name=None):
        """
        Controller is managed in a dictionary.
        The function is used to access the controller by maya node name.
        """
        ctrl_node = None
        if not node_name:
            return None

        if node_name:
            if not Node.object_exist(node_name):
                if node_name in cls.cached_controller_map:
                    del cls.cached_controller_map[node_name]
                return
            ctrl_node = Node(node_name)

        controller = cls.cached_controller_map.get(node_name)
        if controller is None:
            controller = cls(ctrl_node)
            cls.cached_controller_map[node_name] = controller
            return controller
        return controller

    @classmethod
    def clear_cached_controllers(cls, *args, **kwargs):
        """
        Clear cached controllers and remove callback associated with them
        Args:
            *args:
            **kwargs:

        Returns:

        """
        cls.cached_controller_map.clear()

    @classmethod
    def create(cls, name, out_mesh, parent=None):
        """
        Create pose node and setup blendshape for pose workflow

        """
        pose_node = Node.create(
            'MHYCtrl',
            name=name,
            group_exts=[])

        if parent:
            pose_node.set_parent(parent)
        pose_node.shape.shape_type = 4
        pose_node.v.value = False
        pose_node.lock()
        shape_node = pose_node.get_shapes()[0]
        shape_node.controllerType.value = 1
        shape_node.add_attr('message', name=cls.POSE_MESH_MSG_ATTR)
        if not out_mesh:
            OpenMaya.MGlobal.displayError("Base Mesh is not defined. This will result in post process error")
            return
        base_mesh = Node(out_mesh)
        if not base_mesh.has_attr(pose_node.name):
            base_mesh.add_attr('message', name=pose_node.name)
        shape_node.attr(cls.POSE_MESH_MSG_ATTR) >> base_mesh.attr(pose_node.name)
        return cls(shape_node.name)

    def create_blend_shape(self):
        out_mesh = self.output_mesh
        if not out_mesh:
            OpenMaya.MGlobal.displayError("There's no out mesh of this pose controller")
            return
        bs_name = out_mesh.name + '_TARGET_BLENDSHAPE'
        if not Node.object_exist(bs_name):
            Node.create('blendShape',
                        out_mesh.name,
                        name=bs_name,
                        frontOfChain=True)
        return Node(bs_name)

    @classmethod
    def load(cls, data):
        if isinstance(data, six.string_types):
            input_file = open(data, 'r')
            with input_file:
                data_str = input_file.read()
                data = json.loads(data_str)
        if isinstance(data, dict):
            data = [data]

        pose_nodes = []
        for item in data:
            controller_name = item.get('pose_control')
            out_mesh = item.get('out_mesh')
            if Node.object_exist(controller_name):
                controller = PoseController(controller_name)
            else:
                controller = PoseController.create(controller_name, out_mesh=out_mesh)

            controller.set_data(item)
            ui_data = item.get('UI')
            if 'pose_tree' in ui_data:
                tree_data = ui_data.get('pose_tree')
                controller.pose_tree = tree_data
            else:
                controller.pose_tree = ui_data
            pose_nodes.append(controller)

        return pose_nodes

    def __init__(self, ctrl_node):
        self.ui_info = {}
        self.__neutral_mesh = None
        self.__symmetric_table = None
        self.current_targets = set()
        self.__poses = None
        self.selected_influences = set()
        self.__active_pose = None

        self.ctrl_node = Node(ctrl_node)

        self.sculpt_geo_set = '{}_SCULPT_GEOSET'.format(self.node_name)
        cmds.cycleCheck(evaluation=False)

    @property
    def poses(self):
        """
        Get poses in a dictionary mapped from pose name to Pose instance. If
        the data has been cached, return the cache.
        Returns:
            dict:
        """
        if self.__poses is not None:
            return self.__poses
        data = dict()
        for pose_name in self.pose_name_list:
            pose_instance = Pose(pose_name, self)
            data[pose_name] = pose_instance
        self.__poses = data
        return self.__poses

    def refresh_poses(self):
        self.clear_poses_cache()
        return self.poses

    def clear_poses_cache(self):
        """
        This method will clear all the cached data in this instance. Instance will recache data from
        maya scene next time any internal data is used

        """
        self.__poses = None

    @property
    def node_name(self):
        if self.ctrl_node:
            return self.ctrl_node.name
        return ""

    @property
    def maya_node_obj_handle(self):
        """
        Get MayaObjectHandele from the controller object if exists
        Returns:
            OpenMaya.MObjectHandle:

        """
        if self.ctrl_node:
            return self.ctrl_node.maya_handle

    @property
    def is_valid(self):
        """
        return False, if node is not valid.
        """
        if self.ctrl_node and self.ctrl_node.is_valid:
            return True
        return False

    @property
    def mhy_attribute_name(self):
        """
        get attribute name mhy information.
        """
        if self.is_valid:
            return '{}.mhy'.format(self.node_name)
        return None

    @property
    def alias_indices(self):
        controller_node_name = self.node_name
        if controller_node_name:
            return utils.get_alias_indices(controller_node_name, "facePose")
        print("Can't find controller node!")
        return None

    @property
    def active_pose(self):
        """
        get the current active pose.
        """
        return self.__active_pose

    @active_pose.setter
    def active_pose(self, value):
        """
        set the current active pose.
        """

        if isinstance(value, six.string_types):
            pose = self.find_pose(value)
            self.__active_pose = pose
        if value is None or isinstance(value, Pose):
            self.__active_pose = value

    @property
    def pose_tree(self):
        """

        Returns:
            dict: A dictionary of pose tree hierarchy

        """
        mhy_attribute_name = self.mhy_attribute_name
        data = dict()
        if mhy_attribute_name:
            data_str = cmds.getAttr(mhy_attribute_name)
            if not data_str:
                return {}
            data = json.loads(data_str)
        if 'UI' in data:  # Old format
            ui_info = data.get('UI')

            return ui_info.get('pose_tree', {})
        else:
            return data  # New format

    @pose_tree.setter
    def pose_tree(self, value):
        self.save_ui_data(value)

    @property
    def pose_name_list(self):
        """
        Get the pose names in a list directly from the maya node
        Returns:
            (list): A list of pose names
        """
        if self.ctrl_node:
            poses = [i.alias for i in self.ctrl_node.facePose]
            return poses
        return []

    @property
    def output_mesh(self):
        """
        Get the output mesh

        Returns:
            Mesh: The output mesh
            None: This target has no output mesh
        """
        dsts = self.ctrl_node.attr(PoseController.POSE_MESH_MSG_ATTR).destinations
        if dsts:
            dst_node = dsts[0].node
            if dst_node.type_name == 'transform':
                shapes = dst_node.get_shapes()
                if shapes:
                    return shapes[0]
            return dsts[0].node

    @property
    def target_blendshape(self):
        """
        Get the blend shape node on out mesh. All the target shapes will be created on
        it

        """
        out_mesh = self.output_mesh
        if not out_mesh:
            return
        bs = cmds.ls(cmds.listHistory(out_mesh.name), type='blendShape')
        if bs:
            return bs[0]

    @property
    def neutral_mesh(self):
        output_mesh = self.output_mesh
        if output_mesh:
            intermediate = output_mesh.get_intermediate_sibling()
            if intermediate:
                return intermediate

    @property
    def symmetric_table(self):
        neutral_mesh = self.neutral_mesh
        if not neutral_mesh:
            return
        table = utils.create_mirror_list([self.neutral_mesh.name])
        return table

    @property
    def target_mesh(self):
        dests = self.ctrl_node.attr(POSE_MESH_MSG_ATTR).destinations
        if dests:
            return dests[0].node.name

    @property
    def corrective_poses(self):
        """
        get the corrective poses of the current controller
        """
        return [p for p in self.poses.values() if p.is_corrective]

    def mesh_size(self):
        """
        Get the size of target mesh
        Returns:
            list: The size of the bounding box of mesh
             in x, y, z axises
        """
        return utils.mesh_size(self.target_mesh)

    def set_blendshape_weight(self, weight):
        if self.target_blendshape and cmds.objExists(self.target_blendshape):
            cmds.setAttr(self.target_blendshape + '.envelope', weight)

    @staticmethod
    def _load_pose_names_from_json():
        """
        load name json file under resources folder
        """
        resource_path = os.environ.get('MHY_RESOURCE_PATH')
        try:
            with open(resource_path+'/pose_names.json', 'r') as name_file:
                return json.load(name_file)
        except IOError:
            print("can't read from pose_names.json under " + resource_path
                  + ", please check the folder to see if file exists")
            return {}

    def reset(self, progress_lambda=None):
        """
        reset the controller.
        """
        if self.poses:
            self.reset_poses(self.poses.values(), progress_lambda)

    @ staticmethod
    def is_rig_controller(node_name):
        """
        Check if a controller is a pose rig controller.
        """
        mhy_attribute_name = '{}.{}'.format(node_name, 'controllerType')
        return cmds.getAttr(mhy_attribute_name) == PoseController.RIG_POSE_TYPE

    def select_node(self):
        """
        Select controller node in Maya scene.
        """
        node_name = self.node_name
        if node_name:
            cmds.select(node_name)

    @ staticmethod
    def _flatten_tree_leaves(pose_tree):
        """
        convert tree leaf nodes to a list
        """
        pose_list = []
        for value in pose_tree.values():
            if isinstance(value, dict):
                pose_list.extend(PoseController._flatten_tree_leaves(value))
            else:
                # The leave layer is a set, so we can't simple extend list,
                # instad, we have to append item one by one
                for name in value:
                    pose_list.append(name)
        return pose_list

    def get_unique_new_name(self, pose_name):
        """
        Get a unique name for new pose name by adding trailing number if necessary
        Args:
            pose_name(str): A name to query unique name with

        Returns:
            str: unique new name

        """
        if self.find_pose(pose_name):
            r_split = pose_name.rsplit('_', 1)
            pose_name = increment_name(r_split[0])
            if len(r_split) == 2:
                pose_name = pose_name + "_" + r_split[1]
            return self.get_unique_new_name(pose_name)

        return pose_name

    @staticmethod
    def _delete_pose_in_tree(pose_tree, pose_name):
        if isinstance(pose_tree, list) and pose_name in pose_tree:
            pose_tree.remove(pose_name)
        elif isinstance(pose_tree, dict):
            for sub_pose_tree in pose_tree.values():
                PoseController._delete_pose_in_tree(sub_pose_tree, pose_name)

    def delete_poses(self, pose_list):
        for pose_name in pose_list:
            self.delete_pose(
                pose_name=pose_name)

    def delete_pose(self, pose_name):
        pose = self.find_pose(pose_name)
        if pose:
            pose.reset(remove_influence=True)
            if pose.is_corrective:
                pose.delete_corrective()
            self.remove_pose_attribute(pose_name)
            del self.poses[pose_name]

    @staticmethod
    def _rename_pose_in_tree(pose_tree, old_name, new_name):
        if isinstance(pose_tree, list) and old_name in pose_tree:
            for i in range(len(pose_tree)):
                if pose_tree[i] == old_name:
                    pose_tree[i] = new_name
        elif isinstance(pose_tree, dict):
            for sub_pose_tree in pose_tree.values():
                PoseController._rename_pose_in_tree(
                    sub_pose_tree, old_name, new_name)

    @staticmethod
    def _add_pose_in_tree(pose_tree, pose_name, parent_path, index=0):
        if not isinstance(parent_path, list):
            parent_path = parent_path.split('|')
        parent_root = parent_path[0]
        new_parent_path = parent_path[1:]
        if parent_root in pose_tree:
            child_tree = pose_tree[parent_root]
            if isinstance(child_tree, dict):
                if not new_parent_path:
                    OpenMaya.MGlobal.displayError("Can't add pose as sibling of a another groups")
                else:
                    PoseController._add_pose_in_tree(child_tree, pose_name, new_parent_path, index)
            elif isinstance(child_tree, list):
                if not new_parent_path:
                    child_tree.insert(index, pose_name)
                else:
                    OpenMaya.MGlobal.displayError("Can't find valid group path")

    def rename_pose(self, pose, new_name):
        """

        Args:
            pose:
            new_name:

        Returns:

        """
        old_name = pose.name
        if new_name == old_name or new_name == pose.main_name:
            return

        dummy_pose = Pose(name=new_name, controller=self)

        new_name = self.get_unique_new_name(dummy_pose.name)
        if pose:
            pose.name = new_name
            self.poses[new_name] = pose
            del self.poses[old_name]
        return pose.name

    @staticmethod
    def get_attribute_names(node_name):
        indices = cmds.getAttr(node_name + ".facePose", multiIndices=True)
        attribute_names = []
        # stupid maya attribute is sparse and even it doesn't exist it still keep alias name.
        # so don't use for index in indices.
        if indices:
            for index in range(indices[-1]+1):
                index_attr_name = node_name + ".facePose[%d]" % index
                pose_name = cmds.aliasAttr(index_attr_name, query=True)
                if pose_name:
                    attribute_names.append(pose_name)
        return attribute_names

    def add_pose_attribute(self, pose_name):
        """
        Add the attribute for a target pose name
        Args:
            pose_name(str): The name of a pose

        Returns:
            int: THe 

        """
        node_name = self.node_name

        # need run  getAttr to createAttr
        self.remove_pose_alias(pose_name)
        index, index_attribute_name = utils.get_a_free_index_attribute(
            node_name, "facePose")
        attr = Attribute(index_attribute_name)
        _ = attr.value
        attr.alias = pose_name
        return index

    def remove_pose_attribute(self, pose_name):
        """
        Remove the pose related attributes
        Args:
            pose_name(str): The name of the pose


        """
        pose = self.find_pose(pose_name)
        if pose:
            input_attr = pose.input_attribute_full_name
            output_attr = pose.output_attribute_full_name

            if input_attr and cmds.objExists(input_attr):
                input_attr = Attribute(input_attr)
                try:
                    input_attr.remove()
                except RuntimeError:
                    OpenMaya.MGlobal.displayError('failed to remove {}'.format(input_attr))
            if output_attr and cmds.objExists(output_attr):
                output_attr = Attribute(output_attr)
                try:
                    output_attr.remove()
                except RuntimeError:
                    OpenMaya.MGlobal.displayError('failed to remove {}'.format(output_attr))
            self.remove_pose_alias(pose_name)

    def remove_pose_alias(self, pose_name):
        node_name = self.node_name
        if cmds.objExists('{}.{}'.format(node_name, pose_name)):
            Attribute('{}.{}'.format(node_name, pose_name)).alias = None

    def add_attributes(self, pose_list):
        """
        Make sure all pose names in the pose list will be added as attribute
        Args:
            pose_list:

        """
        node_name = self.node_name
        existing_pose_attributes = PoseController.get_attribute_names(
            node_name)
        poses = set(pose_list)
        for pose_name in poses:
            if pose_name not in existing_pose_attributes:
                self.add_pose_attribute(pose_name)

    def delete_key(self, pose=None,  weight=None):
        """
        Remove influences to the active pose.
        """
        if pose is None:
            pose = self.active_pose
        if not pose:
            OpenMaya.MGlobal.displayError("Failed to find active pose")
            return
        if weight is None:
            weight = pose.weight
        target = pose.get_target(weight)
        if target and target in self.current_targets:
            self.current_targets.remove(target)
        pose.delete_key(weight)

    def delete_all_keys(self):
        """
        Remove influences to the active pose.
        """
        pose = self.active_pose
        if pose:
            pose.delete_all_keys()

    def find_pose(self, pose_name):
        """
        Return the pose matching pose_name from poses dict
        Args:
            pose_name:

        Returns:

        """
        if not pose_name:
            return None
        return self.poses.get(pose_name)

    def get_pose(self, pose_name):
        """
        get the cached pose by name. If pose not exists in cache,
        create one
        Args:
            pose_name(str): Pose name

        Returns:
            (Pose): Pose instance
        """

        if not pose_name:
            return None

        pose = self.poses.get(pose_name)
        if not pose:
            pose = self.add_pose(pose_name)
        return pose

    def add_pose(self, pose_name):
        """
        Add a pose to this controller created associated attributes
        Args:
            pose_name(str): The name of the pose

        Returns:
            Pose: Created pose
        """
        pose = Pose(name=pose_name, controller=self)
        pose_name = pose.name
        if pose_name not in self.poses:
            self.add_pose_attribute(pose_name)
            self.poses[pose_name] = pose
            return pose
        else:
            return self.poses[pose_name]

    def get_poses(self, pose_check_func):
        """
        Add corrective pose for current shape.
        """
        poses = []
        for pose in self.poses.values():
            if pose_check_func(pose):
                poses.append(pose)
        return poses

    def get_mirror_pose(self, pose=None):
        """
        get the mirror pose of the current active pose.
        """
        if pose is None:
            pose = self.active_pose
        if not pose:
            return
        mirrored_name = pose.get_mirror_name()
        mirrored_pose = self.get_pose(mirrored_name)
        return mirrored_pose

    def do_at_neutral_pose(self, neutral_lambda, *args):
        none_zero_poses = self.reset_weights()
        if args:
            neutral_lambda(args)
        else:
            neutral_lambda()
        # restore other poses' weight.
        for pose_name, weight in none_zero_poses.items():
            pose = self.find_pose(pose_name)
            if pose:
                pose.weight = weight

    def add_neutral_key(self, pose):
        self.do_at_neutral_pose(neutral_lambda=pose.add_neutral_key)

    def key_current_pose(self):
        """
        save the active pose's driven key
        """
        pose = self.active_pose
        need_add_neutral_weight = pose.add_key()
        if need_add_neutral_weight:
            self.add_neutral_key(pose)

    def add_target(self, weight, pose=None):
        """
        Added a target at given weight
        Args:
            weight(float): A value between 0 and 10
            pose(Pose): Specific pose to add target

        Returns:

        """
        self.create_blend_shape()
        if not pose:
            pose = self.active_pose
        if not pose:
            return
        weight = round(weight, 2)
        if not pose.has_target(weight):
            added_target = pose.add_target(weight)
            return added_target

    def create_sculpt_mesh(self):
        """
        Create a sculpt mesh and connect msg attribute to this pose controller node
        Returns:
            Node: Created sculpt geo

        """
        node_name = self.node_name
        target_mesh = self.target_mesh

        if not target_mesh:
            OpenMaya.MGlobal.displayError(
                "Failed to find target mesh from this pose controller `{}`."
                " Please check if attribute{} has message connection to a "
                "valid deformed mesh".format(node_name, POSE_MESH_MSG_ATTR))
            return

        duplicate = cmds.duplicate(
            target_mesh,
            name="{}_SculptTarget".format(target_mesh))
        if not duplicate:
            return

        if not cmds.objExists(self.sculpt_geo_set):
            cmds.select(cl=True)
            cmds.sets(name=self.sculpt_geo_set)

        duplicate = duplicate[0]
        cmds.sets(duplicate, addElement=self.sculpt_geo_set)
        target_mesh_node = Node(self.target_mesh).get_shapes()[0]

        sculpt_mesh_node = Node(duplicate).get_shapes()[0]

        target_mesh_node.outMesh.connect(sculpt_mesh_node.inMesh)
        cmds.hide(self.target_mesh)
        return sculpt_mesh_node

    def remove_sculpt_mesh(self):
        """
        Remove the sculpt mesh and switch visibility of target mesh to on

        """
        cmds.setAttr('{}.visibility'.format(self.target_mesh), True)
        sculpt_geos = self.active_sculpt_mesh
        if sculpt_geos:
            cmds.delete(sculpt_geos)

    def save_sculpt_to_target(self, sculpt_mesh, pose=None, weight=None, threshold=0.001):
        """
        Save a sculpt geometry to a pose as target shape
        Args:
            sculpt_mesh:
            pose:
            weight:
            threshold:

        Returns:

        """
        self.create_blend_shape()
        if pose is None:
            pose = self.active_pose

        if not pose:
            OpenMaya.MGlobal.displayError("No active pose")
            return

        if weight is None:
            target_weight = pose.weight
        else:
            target_weight = weight

        if not sculpt_mesh or not cmds.objExists(sculpt_mesh):
            OpenMaya.MGlobal.displayError("No existing sculpt mesh passed in")
            return
        sculpt_mesh = Node(sculpt_mesh)
        if sculpt_mesh.type_name == 'transform':
            shapes = sculpt_mesh.get_shapes()
            if not shapes:
                return
            sculpt_mesh = shapes[0]

        sculpt_mesh = Node(sculpt_mesh)
        target_points = sculpt_mesh.get_points(space='object')
        current_weight = pose.weight
        target_weight = round(target_weight, 2)
        found_target = pose.add_target(weight=target_weight)

        if not found_target:
            OpenMaya.MGlobal.displayError("Failed to find target at weight {} from pose {}".format(
                current_weight,
                pose.name))
            return
        found_target.save_sculpt_to_target(target_points, threshold=threshold)
        pose.refresh_cache(False)

    @property
    def active_sculpt_mesh(self):
        if not cmds.objExists(self.sculpt_geo_set):
            return
        sculpt_geos = cmds.sets(self.sculpt_geo_set, query=True)
        return sculpt_geos

    @property
    def is_sculpting(self):
        return cmds.objExists(self.sculpt_geo_set) \
               and cmds.sets(self.sculpt_geo_set, query=True)

    def delete_target(self, pose=None, weight=None):
        """
        Delete a target from a pose at given weight or current weight
        Args:
            pose(None or Pose): If not given, use current active pose
            weight(None or float): If not given, use current weight

        """
        if pose is None:
            pose = self.active_pose
        if not pose:
            OpenMaya.MGlobal.displayError("There's no active pose currently")
            return
        if weight is None:
            weight = pose.weight
        target_weight = weight/10.0
        target = pose.get_target(target_weight)
        if target:
            pose.delete_target(target_weight)

    def reset_weights(self, exclude=None):
        """
        Reset the weights of all poses to 0.0
        Args:
            exclude(list): Exclude some poses from being reset

        Returns:
            (dict): The poses needs to be reset

        """
        need_update_poses = dict()
        for pose_name in self.pose_name_list:
            if exclude and pose_name not in exclude:
                pose = self.find_pose(pose_name)
                if pose:
                    current_weight = pose.weight
                    if current_weight != 0.0:
                        need_update_poses[pose_name] = current_weight
                        pose.weight = 0.0
        return need_update_poses

    def reset_pose(self, pose_name, remove_influence=False):
        """
        set the controller from IO
        """
        pose_instance = self.poses.get(pose_name)
        if not pose_instance:
            return
        self.do_at_neutral_pose(pose_instance.reset, remove_influence)

    @staticmethod
    def reset_poses(poses, progress_lambda=None):
        """
        set the controller from IO
        """
        pose_num = len(poses)
        for idx, pose in enumerate(poses):
            if progress_lambda:
                progress_lambda("Resetting pose({0}/{1}): {2}.".format(
                    idx,
                    pose_num,
                    pose.name),
                    100.0*float(idx)/float(pose_num))
            pose.reset(remove_influence=True)
        return None

    def set_data(self, data, progress_lambda=None):
        """
        set the controller from IO
        """
        self.reset(progress_lambda)
        ui_info = data.get('UI', {})
        self.ui_info = ui_info
        pose_collect_data = data['pose']
        pose_list = pose_collect_data.keys()
        for pose_name in pose_list:
            self.add_pose(pose_name)

        pose_num = len(pose_list)
        for idx, (pose_name, pose_data) in enumerate(pose_collect_data.items()):
            if progress_lambda:
                progress_lambda("Updating pose({0}/{1}): {2}.".format(idx, pose_num, pose_name),
                                100.0*float(idx)/float(pose_num))
            pose = self.get_pose(pose_name)
            influence_data = pose_data.get('influence')
            if influence_data:
                pose.set_neutral_pose(influence_data)
            if pose_data:
                pose.set_data(pose_data)

        return None

    def merge_data(self, data, pose_list=None, progress_lambda=None):
        """
        Merge data into this controller
        Args:
            data:
            pose_list:
            progress_lambda:

        Returns:

        """
        if isinstance(data, list):
            data = data[0]

        new_poses = list()
        poses = list()
        if pose_list is None:
            pose_list = self.pose_name_list

        for pose in pose_list:
            found_pose = self.find_pose(pose)
            if found_pose:
                poses.append(found_pose)
            else:
                OpenMaya.MGlobal.displayInfo("Added missing pose {}".format(pose))
                added_pose = self.add_pose(pose)
                poses.append(added_pose)
                new_poses.append(added_pose.name)

        self.reset_poses(poses, progress_lambda)
        pose_collect_data = data['pose']
        pose_num = len(poses)

        progress_lambda("Started Updating poses", 0)

        for idx, pose in enumerate(poses):
            if progress_lambda:
                progress_lambda("Updating pose({0}/{1}): {2}.".format
                                (idx, pose_num, pose.name),
                                100.0*float(idx)/float(pose_num))
            pose_data = pose_collect_data.get(pose.name)
            if pose_data:
                self.poses[pose.name] = pose
                influence_data = pose_data.get('influence')
                if influence_data:
                    pose.set_neutral_pose(influence_data)
                pose.set_data(pose_data)
        return new_poses

    @staticmethod
    def get_pose_root(pose_tree, root):
        if root is None:
            return pose_tree
        groups = root.split('/')
        utils.remove_all_in_list(groups, '')
        parent = {}
        pose_root = parent
        while groups and pose_tree:
            group_leaf = groups.pop(0)
            pose_tree = pose_tree.get(group_leaf)
            if isinstance(pose_tree, list):
                # it's the full path for a single pose.
                if len(groups) == 1 and groups[0] in pose_tree:
                    parent[group_leaf] = [groups[0]]
                    return pose_root
                # it's the full path for a group.
                elif not groups:
                    parent[group_leaf] = pose_tree
                    return pose_root
                else:
                    raise(RuntimeError("Invalid Pose Path:%s" % (root)))
            else:
                children = {}
            parent[group_leaf] = children
            parent = children
        return pose_tree

    def get_poses_under(self, root, make=False):
        if root is None:
            return self.poses.values()
        if root == '//CORRECTIVE':
            return self.corrective_poses
        prefix_len = len('//CORRECTIVE/')
        poses = []
        if root[:prefix_len] == '//CORRECTIVE/':
            pose_name = root[prefix_len:]
            pose = self.poses.get(pose_name)
            if pose is not None:
                return [pose]
            return poses
        pose_tree = self.get_pose_root(self.pose_tree, root)
        if pose_tree:
            pose_name_list = list(
                set(PoseController._flatten_tree_leaves(pose_tree)))
            for pose_name in pose_name_list:
                pose = self.find_pose(pose_name)
                if not pose and make:
                    pose = Pose(name=pose_name, controller=self)
                poses.append(pose)
        return poses

    @staticmethod
    def get_poses_data(pose_list, progress_lambda=None):
        """
        get current all poses data for IO.
        """
        data = dict()
        pose_num = len(pose_list)
        for idx, pose in enumerate(pose_list):
            if progress_lambda:
                progress_lambda("Getting pose({}/{}): {} information.".format(
                    idx, pose_num, pose.name), 100.0*float(idx)/float(pose_num))
            pose_data = pose.get_data()
            if pose_data:
                data[pose.name] = pose_data
        return data

    def get_data(self, root=None, progress_lambda=None):
        """
        get current data for IO.
        """
        pose_list = self.get_poses_under(root)
        data = dict()
        data['pose'] = self.get_poses_data(pose_list, progress_lambda)
        data['UI'] = self.ui_info
        return data

    def export_data(self, file_path=None, pose_list=None,
                    progress_lambda=None, compress=False):
        """
        Export data from this pose controller node. If a file path give,
        data will be written to disk
        Args:
            file_path(str):
            pose_list(list):
            progress_lambda(function):
            compress(bool): If compress data

        Returns:
            dict:

        """

        data = dict()
        if pose_list is None:
            pose_list = [self.get_pose(p) for p in self.pose_name_list]
        data['pose'] = self.get_poses_data(pose_list, progress_lambda)
        data['pose_control'] = self.node_name
        out_mesh = self.output_mesh
        if out_mesh:
            data['out_mesh'] = out_mesh.name

        data['UI'] = self.pose_tree
        if file_path:
            data_str = json.dumps(data,
                                  sort_keys=True,
                                  indent=4,
                                  separators=(',', ': '))
            if compress:
                data_str = data_str.decode('utf-8')
                with gzip.open(file_path, "w") as out_file:
                    out_file.write(data_str)
            else:
                with open(file_path, 'w') as out_file:
                    out_file.write(data_str)

        return data

    def load_data(self, file_path, progress_lambda=None):
        """
        load the Rigging Poses from a chosen file.
        """
        input_file = open(file_path, 'r')
        with input_file:
            data_str = input_file.read()
            data = json.loads(data_str)

        if isinstance(data, list):
            data = data[0]

        self.set_data(data, progress_lambda=progress_lambda)
        ui_data = data.get('UI')
        if 'pose_tree' in ui_data:
            tree_data = ui_data.get('pose_tree')
            self.pose_tree = tree_data
        else:
            self.pose_tree = ui_data

    @ staticmethod
    def _get_influence_name(name):
        if '_LIMB' in name:
            split_names = name.split('_LIMB')
            return split_names[0]+'_LIMB'
        split_names = name.split('_')
        if len(split_names) > 1:
            return '_'.join(split_names[:-1])
        return None

    def save_ui_data(self, data):
        """
        Save the pose tree data from the cached variable to maya node attribute
        Args:
            data(dict): Ui data

        """
        mhy_attribute_name = self.mhy_attribute_name
        if mhy_attribute_name:
            data_str = json.dumps(data)
            cmds.setAttr(mhy_attribute_name, data_str, type='string')

    # Corrective Pose Code.
    def get_corrective_pose_name(self, name):
        if name not in self.pose_name_list:
            return name
        last_underscore = name.rfind('_')
        idx = 0
        head_str = name
        if last_underscore > 0:
            tail_str = name[last_underscore+1:]
            if utils.is_int(tail_str):
                idx = int(tail_str)+1
                head_str = name[:last_underscore+1]
        else:
            return name+'_0'
        return head_str+'_'+str(idx)

    def create_pose(self, pose_name):
        """
        Create a new pose with a given pose name. If pose exists with the same
        pose name, unique name with trailing index will be used instead.
        Args:
            pose_name(str):

        Returns:
            Pose: Created pose instance
        """
        pose = Pose(name=pose_name, controller=self)
        pose_name = pose.name

        # Need to make sure created pose is having a unique name
        pose_name = self.get_unique_new_name(pose_name)
        pose.rename(pose_name)
        self.poses[pose_name] = pose
        self.add_attributes([pose_name])
        return pose

    def create_corrective_pose(self,
                               name,
                               drive_poses,
                               symmetry,
                               weight=Settings.maximum_weight):
        """
        Create a corrective pose from some drive poses. This method will setup
        rbf net work from some other pose output values.
        Args:
            name:
            drive_poses:
            symmetry:
            weight:

        Returns:

        """
        corrective_pose_name = self.get_corrective_pose_name(
            name)+'_'+Symmetry.to_str_table.get(symmetry, 'M')

        corrective_pose = self.add_pose(corrective_pose_name)
        corrective_pose.weight = weight
        corrective_pose.set_up_corrective_nodes(
            drive_poses=drive_poses,
            weight=weight)
        return corrective_pose

    def split_pose(self, pose, drivers=None, fall_off=0.7, influence=True, target=True):
        """
        Split a pose's influence or target based on distance to given drivers,
        Args:
            pose:
            drivers:
            fall_off:
            influence:
            target:

        Returns:

        """
        assert drivers, "No target drivers to associate influences with"
        assert isinstance(drivers, list) and len(drivers) > 1, "Valid drivers is a list longer than 2"
        drivers = [Node(driver) for driver in drivers]

        influence_data, target_data = None, None
        if influence:
            influence_data = self.__split_influence_data(pose, drivers, fall_off)

        if target:
            target_data = self.split_target_data(pose, drivers, self.target_mesh, fall_off)

        created_poses = []
        for driver in drivers:
            new_pose = self.create_pose(pose.name)
            self.add_attributes([new_pose.name])
            created_poses.append(new_pose)

            if influence_data:
                data = influence_data.get(driver.name)
                new_pose.set_neutral_pose(data)
                new_pose.set_influences_data(data)
            if target_data:
                data = target_data.get(driver.name)
                new_pose.set_targets_data(data)

        return created_poses

    @staticmethod
    def __split_influence_data(pose, drivers, fall_off=0.7):
        """
        Split the influence data of a pose by geqtting a list of weights for each driven based on
        driven's distance to given drivers.
        Args:
            pose:
            drivers:
            fall_off:

        Returns:

        """
        influence_data = pose.get_influences_data()
        neutral_values = Influence.get_neutral_values()

        drivers_positions = {driver: driver.get_translation(space="world", as_tuple=False)
                             for driver in drivers}
        out_data = {driver.name: {} for driver in drivers}

        for driven, influence_inst in pose.influences.items():
            node = Node(influence_inst.get_maya_node_name())
            node_position = node.get_translation(space="world", as_tuple=False)
            dists = [(node_position - drivers_positions[driver]).length() for driver in drivers]
            dist_pairs = [[driver.name, dist] for driver, dist in
                          sorted(zip(drivers, dists), key=lambda p: p[1])]
            closest_dist = dist_pairs[0][1]
            for pair in dist_pairs:
                dist = pair[1]
                pair[1] = max(1 - fall_off * (dist - closest_dist), 0)
            sum_dists = sum((i[1] for i in dist_pairs))
            inf_weights = {pair[0]: pair[1] / sum_dists for pair in dist_pairs}
            source_data = influence_data.get(driven)
            for driver, weight in inf_weights.items():
                if weight == 0:
                    continue
                out_data[driver][driven] = {}
                for attr, delta in source_data.items():
                    neutral = neutral_values.get(attr, 0)
                    out_data[driver][driven][attr] = {
                        key: {'v': neutral + (value.get('v', 0) - neutral) * weight} for key, value in
                        delta.items() if value != neutral}

        return out_data  # {driver: {driven : {att: {key: {v: value}, ...} ...} ...}}

    def split_target_data(self, pose, drivers, mesh, fall_off=0.7):
        target_data = pose.get_targets_data()
        if not target_data:
            return
        drivers_positions = [driver.get_translation(space="world", as_tuple=False)
                             for driver in drivers]

        vtx_count = self.output_mesh.num_vertices
        weight_list = []
        for idx in range(vtx_count):
            pos = cmds.xform(
                "{0}.vtx[{1}]".format(mesh, idx),
                worldSpace=True,
                translation=True,
                query=True)

            pos = OpenMaya.MVector(*pos)

            dists = [(pos - driver_pos).length() for driver_pos in drivers_positions]
            dist_pairs = [[driver, dist] for driver, dist in
                          sorted(zip(drivers, dists), key=lambda p: p[1])]
            closest_dist = dist_pairs[0][1]
            for pair in dist_pairs:
                dist = pair[1]
                pair[1] = max(1 - fall_off * (dist - closest_dist), 0)

            sum_dists = sum((i[1] for i in dist_pairs))
            inf_weights = {pair[0]: pair[1] / sum_dists for pair in dist_pairs}
            weight_list.append(inf_weights)  # [{driver0: weight, driver1: weight1 ...}, ...]

        out_data = {driver.name: {} for driver in drivers}
        for key, data in target_data.items():
            for driver in drivers:
                out_data[driver.name][key] = {'delta': []}
            delta_list = data['delta']
            for idx, delta in enumerate(delta_list):
                weight_distribution = weight_list[idx]  # {driver0: weight, driver1: weight1 ...}
                for driver in drivers:
                    weight = weight_distribution.get(driver, 0)
                    out_data[driver.name][key]['delta'].append([weight*d for d in delta])

        return out_data  # {driver: {key: [{driver0: weight, driver1: weight1 ...}, ...] ...} ...}

    def set_target_status(self, val):
        bs_name = self.target_blendshape
        if Node.object_exist(bs_name):
            current_state = cmds.autoKeyframe(state=True, query=True)
            cmds.autoKeyframe(state=False)
            try:
                Node(bs_name).set_attr('envelope', val)
            except RuntimeError:
                pass
            finally:
                cmds.autoKeyframe(state=current_state)

    def target_is_enabled(self):
        if not Node.object_exist(self.target_blendshape):
            return True
        bs_name = self.target_blendshape
        val = Node(bs_name).get_attr('envelope')
        if val > 0.5:
            return True
        return False

    def clean_up(self):
        self.clean_up_sparse_components_data()
        self.merge_targets_to_one_per_pose()
        self.clean_up_neutral_pose()

    def clean_up_sparse_components_data(self):
        bs_name = self.target_blendshape
        if not Node.object_exist(bs_name):
            return
        bs_node = Node(bs_name)
        out_mesh = bs_node.output_objects[0]
        num_vtx = out_mesh.num_vertices
        for tgt_group in bs_node.inputTarget[0].inputTargetGroup:
            for item in tgt_group.inputTargetItem:
                self.clean_up_sparce_item(item, num_vtx)
        OpenMaya.MGlobal.displayInfo("Done clean up blend shape")

    def clean_up_neutral_pose(self):
        anim_curves = list()
        for pose_name, pose in self.poses.items():
            for i in pose.get_anim_curves():
                anim_curves.append(i)

        anim_curves = list(set(anim_curves))
        for ac in anim_curves:
            cmds.setKeyframe(ac, value=0, float=0)
        cmds.dgdirty(cmds.ls(type='blendWeighted'))

    @staticmethod
    def clean_up_sparce_item(item, num_vtx):
        points_data = item.inputPointsTarget.value
        components_data = item.inputComponentsTarget.value
        if components_data:
            flatten_list = list()
            for comp in components_data:
                split = comp[comp.index('[') + 1:-1].split(":")
                if split[0] == '*':
                    flatten_list.extend(list(range(num_vtx)))
                elif len(split) == 1:
                    flatten_list.append(int(split[0]))
                else:
                    flatten_list.extend(list(range(int(split[0]), int(split[1]) + 1)))
            data_map = {idx: pnt for idx, pnt in zip(flatten_list, points_data)}
            points_data = [[0, 0, 0, 1]] * num_vtx
            for idx, pnt in data_map.items():
                points_data[idx] = pnt

            components_data = ['vtx[{}]'.format(i) for i in range(num_vtx)]
            item.inputPointsTarget.value = points_data
            item.inputComponentsTarget.value = components_data

    def merge_targets_to_one_per_pose(self):
        for _, inst in self.poses.items():
            inst.merge_target_keys_to_single_entry()


def add_corrective_drive(drive_pose, corrective_pose):
    """
    add pose to current corrective pose.
    """
    corrective_pose.add_corrective_drive(drive_pose)


def delete_corrective_drive(drive_pose, corrective_pose):
    corrective_pose.delete_corrective_drive(drive_pose)


def list_pose_controllers():
    """
    List all available pose controllers in the scene
    Returns:

    """
    controller_nodes = cmds.ls(type='mhyController', shortNames=True)
    rig_controller_nodes = [node for node in controller_nodes if is_pose_controller(node)]
    return rig_controller_nodes


def is_pose_controller(node_name):
    """
    Check if a controller is a pose rig controller.
    """
    mhy_attribute_name = '{}.{}'.format(node_name, 'controllerType')
    return cmds.getAttr(mhy_attribute_name) == PoseController.RIG_POSE_TYPE


def do_clean_up():
    pose_controllers = list_pose_controllers()
    for pc in pose_controllers:
        pc_inst = PoseController(pc)
        pc_inst.clean_up()
