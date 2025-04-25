"""
The Pose class.
The pose data
"""
import bisect
import sys
import random
from functools import partial

from maya import cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.rigtools.pose_editor.api.influence import Influence
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.rigtools.pose_editor.api.anim_curve import AnimCurve
from mhy.maya.rigtools.pose_editor.api.target import PoseTarget
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.nodezoo.attribute import Attribute
from mhy.maya.nodezoo.node import Node
from mhy.maya.rigtools.pose_editor.api import utils


class Pose(Symmetry):
    """
    The Pose class manage all the information related to the pose.

    Pose instance does caching influences and targets data.


    """
    out_attr_name = 'facePose'
    in_attr_name = 'facePoseDriver'
    override_attr_name = 'facePoseOverride'

    value_range = [0.0, Settings.maximum_weight]

    def __init__(self, name, controller):
        """

        Args:
            name(str): Pose Name
            controller(.api.PoseController):PoseController instance
        """
        self.controller = controller
        Symmetry.__init__(self, name)

        self.__influence_keys = list()
        self.__weight_keys = list()

        # ------------------------------------------------------------------------
        # Instance Caches
        # ------------------------------------------------------------------------
        self.tmp_iter_count_dict = dict()  # A counter container can work with thread worker
        self.tmp_influence_dict = dict()  # A data container can work with thread worker
        self.tmp_target_dict = dict()  # A counter container can work with thread worker
        self.__influences = None
        self.__targets = None

        self._current_corrective_index = 1

        SignalManager.single_step_cache_finished_signal.connect(self.update_single_step_cache_data_slot)

    def __repr__(self):
        return "<PoseEditor.{0}: '{1}' at <{2}>>".format(
            self.__class__.__name__,
            self.name,
            hex(id(self))
        )

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------

    @property
    def name(self):
        """
        Get the name of this pose
        Returns:

        """
        return self.get_name()

    @name.setter
    def name(self, new_name):
        """
        Set name of this pose. This action will update the alias for associated
        attribute on pose controller node.
        Args:
            new_name:

        Returns:

        """
        old_name = self.name
        if old_name == new_name:
            return
        controller_node_name = self.controller.node_name
        if controller_node_name:
            output_attribute_full_name = self.output_attribute_full_name
            alias_attribute = controller_node_name + "." + self.name
            cmds.aliasAttr(alias_attribute, remove=True)
            cmds.aliasAttr(new_name, output_attribute_full_name)
            self.rename(new_name)

    @property
    def key_number(self):
        """
        Get the number of keys
        Returns:
            int: Number of keys
        """
        if not self.weight_keys:
            return 0
        return len(self.weight_keys)

    @property
    def weight_keys(self):
        target_keys = self._get_target_weights()
        target_keys = [10.0*i for i in target_keys]
        influence_keys = self.__influence_keys
        return sorted(list(set(target_keys + influence_keys)))

    @property
    def is_corrective(self):
        """
        Check if this pose if a corrective pose based on the source node type,
        corrective pose is connected with rbfSolver node
        Returns:
            bool: If this pose is corrective pose
        """
        if not self.input_attribute_full_name:
            return False
        input_attr = Attribute(self.input_attribute_full_name)
        source = input_attr.source
        if source:
            return source.node.type_name == 'rbfSolver'
        return False

    @property
    def weight(self):
        """
        Get the current weight of the pose.
        if force_update=True, it'll update pose weight from
        Pose controller node's weight attribute in Maya.
        """
        input_attribute_name = self.input_attribute_name
        if not input_attribute_name or not cmds.objExists(self.input_attribute_full_name):
            return 0
        return cmds.getAttr(self.input_attribute_full_name)

    @weight.setter
    def weight(self, w):
        """
        Set pose's weight, It'll update Pose controller
        node's weight attribute in Maya
        """
        current_state = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(state=False)
        try:
            if self.is_corrective:
                cmds.setAttr(self.output_attribute_full_name, w)
            else:
                cmds.setAttr(self.input_attribute_full_name, w)
        except RuntimeError as e:
            pass
        finally:
            cmds.autoKeyframe(state=current_state)

    @property
    def index(self):
        """
        Get the index of this pose attribute
        Returns:

        """
        if not Node.object_exist(self.controller.node_name):
            return None
        if not cmds.objExists("{}.{}".format(self.controller.node_name, self.name)):
            return None
        face_pose_attr = self.controller.ctrl_node.attr(self.name)
        if face_pose_attr:
            return face_pose_attr.index
        return -1

    @property
    def output_attribute_name(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        index = self.index
        if index is None:
            return ""
        return "{}[{}]".format(Pose.out_attr_name, index)

    @property
    def input_attribute_name(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        index = self.index
        if index is None:
            return
        return "{}[{}]".format(Pose.in_attr_name, index)

    @property
    def input_attribute_full_name(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        input_attribute_name = self.input_attribute_name
        if not input_attribute_name:
            return ""
        return self.controller.node_name + "." + self.input_attribute_name

    @property
    def override_attribute_name(self):
        """
        get pose's override attribute name of Maya Pose Controller Node.
        """
        index = self.index
        if index is None:
            return ""
        return "{}[{}]".format(Pose.override_attr_name, index)

    @property
    def output_attribute_full_name(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        output_attribute_name = self.output_attribute_name
        if not output_attribute_name:
            return ""
        return self.controller.node_name + "." + self.output_attribute_name

    @property
    def override_attribute_full_name(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        override_attr_name = self.override_attribute_name
        if not override_attr_name:
            return ""
        return self.controller.node_name + "." + self.override_attribute_name

    @property
    def output_weight_plug(self):
        """
        get pose's driver attribute name of Maya Pose Controller Node.
        """
        try:
            face_pose_attr = self.controller.ctrl_node.attr(self.name)
        except RuntimeError:
            return None
        return face_pose_attr.long_name

    # ------------------------------------------------------------------------
    # Influence methods
    # ------------------------------------------------------------------------

    @property
    def influences(self):
        """
        Get all the influence instances by iterate outputs from the
        output weight plug. Only objects connected by animation curves
        will be considered as influences.
        If influences have been cached, return cached data instead.

        To clear cache, call clear_influence_cache method.

        Returns:
            dict: A dictionary of node name verses Influence instance map
        """
        if self.has_influence_cache():
            return self.__influences
        self.start_cache_job(False)
        return self.__influences

    def has_influence_cache(self):
        """
        Check if influences have been cached to this pose instance
        Returns:
            bool: True if influences have been cached, otherwise false
        """
        return self.__influences is not None

    def finish_influence_cache(self, results):
        """

        Args:
            results:

        Returns:

        """
        results = results or {}
        self.__influences = {i: Influence(node_name=i, pose=self) for i in results}
        SignalManager.influence_cache_finished_signal.emit(self)

    def clear_influence_cache(self):
        """
        This method will clear all the cached influences data in this instance. Instance will recache data from
        maya scene next time any internal data is used

        """
        self.__influences = None
        self.__influence_keys = list()

    # ------------------------------------------------------------------------
    # Targets methods
    # ------------------------------------------------------------------------

    @property
    def targets(self):
        """
        Get all the target instances by iterate outputs from the
        output weight plug. Only objects connected with blend shape
        through animation curves will be considered as targets.
        If targets have been cached, return cached data instead.

        To clear cache, call clear_target_cache method.

        Returns:
            dict: A dictionary of weight verses Target instance map
        """
        if self.has_target_cache():
            return self.__targets
        self.start_cache_job(False)
        return self.__targets

    def has_target_cache(self):
        """
        Check if targets have been cached to this pose instance
        Returns:
            bool: True if targets have been cached, otherwise false
        """
        return self.__targets is not None

    def finish_target_cache(self, results):
        """
        Cache target data to this pose instance.
        results: {@blendShape name: [weight element attributes]}

        """
        pose_entry = results.get(self.controller.target_blendshape)
        data = {}
        if pose_entry:
            pose_entry = Attribute(pose_entry[0])
            idx = pose_entry.index
            bs = self.controller.target_blendshape
            bs_node = Node(bs)
            for i in bs_node.inputTarget[0].inputTargetGroup[idx].inputTargetItem:
                weight = i.index
                weight = float(weight - 5000) / 1000
                tgt = PoseTarget(pose_entry, weight=weight, pose=self)
                data[weight] = tgt
        self.__targets = data
        SignalManager.target_cache_finished_signal.emit(self)

    def clear_target_cache(self):
        """
        This method will clear all the cached target data in this instance. Instance will recache data from
        maya scene next time any internal data is used

        """
        self.__targets = None

    def merge_target_keys_to_single_entry(self):
        """
        This method is for transferring old pose rig to new style by merging multiple inbetween targets
        into on single target item with multiple target items
        Returns:

        """
        _, target_results = self.__get_connected_nodes(using_threading=False)
        bs = self.controller.target_blendshape
        bs_node = Node(bs)
        connected_weights = target_results.get(bs)
        if not connected_weights:
            return

        first_connection = Attribute(connected_weights[0])
        target_idx = first_connection.index

        for i in connected_weights:
            attr = Attribute(i)
            idx = attr.index
            alias_split = attr.alias.split('_')
            weight = 10.0
            if alias_split:
                weight = float(alias_split[-3])
            source_item = bs_node.inputTarget[0].inputTargetGroup[idx].inputTargetItem[6000]
            points_data = source_item.inputPointsTarget.value
            component_value = source_item.inputComponentsTarget.value
            weight = int((weight/10)*1000 + 5000)
            target_item_attr = bs_node.inputTarget[0].inputTargetGroup[target_idx].inputTargetItem[weight]
            target_item_attr.inputPointsTarget.value = points_data
            target_item_attr.inputComponentsTarget.value = component_value
            if target_idx != idx:
                attr.remove()
                bs_node.inputTarget[0].inputTargetGroup[idx].remove()

    def _get_target_weights(self):
        """
        Get the target weights from this pose in a sorted list
        Returns:
            list: weights list
        """
        return sorted([weight for weight in self.targets])

    def update_delta_curves(self):
        """
        Updated set driven key animation curves to blend shape
        targets based on the weight values

        """
        self.clear_target_cache()
        if not self.targets:
            return

        pose_out_plug = self.output_weight_plug
        target_input_plug = self.targets.values()[0].input_attr

        cmds.setDrivenKeyframe(
            target_input_plug,
            inTangentType="linear",
            outTangentType="linear",
            currentDriver=pose_out_plug,
            driverValue=0,
            value=0
        )
        cmds.setDrivenKeyframe(
            target_input_plug,
            inTangentType="linear",
            outTangentType="linear",
            currentDriver=pose_out_plug,
            driverValue=10,
            value=1
        )

    def has_target(self, weight):
        """
        Determines if this pose has target at given weight value
        Args:
            weight(float): The weight value

        Returns:
            bool: If the target exists at given weight
        """
        if not self.targets:
            return False
        return weight in self.targets

    def enable_all_targets(self):
        if not self.targets:
            return
        for _, target in self.targets.items():
            target.enable = True

    def disable_all_targets(self):
        if not self.targets:
            return
        for _, target in self.targets.items():
            target.enable = False

    def add_target(self, weight=None):
        """
        Add a new delta pose.
        Args:
            weight(float): The pose weight range are fix to (0 - 10), it will be map to (0-1) for target creation

        Returns:

        """
        if weight is None:
            weight = self.weight
        weight = weight/10.0
        target = self.targets.get(weight, None)
        if target:
            return target

        bs_node = Node(self.controller.target_blendshape)
        target_attr = None
        if cmds.objExists('{}.{}'.format(bs_node.name, self.name)):
            # Weight attribute with alias the same as this pose exists, assume this is the weight plug for targets
            target_attr = Attribute('{}.{}'.format(bs_node.name, self.name))

        if self.targets:  # There's existing target in on this pose, then just need to add an in between
            sibling_target = list(self.targets.values())[0]
            if target_attr and target_attr.alias != sibling_target.weight_attribute.alias:
                OpenMaya.MGlobal.displayError("There is an existing target attribute "
                                              "aliased {}".format(target_attr.alias))
                return
            new_target = PoseTarget(sibling_target.weight_attribute, weight=weight, pose=self)
            bs_node.add_in_between(index=sibling_target.index, value=weight)

        else:  # Need to create a new pose target for this pose
            if target_attr:
                OpenMaya.MGlobal.displayWarning("There is an existing target aliased {}".format(target_attr.name))
                target_weight_attr = target_attr
            else:
                target_weight_attr = bs_node.add_target(self.name, with_target_object=False)

            new_target = PoseTarget(target_weight_attr, pose=self, weight=weight)
            cmds.setDrivenKeyframe(target_weight_attr,
                                   inTangentType="linear",
                                   outTangentType="linear",
                                   currentDriver=self.output_attribute_full_name,
                                   driverValue=0,
                                   value=0)

            cmds.setDrivenKeyframe(target_weight_attr,
                                   inTangentType="linear",
                                   outTangentType="linear",
                                   currentDriver=self.output_attribute_full_name,
                                   driverValue=10,
                                   value=1)
        self.controller.current_targets.add(new_target)
        self.refresh_cache(False)
        return new_target

    def get_target(self, weight=None):
        """
        Get the delta pose at the weight, return None if does not exist.
        Args:
            weight(float): weight value

        Returns:
            Target: Found Target instance
            None: No target found at given weight
        """

        if weight is None:
            weight = self.weight
        return self.targets.get(weight, None)

    def delete_target(self, weight):
        """
        Delete target associated with this pose at given weight
        Args:
            weight(float): Weight value. A valid weight value falls in 0.0-1.0

        """
        target = self.targets.get(weight)
        if target:
            target.destroy()
        self.refresh_cache(False)

    def clear_targets(self):
        """
        Clear all the targets associated with this pose

        """
        for key, target in self.targets.items():
            target.destroy()
        self.__targets = dict()

    def get_targets_data(self):
        """
        Get the target data in a dictionary mapped from weight to specific bs data
        Returns:
            dict: Targets data
        """
        data = dict()
        for weight, target in self.targets.items():
            target_data = target.get_data()
            data[10.0*weight] = target_data
        return data

    def get_closest_target(self, weight, tolerance=0.01):
        weight = weight/10.0
        target_weights = self.targets.keys()
        if weight is None:
            return
        sort_by_dist = sorted(target_weights, key=lambda a: abs(a-weight))
        if not sort_by_dist:
            return
        closest_weight = sort_by_dist[0]
        if abs(closest_weight-weight) < tolerance:
            return closest_weight

    def reset(self, remove_influence=False):
        """
        reset the Pose's information.
        delete all the influence and targets.

        Args:
            remove_influence(bool): If remove existing influence

        Returns:
            list: deleted nodes
        """

        self.weight = 0.0
        affected_nodes = []
        if remove_influence:
            affected_nodes = self.get_anim_curves()
            if affected_nodes:
                cmds.delete(list(affected_nodes))
            for _, influence in self.influences.items():
                influence.reset_neutral_position()
            self.__influences = dict()
        self.clear_targets()
        return affected_nodes

    def is_range_default(self):
        """
        Check if the weight range is default.
        Used to skip saving data if it's default.
        """
        return self.value_range[0] == 0 and self.value_range[1] == Settings.maximum_weight

    def select_influences(self, influences):
        """
        Select influences in the maya scene
        Args:
            influences(list): A list of influence names

        """
        if influences:
            nodes = []
            for influence_name in influences:
                inf = self.influences.get(influence_name)
                if not inf:
                    continue
                node = inf.get_maya_node_name()
                nodes.append(node)

            cmds.select(nodes)

    def select_all_influences(self):
        """
        select all the influences of the pose.
        """
        influences = [i for i in self.influences]
        if influences:
            cmds.select(influences)

    def delete_influence(self, node_name):
        """
        Remove influence from the pose.
        """
        influence = self.influences.get(node_name)
        if influence is None:
            return
        del self.influences[node_name]
        influence.reset()

    def delete_influences(self, influence_names=None):
        """
        Remove influences from the pose.
        """
        if influence_names is None:
            influence_names = self.influences.keys()
        for influence_name in influence_names:
            self.delete_influence(influence_name)
        self.refresh_cache(False)

    def add_influence(self, name):
        """
        Add influence object to the pose.
        Args:
            name(str): The name of added influence object

        Returns:
            Influence: successfully added influence
            None: Failed to add influence

        """

        _ = self.influences  # Make sure it's fully cached
        if not Node.object_exist(name):
            OpenMaya.MGlobal.displayWarning("Failed to add influence object {}"
                                            " because it's not in the scene".format(name))
            return
        try:
            influence = Influence(name, pose=self)
            influence.add_neutral_key(self.output_attribute_full_name)
            self.__influences[influence.name] = influence
            return influence
        except RuntimeError:
            return

    def add_influences(self, influence_names):
        """
        Add influences to the pose.
        """
        result = []
        for name in influence_names:
            if self.add_influence(name):
                result.append(name)
        return result

    def add_neutral_key(self):
        """
        save the the neutral pose for weight 0
        """
        weight = self.weight
        self.weight = 0.0
        influences = self.influences.values()
        for influence in influences:
            influence.add_neutral_key(
                self.output_attribute_full_name)
        # reset the weight to original weight
        if weight != 0.0:
            self.weight = weight

    def has_weight_key(self, weight):
        """
        Check if the given weight is a valid key on this pose
        Args:
            weight(float): Weight value

        Returns:
            bool: If weight is in the weight keys
        """
        return weight in self.weight_keys

    def add_key(self, weight=None):
        """
        add the pose key at current weight.
        """
        if weight is None:
            weight = self.weight
        need_add_neutral = False
        if not self.weight_keys:
            need_add_neutral = True
        target = self.get_target(weight)
        if target:
            target.save_sculpt()
        if weight not in self.weight_keys:
            bisect.insort(self.weight_keys, weight)
        influences = self.influences.values()
        for influence in influences:
            influence.add_key(
                self.output_attribute_full_name)
        return need_add_neutral

    def find_closet_index(self, weight):
        """
        this function should be replaced with curveAnimFn to get closest index.
        """
        if not self.weight_keys:
            return None
        dist = weight - self.weight_keys[0]
        index = 0
        for key in self.weight_keys[1:]:
            if weight <= key:
                if key - weight < dist or index == 0:
                    return index + 1
                return index
            index += 1
            dist = weight - key
        return None

    def delete_key(self, weight=None):
        """
        remove the pose key closest to weight.

        Args:
            weight(float): Delete key at a given weight value. If None passed in, use current weight


        """

        if weight is None:
            weight = self.weight
        if not weight:
            return
        pose_index = self.find_closet_index(weight)
        if pose_index is None:
            return

        self.delete_target(weight)

        anim_curves = self.get_anim_curves()

        for anim_curve in anim_curves:
            curve_fn = utils.get_anim_curve_fn(anim_curve)
            if curve_fn and curve_fn.numKeys > 0:
                # curve_index is not equal to pose_index. because target delta is sparse
                curve_index = curve_fn.findClosest(weight)
                if abs(curve_fn.input(curve_index) - weight) > Settings.epsilon:
                    return
                curve_fn.remove(curve_index)
        self.refresh_cache(False, verbose=False)
    # ------------------------------------------------------------------------
    # Cache methods
    # ------------------------------------------------------------------------

    def refresh_cache(self, using_threading=True, verbose=False):
        self.clear_target_cache()
        self.clear_influence_cache()
        self.start_cache_job(using_threading=using_threading, verbose=verbose)

    def __get_connected_nodes(self, using_threading=True, verbose=False):
        """
        This is a private method to query connected nodes from the output plug of the
        pose controller node based on an optional filter callable.

        Args:
            using_threading(bool): If this method is in threading mode. If so, evaluate each
            output connection in evalDeferred
            verbose(bool): If print out debug information
        Returns:
            tuple: Cached influence data and targets data


        """
        if not self.output_weight_plug or not cmds.objExists(self.output_weight_plug):
            return None, None
        out_plug = Attribute(self.output_weight_plug)
        if using_threading:
            # To thread caching, firstly allocate a place holder dict for result from thread work
            rand_id = random.uniform(0, 1000)
            while rand_id in self.tmp_influence_dict.keys():
                rand_id = random.uniform(0, 1000)

            self.tmp_influence_dict[rand_id] = {}
            self.tmp_target_dict[rand_id] = {}
            self.tmp_iter_count_dict[rand_id] = 0
            destinations = out_plug.destinations
            num_of_dst = len(destinations)
            if num_of_dst:
                for dst in out_plug.destinations:
                    cmds.evalDeferred(partial(self.analyze_destination_plug,
                                              dst,
                                              None,
                                              None,
                                              True,
                                              rand_id,
                                              num_of_dst,
                                              verbose))
            else:
                self.finish_influence_cache(self.tmp_influence_dict[rand_id])
                self.finish_target_cache(self.tmp_target_dict[rand_id])
                self.tmp_target_dict.pop(rand_id)
                self.tmp_iter_count_dict.pop(rand_id)
            return None, None

        else:
            influence_results = {}
            target_results = {}
            for dst in out_plug.destinations:
                self.analyze_destination_plug(
                    dest_plug=dst,
                    influence_result=influence_results,
                    target_result=target_results,
                    using_threading=using_threading,
                    verbose=verbose)

            return influence_results, target_results

    def update_single_step_cache_data_slot(self, info):
        """
        This method is a callback function connected to signal emitted once each step cache finished.
        It will check if all the steps are finished. If so, clear the temporary cache for current thread
        work and push data to finish cache jobs.
        Args:
            info(list): A list of three elements:
            1.the pose instance: Who did this update
            2. result_id: The id for query cached data from tmp dictionaries
            3. total number of steps: For this thread work. It is the number of out put connections from
             output attribute on the pose controller associated with this pose

        """
        inst, result_id, total_number = info
        if not inst == self:
            return

        iter_count = self.tmp_iter_count_dict.get(result_id)
        if iter_count >= total_number:
            inf_result = self.tmp_influence_dict.get(result_id)
            self.finish_influence_cache(inf_result)

            tgt_result = self.tmp_target_dict.get(result_id)
            self.finish_target_cache(tgt_result)

            self.tmp_influence_dict.pop(result_id)
            self.tmp_target_dict.pop(result_id)
            self.tmp_iter_count_dict.pop(result_id)

    def analyze_destination_plug(
            self,
            dest_plug,
            influence_result=None,
            target_result=None,
            using_threading=True,
            result_id=None,
            total_length=0,
            verbose=False):
        """
        This is the single step for the caching system which iterate the downstream from one plug connected to
        the output attribute on pose controller.

        Args:
            dest_plug: The connected destination attribute
            influence_result(dict or None): If provided for none
            threading mode, this action will modify it by adding
            influence data to it. In threading mode, this argument will be not used.

            target_result(dict or None): If provided for none threading mode, this action will modify it by adding
            target data to it. In threading mode, this argument will be not used.

            using_threading(bool): If this action is called in threading mode

            result_id(int): A id associated with a batch of thread work to
            get influence and target temp cache from
            an instance variable.

            total_length(int): The total length of this thread batch.
            It will be passed to next step through signal so
            the slot receiver will know if the thread batch is done.
            verbose(bool): If print out debug information


        """
        def append_connected_attr(result_dict, node_name,  attr_name):
            if node_name in result_dict:
                result_dict[node_name].append(attr_name)
            else:
                result_dict[node_name] = [attr_name]
        if result_id is not None:
            influence_result = self.tmp_influence_dict.get(result_id)
            target_result = self.tmp_target_dict.get(result_id)
        dst_node = dest_plug.node
        if dst_node.type_name.startswith('animCurve'):
            anim_keys = dst_node.get_keys()
            if verbose:
                OpenMaya.MGlobal.displayInfo("{}: number of keys: {}".format(dst_node, anim_keys))
            self.__influence_keys = sorted(list(set(self.__influence_keys + anim_keys)))
            outputs = dst_node.output.destinations
            for out in outputs:
                out_node = out.node
                if out_node.type_name == 'blendWeighted':
                    blend_weighted_outs = out_node.output.destinations
                    for k in blend_weighted_outs:
                        if k.node.type_name == 'blendShape':
                            append_connected_attr(target_result, k.node.name, k.long_name)
                        else:
                            append_connected_attr(influence_result, k.node.name, k.long_name)
                else:
                    if out_node.type_name == 'blendShape':
                        append_connected_attr(target_result, out_node.name, out.long_name)
                    else:
                        append_connected_attr(influence_result, out_node.name, out.long_name)
        if using_threading:
            self.tmp_iter_count_dict[result_id] = self.tmp_iter_count_dict.get(result_id, 0) + 1
            SignalManager.single_step_cache_finished_signal.emit([self, result_id, total_length])

    def start_cache_job(self, using_threading=True, verbose=False):
        """
        The worker method which really do the cache job. A Qt signal will be emiited
        Returns:

        """
        influence_results, targets_results = self.__get_connected_nodes(
            using_threading=using_threading,
            verbose=verbose)
        if not using_threading:  # If not threading cache, pass the returned data directory to finish method
            self.finish_influence_cache(influence_results)
            self.finish_target_cache(targets_results)

    def get_anim_curves(self):
        """
        Get all the affected maya animCurve nodes by the pose,
        """
        out_plug = self.output_attribute_full_name
        if not cmds.objExists(out_plug):
            return []
        attr = Attribute(out_plug)
        dests = [i.node for i in attr.destinations]
        dests = [i.name for i in dests if i.type_name.startswith('animCurve')]
        return dests

    def get_influences_data(self):
        """
        Get the dictionary data for all pose's influences.
        """

        print(' >> pose.py get_influences_data:')
        print('')
        print(self.influences.values())      #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        def rreplace(s, old, new, occurrence):
            li = s.rsplit(old, occurrence)
            return new.join(li)

        data = dict()
        pose_anim_curves = self.get_anim_curves()
        if not pose_anim_curves:
            return data
        for influence in self.influences.values():
            influence_data = dict()
            for attr_name in influence.attributes:
                anim_curve_name = influence.get_anim_curve(attr_name)
                anim_curve = AnimCurve(anim_curve_name)
                influence_data[attr_name] = anim_curve.get_data(
                    keys_range=(0.01, sys.float_info.max))
            if influence_data:
                pose_name = influence.name
                
                print(' >> rig_tool/pose_editor/api/pose.py', '-'*30)
                print('influence.name:', pose_name)      #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                
                if pose_name.endswith('_FKPOSE'):
                    pose_name = rreplace(pose_name, '_FKPOSE', '_FKCTRL', 1)
                    print(' new pose_name:', pose_name)     #<<<<<<<<<<<<<<<<<<<<<<<<<<

                data[pose_name] = influence_data
        return data

    def get_driver_node(self):
        """
        Get the driver data for current pose
        Returns:
            Node: The driver node if exists

        """
        input_attr = Attribute(self.input_attribute_full_name)
        source = input_attr.source
        if source:
            return source.node

    @staticmethod
    def get_driver_range_from_anim_curve(anim_curve):
        """
        This is a convenient function to get driver attribute and it's range
        which is mapped to 0 and 10 of pose weight
        Args:
            anim_curve(AnimCurve): A anim curve nodezoo instance

        Returns:
            tuple: driver_attribute, default_value, extreme_value

        """
        driver_attribute, default_value, extreme_value = None, None, None
        source = anim_curve.input.source

        if source:
            driver_attribute = source.short_name
            key_data = []
            for idx in range(anim_curve.num_keys):
                key_data.append(
                    (anim_curve.get_value(idx),
                     anim_curve.get_input(idx))
                )

            key_data.sort(key=lambda x: (x[0], abs(x[1])))
            default_value = key_data[0][1]
            extreme_value = key_data[-1][1]
        return driver_attribute, default_value, extreme_value

    def get_driver_data(self):
        """
        Get the driver data for current pose
        Returns:

        """
        input_attr = Attribute(self.input_attribute_full_name)
        source = input_attr.source
        data = {}
        if source:
            # Only export additional node as anim curve or rbf solver
            # Otherwise, assume it is directly connected to a node in the rig
            soure_node = source.node
            if soure_node.type_name.startswith('animCurve') \
                    or soure_node.type_name == 'rbfSolver':
                data['creation_node'] = soure_node.export()
            else:
                data['connection'] = source.full_attr_name
        return data

    def get_data(self):
        """
        get the io data for the pose.
        """
        data = dict()
        influence_data = self.get_influences_data()
        if influence_data:
            data['influence'] = influence_data
        targets_data = self.get_targets_data()
        if targets_data:
            data['target'] = targets_data

        driver_data = self.get_driver_data()
        if driver_data:
            data['driver_data'] = driver_data

        corrective_data = self.get_corrective_data()
        if corrective_data:
            data['corrective'] = corrective_data
            data['current_corrective_index'] = self._current_corrective_index
        return data

    def set_neutral_pose(self, influences_name_list):
        """
        set the influences for neutral pose.
        """
        for influence_name in influences_name_list:
            self.add_influence(influence_name)

    def set_data(self, data, using_threading=True, skip_driver=False):
        """
        load pose from the serialized json data.

        Args:
            data(dict): Load dict data to this pose controller instance
            using_threading(bool): If refresh cache at idle thread


        """
        target_data = data.get('target')
        influence_data = data.get('influence')
        corrective_data = data.get('corrective')
        driver_data = data.get('driver_data')

        if corrective_data:
            self.set_corrective_data(corrective_data)
        if influence_data:
            self.set_influences_data(influence_data)
        if target_data:
            if self.controller:
                self.controller.create_blend_shape()
            self.set_targets_data(target_data)
        if not skip_driver and driver_data:
            self.set_driver_data(driver_data)
        self.refresh_cache(using_threading=using_threading)

    def remove_pose_attribute(self):
        """
        Remove the attributes associated with this pose on the pose controller node

        """
        input_attr = self.input_attribute_full_name
        output_attr = self.output_attribute_full_name

        if input_attr and cmds.objExists(input_attr):
            try:
                cmds.removeMultiInstance(input_attr, b=True)
            except RuntimeError:
                OpenMaya.MGlobal.dispalyError('failed to remove {}'.format(input_attr))
        if output_attr and cmds.objExists(output_attr):
            try:
                cmds.aliasAttr(output_attr, rm=True)
                cmds.removeMultiInstance(output_attr, b=True)
            except RuntimeError:
                OpenMaya.MGlobal.dispalyError('failed to remove {}'.format(output_attr))

    def set_influences_data(self, data):
        """
        set the influence data from the dictionary data.
        Args:
            data(dict): The Influence

        Returns:

        """

        for influence_name, influence in self.influences.items():
            influence_data = data.get(influence_name)
            if not influence_data:
                continue
            for attr_name in influence.attributes:
                channel_data = influence_data.get(attr_name)
                if channel_data is None:
                    continue
                curve_name = influence.get_anim_curve(attr_name)
                if curve_name and influence_data:
                    # load curves
                    curve = AnimCurve(curve_name)

                    curve.load(
                        channel_data,
                        keys_range=(0.01, sys.float_info.max))

    def set_targets_data(self, data):
        """
        set the target data from the dictionary data.
        """
        self.clear_targets()
        for weight_str, target_data in data.items():
            # The json only accept string as key. we need convert back to float.
            target_added = self.add_target(float(weight_str))
            if not target_data:
                OpenMaya.MGlobal.displayError("Failed to add target on pose {} at weight {}".format(
                    self.name,
                    weight_str))
            target_added.set_data(target_data)

    # corrective pose functions.########################################

    def set_corrective_data(self, data):
        drive_poses = list()
        corrective_keys = list()
        for element in data:
            corrective_weight = element[0]
            drive_poses_info = element[1]
            drive_poses_details = {}
            for drive_pose_name, drive_weight in drive_poses_info.items():
                drive_pose = self.controller.get_pose(drive_pose_name)
                if drive_pose in drive_poses:
                    drive_poses.append(drive_pose)
                drive_poses_details[drive_pose] = drive_weight
            corrective_keys.append([corrective_weight, drive_poses_details])
        self.set_up_corrective_nodes(drive_poses, corrective_keys=corrective_keys)

    def get_corrective_data(self):
        if not self.is_corrective:
            return None
        data = []
        for element in self.corrective_keys:
            corrective_weight = element[0]
            drive_poses_details = element[1]
            drive_poses_info = {}
            for drive_pose, drive_weight in drive_poses_details.items():
                drive_poses_info[drive_pose.name] = drive_weight
            data.append([corrective_weight, drive_poses_info])
        return data

    def get_weight_index(self):
        for idx, key in enumerate(self.corrective_keys):
            pose_keys = key[1]
            is_match = True
            for pose, weight in pose_keys.items():
                if pose.weight != weight:
                    is_match = False
                    break
            if is_match:
                return idx
        return -1

    def set_driver_data(self, data):
        if "creation_node" in data:
            creation_data = data['creation_node']
            for attr_data in creation_data['attributes']:
                if attr_data['name'] == "output":
                    for dst in attr_data['destinations']:
                        dst['dst'] = "{}.facePoseDriver[{}]".format(
                            self.controller.node_name,
                            self.index)

            Node.load_data(data['creation_node'])
        else:
            direction_connection = data.get('connection')
            if direction_connection and cmds.objExists(direction_connection):
                try:
                    cmds.connectAttr(
                        direction_connection,
                        self.input_attribute_full_name,
                        force=True)
                except RuntimeError as e:
                    print("Failed to connect attributes from {} to {}"
                          "".format(direction_connection,
                                    self.input_attribute_full_name))

    @property
    def drive_weights(self):
        return {drive_pose: drive_pose.weight for drive_pose in self.drive_poses}

    def sort_keys(self, corrective_keys):
        corrective_keys.sort(key=lambda element: element[0])
        return corrective_keys

    def add_corrective_key(self, weight=None):
        drive_poses = self.drive_poses
        weight_index = self.get_weight_index()
        corrective_keys = self.corrective_keys
        if weight is None:
            weight = self.weight

        if weight_index < 0:
            corrective_keys.append((weight, self.drive_weights))
        else:
            corrective_keys[weight_index] = (weight, self.drive_weights)
        corrective_keys = self.sort_keys(corrective_keys)
        # update current index.

        for idx, key in enumerate(corrective_keys):
            if key[0] == weight:
                self.current_corrective_index = idx
        self.set_up_corrective_nodes(
            drive_poses,
            corrective_keys=corrective_keys)

    def update_corrective_key(self):
        drive_poses = self.drive_poses
        weight_index = self.current_corrective_index
        corrective_keys = self.corrective_keys
        corrective_keys[weight_index] = (self.weight, self.drive_weights)
        corrective_keys = self.sort_keys(corrective_keys)
        # update current index.
        for idx, key in enumerate(corrective_keys):
            if key[0] == self.weight:
                self.current_corrective_index = idx
        self.set_up_corrective_nodes(
            drive_poses,
            corrective_keys=corrective_keys)

    def delete_corrective_key(self, weight_index=None):
        if weight_index is None:
            weight_index = self.current_corrective_index

        drive_poses = self.drive_poses
        corrective_keys = self.corrective_keys
        del corrective_keys[weight_index]
        self.set_up_corrective_nodes(
            drive_poses=drive_poses,
            corrective_keys=corrective_keys)
        if self._current_corrective_index == weight_index:
            self._current_corrective_index = len(self.corrective_keys) - 1
        elif self._current_corrective_index > weight_index:
            self._current_corrective_index -= 1

    def add_corrective_drive(self, drive_pose):
        drive_poses = self.drive_poses
        if drive_pose in drive_poses:
            return
        drive_poses.append(drive_pose)

        corrective_keys = self.corrective_keys
        for key in corrective_keys:
            if key[0] == self.weight:
                key[1][drive_pose] = drive_pose.weight
            else:
                key[1][drive_pose] = 0.0

        self.set_up_corrective_nodes(drive_poses, corrective_keys=corrective_keys)

    def delete_corrective_drive(self, drive_pose):
        drive_poses = self.drive_poses
        if drive_pose not in drive_poses:
            return
        drive_poses.remove(drive_pose)
        corrective_keys = self.corrective_keys
        for key in corrective_keys:
            del key[1][drive_pose]
        self.set_up_corrective_nodes(drive_poses, corrective_keys=corrective_keys)

    @property
    def current_corrective_key(self):
        return self.corrective_keys[self._current_corrective_index][0]

    @property
    def current_drive_pose(self):
        return self.corrective_keys[self._current_corrective_index][1]

    @property
    def current_corrective_index(self):
        return self._current_corrective_index

    @current_corrective_index.setter
    def current_corrective_index(self, index):
        if index >= len(self.corrective_keys):
            return
        key = self.corrective_keys[index]
        self._current_corrective_index = index
        self.weight = key[0]

    # Maya make RBF connection code.
    @property
    def rbf_node_name(self):
        return 'MHY_RBF_'+self.name

    def delete_corrective(self):
        if cmds.objExists(self.rbf_node_name):
            cmds.delete(self.rbf_node_name)

    @property
    def drive_poses(self):
        if not self.is_corrective:
            return
        if not Node.object_exist(self.rbf_node_name):
            return
        rbf_node = Node(self.rbf_node_name)
        num_drives = rbf_node.get_attr('NDimension')
        poses = []
        for i in range(num_drives):
            input_attr = rbf_node.attr('nInput')[i]
            source_attr = input_attr.source
            if not source_attr:
                OpenMaya.MGlobal.displayError("Invalid connections on rbf node for pose:".format(self.name))
                return
            index = source_attr.index
            controller_node = source_attr.node
            pose_name = controller_node.facePose[index].alias
            pose = self.controller.find_pose(pose_name)
            poses.append(pose)
        return poses

    @property
    def corrective_keys(self):
        if not self.is_corrective:
            return []
        if not Node.object_exist(self.rbf_node_name):
            return []
        rbf = Node(self.rbf_node_name)
        drive_poses = self.drive_poses
        num_keys = len(rbf.attr('poses').indices)
        num_drives = rbf.get_attr('NDimension')

        tmp_dict = {}
        for i in range(num_keys):
            for j in range(num_drives):
                key_val = rbf.poses[i].mValue[j].value
                if key_val not in tmp_dict:
                    tmp_dict[key_val] = {}
                pose_w = rbf.poses[i].nKey[j].value
                tmp_dict[key_val][drive_poses[j]] = pose_w

        flatten_list = [(weight, pose_map) for weight, pose_map in tmp_dict.items()]
        return flatten_list

    def set_up_corrective_nodes(self, drive_poses, weight=10, corrective_keys=None):
        """
        Set up the corrective pose network based on drive poses and extreme weight value
        Args:
            drive_poses(list): A list of drive poses [Pose * x]
            weight(float): Usually it's 10
            corrective_keys(list): If given, weight will be ignored

        Returns:
            list: Generated corrective keys data in a list of tuples.
        """
        if cmds.objExists(self.rbf_node_name):
            cmds.delete(self.rbf_node_name)
        if not drive_poses:
            # skip making rbf, when there is not drive pose.
            return
        # set attributes.
        rbf_node = Node.create('rbfSolver', name=self.rbf_node_name)
        # if rbf_node != self.rbf_node_name:
        # warning
        rbf_node.NDimension.value = len(drive_poses)
        rbf_node.MDimension.value = 1
        rbf_node.scale.value = 0.5
        rbf_node.normalize.value = 0
        rbf_node.rbfMode.value = 1  # gaussian=1

        if corrective_keys is None:
            corrective_keys = [
                (0.0, {drive_pose: 0.0 for drive_pose in drive_poses}),
                (weight, {drive_pose: drive_pose.weight for drive_pose in drive_poses})
            ]

        for idx, corrective_key in enumerate(corrective_keys):
            corrective_weight = corrective_key[0]
            for drive_pose, drive_pose_weight in corrective_key[1].items():
                drive_idx = drive_poses.index(drive_pose)
                rbf_node.poses[idx].mValue[drive_idx].value = corrective_weight
                rbf_node.poses[idx].nKey[drive_idx].value = drive_pose_weight

        # make connections.
        input_attr = Attribute(self.input_attribute_full_name)
        rbf_node.mOutput[0].connect(input_attr)

        for idx, pose in enumerate(drive_poses):
            override_attr = Attribute(pose.override_attribute_full_name)
            override_attr.connect(rbf_node.nInput[idx])

        return corrective_keys

    # ------------------------------------------------------------------------
    # Mirror methods
    # ------------------------------------------------------------------------

    @staticmethod
    def _get_mirror_attribute_name(attribute_name):
        if attribute_name[-1:] == "L":
            return attribute_name[:-1]+"R"
        if attribute_name[-1:] == "R":
            return attribute_name[:-1]+"L"
        return attribute_name

    def mirror(self, source=Symmetry.LEFT, using_threading=True):
        """
        self-mirror the driven key animation curves from left to right.
        """
        if not self.weight_keys:
            return
        self.mirror_influences_from(source=source, other=self)
        self.mirror_targets(source=source)
        self.refresh_cache(using_threading=using_threading)

    def mirror_from(self, pose, using_threading=True):
        """
        mirror the pose influence and targets
        """
        if not pose.weight_keys:
            return
        self.reset(remove_influence=True)
        self.mirror_influences_from(other=pose)
        self.mirror_targets_from(other=pose)
        self.refresh_cache(using_threading=using_threading)

    def mirror_influences_from(self, source=None, other=None):
        """
        Mirror influences data with it self based on a direction or from another pose
        by flipping the data
        Args:
            source(int): An enum integer representing a mirror side
            other(Pose):

        Returns:

        """
        if not other and not self.influences:
            return
        num_inf = len(other.influences)
        for original_influence in other.influences.values():
            if source is not None and original_influence.symmetry != source:
                continue
            symmetry_name = original_influence.get_mirror_name()
            if not cmds.objExists(symmetry_name):
                OpenMaya.MGlobal.displayWarning('{} does not exist. Skip mirroring {}'.format(
                    symmetry_name, original_influence))
                continue
            symmetry_influence = self.add_influence(symmetry_name)
            if symmetry_influence is None:
                return
            symmetry_influence.add_neutral_key(
                self.output_attribute_full_name)

            if original_influence.name.endswith('TRACER'):
                self.mirror_tracer(
                    original_influence,
                    symmetry_influence)

            else:
                self.mirror_fk_control(
                    original_influence,
                    symmetry_influence)
        OpenMaya.MGlobal.displayInfo("Mirrored {} Influences on pose `{}` from `{}`".format(
            num_inf,
            self.name,
            other.name))

    def mirror_targets(self, source=Symmetry.LEFT):
        if not self.targets:
            return
        num_tgt = len(self.targets)
        for target in self.targets.values():
            target.mirror(source=source)
        OpenMaya.MGlobal.displayInfo("Mirrored {} Targets on pose `{}`".format(num_tgt, self.name))

    def mirror_targets_from(self, other=None):
        """
        Mirror all the targets on this pos from another pose
        Args:
            other:

        Returns:

        """
        self.clear_targets()
        if not other.targets:  # If other pose has no targets, skip
            return
        num_tgt = len(other.targets)
        for target in other.targets.values():
            # add target mapped weight 0-10 to 0-1, so input weight need to be scaled to 0-10 range
            target_weight = target.weight*10.0
            added_target = self.add_target(target_weight)
            flipped_points, flipped_components = target.mirror(flip=True, dry_run=True)
            added_target.target_components = flipped_components
            added_target.mesh_delta = flipped_points
        OpenMaya.MGlobal.displayInfo("Mirrored {} Targets on pose `{}`".format(num_tgt, self.name))

    @staticmethod
    def mirror_tracer(original_influence, symmetry_influence):
        patch = get_patch_from_tracer(original_influence.name)
        sym_patch = get_patch_from_tracer(symmetry_influence.name)
        if not patch or not sym_patch:
            return False

        original_u_curve = original_influence.get_anim_curve('parameterU')

        symmetry_u_curve = symmetry_influence.get_anim_curve('parameterU')

        original_v_curve = original_influence.get_anim_curve('parameterV')

        symmetry_v_curve = symmetry_influence.get_anim_curve('parameterV')
        if original_u_curve and original_v_curve and symmetry_u_curve and symmetry_v_curve:
            orig_u_delta = Node(original_influence.name).originU.value
            orig_v_delta = Node(original_influence.name).originV.value

            sym_u_delta = Node(symmetry_influence.name).originU.value
            sym_v_delta = Node(symmetry_influence.name).originV.value

            orig_u_curve = Node(original_u_curve)
            orig_v_curve = Node(original_v_curve)

            orig_u_data = orig_u_curve.get_keys_data()
            orig_v_data = orig_v_curve.get_keys_data()

            sym_u_curve = Node(symmetry_u_curve)
            sym_v_curve = Node(symmetry_v_curve)

            target_u_keys_data = {}
            target_v_keys_data = {}
            for key, data in orig_u_data.items():
                v_data = orig_v_data.get(key)
                if not v_data:
                    continue
                u_value = data['value'] + orig_u_delta

                v_value = v_data['value'] + orig_v_delta
                if not (0 < u_value < 1 and 0 < v_value < 1):
                    OpenMaya.MGlobal.displayError("Mirror failed on {}. Please check the orginU/V "
                                                  "attributes are set correctly ".format(original_influence))
                    return
                if key != 0:
                    patch = Node(patch.name)
                    pos = patch.point_at_param(u_value,  v_value)
                    pos = [-1 * pos[0], pos[1], pos[2]]
                    param_u, param_v = sym_patch.closest_param(pos)

                    data['value'] = param_u - sym_u_delta
                    v_data['value'] = param_v - sym_v_delta
                else:
                    data['value'] = 0.0
                    v_data['value'] = 0.0

                target_u_keys_data[key] = data
                target_v_keys_data[key] = v_data
            sym_u_curve.set_keys_data(target_u_keys_data, merge=False, set_tangent_val=False)
            sym_v_curve.set_keys_data(target_v_keys_data, merge=False, set_tangent_val=False)
        return True

    def mirror_fk_control(self,
                          original_influence,
                          symmetry_influence):
        """
        Mirror the fk control
        Args:
            original_influence:
            symmetry_influence:

        Returns:

        """
        flip_attrs = ['tz', 'rx', 'ry']
        flip_attrs = ['tx', 'ry', 'rz']
        if symmetry_influence.name == original_influence.name:
            flip_attrs = ['tx', 'ry', 'rz']

        for attr_name in original_influence.attributes:
            original_curve = original_influence.get_anim_curve(attr_name)

            mirror_attr_name = self._get_mirror_attribute_name(attr_name)

            symmetry_curve = symmetry_influence.get_anim_curve(mirror_attr_name)

            if original_curve and symmetry_curve:
                # copy curves
                if attr_name in flip_attrs:
                    utils.copy_curve(src=original_curve, dst=symmetry_curve,
                                     value_func=lambda value: -value)
                else:
                    utils.copy_curve(src=original_curve,
                                     dst=symmetry_curve)


def get_patch_from_tracer(tracer):
    # continue
    tracer = Node(tracer)
    follicle = tracer.search_node('.*_FLC',
                                  False,
                                  type_filter=OpenMaya.MFn.kFollicle)
    if not follicle:
        return
    patch = follicle.search_node('.*_SKULLShape',
                                 type_filter=OpenMaya.MFn.kNurbsSurface)
    return patch



