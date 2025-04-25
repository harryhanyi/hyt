"""
This module contains the core `Retargeter` class.

Basic usage:

.. code-block:: python

    from mhy.maya.anim.retarget.retargeter import Retargeter

    retargeter = Retargeter(
        target_rig_file_path,
        source_rig_file_path,
        config_file=config_file_path)

    for source_anim_path in source_anims:
        retargeter.run(source_anim_path)

**Global Configuration File**

Each retargeting is performed based upon a user-provided configuration
file (JSON) containing mapping relationship between controls in the
target rig and transforms in the source rig.

We support 2 types of mapping relationship:

+ One-to-one mapping:

.. code-block:: json

    {
        "target_to_source": {
            target_ctrl_1: source_xform_1,
            target_ctrl_2: source_xform_2,
            target_ctrl_3: source_xform_2
        }
    }

Note that we can map multiple target controls on to a single source
transform. Keep in mind that **THE ORDER MATTERS**! make sure to layout
the mapping pairs by hierarchical order as retargeting is performed using
the same order presented in the config file.

+ One-to-multiple mapping:

.. code-block:: json

    {
        "target_to_source": {
            target_ctrl: {
                "position": [[source_xform_1, 0.7], [source_xform_2, 0.3]],
                "aim": [source_xform_1, "x"]
            }
        }
    }

In the above example, a single control's position is mapped to 2 source
transforms, and its orientation is specified as aimming to source_xform_1
using "x" as aim axis. This method is useful in situation where a target
control has no direct counterpart in the source rig.

**Configurate Dynamic Attributes**

+ Setting dynamic attributes directly

.. code-block:: json

    {
        "dynamic_attributes": {
            "head_M_FKCTRL.stretch": 1,
            "arm_wrist_L_IKCTRL.IKFKBlend": 0,
            "leg_knee_L_IKCTRL.space": {
                "default": 1,
                "overrides": [[2, [1, 1]]]
            }
        }
    }

This is handy for specifying things like IKFK modes, space switch
values, etc.
We can also specify dynamic attribute values per time range,
See "leg_knee_L_IKCTRL.space" as an example.

+ Associate dynamic attributes

.. code-block:: json

    {
        "dynamic_attributes": {
            "arm_wrist_L_IKCTRL.IKFKBlend": ["arm_l.ikfk", 10],
            "leg_knee_L_IKCTRL.space": ["arm_l.ikfk", {"0": 1, "1", 2, "2", 0}]
        }
    }

This example shows how to associate dynamic attributes between the source rig
and target rig. The format is a list of `[source_attr, remapper]`, the remapper
can be a single multipler or a dict of {old_value: new_value} pairs.

**Global Options**

.. code-block:: json

    {
        "options": {
            "keyframe_only": true
        }
    }

**[Optional] Animation Config File**

An animation config file can be created a specifc animation to
override the dynamic attrs and options in the global configuration:

.. code-block:: json

    {
        "time_ranges": [
            [0, 10], [30, 40]
        ],
        "options": {
            "keyframe_only": false
        }
        "dynamic_attributes": {
            "arm_wrist_L_IKCTRL.IKFKBlend": 1,
        }
    }

As you can see, we can also specify time ranges for the given animation:
Only animation within these ranges wil be retargeted. If not provided.
The system will automatically find the first and last key and retarget
all frames inbetween.
"""

import os
import time
import copy

from maya import cmds

from mhy.python.core.signal import Signal

import mhy.maya.scene as sutil
import mhy.maya.ma_parser as mp
import mhy.maya.maya_math as mmath
from mhy.maya.nodezoo.node import Node

import mhy.maya.anim.retarget.constants as const
import mhy.maya.anim.retarget.utils as util
import mhy.maya.anim.retarget.bind_pose as bp


DEFAULT_CONFIG_NAME = 'retarget_config.json'


class Retargeter(object):
    """
    Animation retargeter class.
    """

    def __init__(
            self, tgt_rig, src_rig=None, config_file=None,
            namespace=None, frame_rate=None):
        """Initializes an animation retargeter object.

        Args:
            tgt_rig (str): A rig file to recieve retargeted animations.
            src_rig (str): The rig file used in the source animations.
                If None, sample the source rig from each source animation.
            config_file (str): Path to a retargeting configuration file.
                If None, assume the config file shares the same name as the
                rig file. This file defines how to perform each retargeting.
            namespace (str): The namespace to use in the retargeted animation.
                If None, use the rig file name.
            frame_rate (float): A frame rate to use for the output animations.
                If None, use the source animation's frame rate.
        """
        if frame_rate and not sutil.is_frame_rates_valid(frame_rate):
            raise ValueError('Invalid frame rate: {}'.format(frame_rate))
        self.__frame_rate = frame_rate
        if src_rig:
            src_rig = src_rig.replace('\\', '/')
        tgt_rig = tgt_rig.replace('\\', '/')

        # validate rig file
        util.validate_file_path(tgt_rig, const.EXT_MAYA, 'rig file')
        self.__src_rig = src_rig
        self.__tgt_rig = tgt_rig

        # validate rig config file path
        if not config_file:
            d, _ = os.path.split(tgt_rig)
            config_file = os.path.join(d, DEFAULT_CONFIG_NAME).replace('\\', '/')
        util.validate_file_path(
            config_file, const.EXT_CONFIG, 'retarget config')
        self.__config_file = config_file

        # cache namespace
        if not namespace:
            self.__namespace = os.path.splitext(os.path.split(tgt_rig)[-1])[0]
        else:
            self.__namespace = str(namespace)

        # cache rig config data
        self.__config = util.read_config_file(self.config_file)

        # cache/update bind pose data
        bind_pose = bp.BindPose(self.__config_file, src_rig, tgt_rig)
        if self.has_hik:
            self.__src_hik = None
            if src_rig:
                self.__src_hik = bind_pose.read_bind_pose('source_hik')
            self.__tgt_hik = bind_pose.read_bind_pose('target_hik')
            self.__tgt_bind_pose = bind_pose.read_bind_pose('target')
        else:
            self.__src_bind_pose = None
            if src_rig:
                self.__src_bind_pose = bind_pose.read_bind_pose('source')
            self.__tgt_bind_pose = bind_pose.read_bind_pose('target')

        self.__cur_frame = None

        # signals
        self.retarget_started = Signal()
        self.frame_count_changed = Signal(int)
        self.current_frame_changed = Signal(int)
        self.status_changed = Signal(str, int)

    # --- rig properties/methods

    # @property
    # def source_rig_file(self):
    #     """The source rig file path."""
    #     return self.__src_rig

    @property
    def target_rig_file(self):
        """The target rig file path."""
        return self.__tgt_rig

    @property
    def config_file(self):
        """The retarget config file path."""
        return self.__config_file

    @property
    def namespace(self):
        """The rig namespace in the retargeted animation file."""
        return self.__namespace

    @property
    def has_hik(self):
        """If humanIK is used in this transfer."""
        return const.KEY_SRC_HIK in self.__config

    # --- per-animation data caching

    def __create_interm_hik_rig(self):
        """With bind pose data, creates humanIK skeleton, one for
        source and one for target, and link them together.
        """
        # cache source hik bind pose data
        if not self.__src_rig:
            bind_pose = bp.BindPose(
                self.__config_file, self.__src_rig, self.__tgt_rig)
            self.__src_hik = bind_pose.get_bind_pose_data(
                source_type='source_hik')
            util.log_info('Extracted bind pose data from source anim...')

        # create hik skeletons
        roots = []
        hik_data_src = {}
        hik_data_tgt = {}
        hik_src_joints = {}
        hik_tgt_joints = {}
        for data, suffix, it_cache, hik_data in zip(
                (self.__src_hik, self.__tgt_hik),
                (const.SUFFIX_SRC_HIK, const.SUFFIX_TGT_HIK),
                (hik_src_joints, hik_tgt_joints),
                (hik_data_src, hik_data_tgt)):

            for node, mat in data['matrix'].items():
                it_node = cmds.createNode('joint', name=node + '_' + suffix)
                it_cache[node] = it_node
                cmds.xform(it_node, worldSpace=True, matrix=mat)
                parent = data['parent'].get(node)
                if parent:
                    parent = it_cache.get(parent)
                if not parent:
                    if not cmds.objExists(const.ROOT_IT):
                        cmds.createNode('transform', name=const.ROOT_IT)
                    parent = const.ROOT_IT
                    roots.append(it_node)
                cmds.makeIdentity(
                    it_node, translate=False, rotate=False, scale=True, apply=True)
                cmds.parent(it_node, parent)
                element_name = data['hik_element'].get(node)
                hik_data[element_name] = it_node
                if suffix == const.SUFFIX_TGT_HIK:
                    self.__hik_src_remap[node] = it_node

        for root in roots:
            cmds.makeIdentity(
                root, translate=False, rotate=True, scale=True, apply=True)

        # build hik skeletons
        hik_src = Node.create('HIKCharacterNode', name='hik_src')
        hik_src.load_joint_data(hik_data_src)
        hik_src.flatten_arm_joints()
        hik_src.skeleton_locked = True
        hik_tgt = Node.create('HIKCharacterNode', name='hik_tgt')
        hik_tgt.load_joint_data(hik_data_tgt)
        hik_tgt.flatten_arm_joints()
        hik_src.skeleton_locked = True

        # attach source hik to source joints
        for node, it_node in hik_src_joints.items():
            nodes = cmds.ls('{}:{}'.format(const.NAMESPACE_SRC, node))
            nodes += cmds.ls('{}:*:{}'.format(const.NAMESPACE_SRC, node))
            if not nodes:
                util.log_error('Source node not found: {}'.format(node))
            else:
                cmds.parentConstraint(nodes[0], it_node, maintainOffset=False)

        # connect hik skeletons
        hik_tgt.set_source(hik_src)

        self.__hik_nodes = [hik_src, hik_tgt]

    def __create_interm_rig(self, relative=False):
        """With bind pose data, creates a 2-layered intermidiate hierarchy
        nesting each target node under the associated sourcec node.

        Args:
            relative (bool): If True, applies relative offsets.
        """
        for target, source in self.__config[const.KEY_TGT_NODE].items():
            src_names = util.get_source_names(source)
            for src in src_names:
                it_src = self.__it_src_dict.get(src)
                if not it_src:
                    if not cmds.objExists(const.ROOT_IT):
                        cmds.createNode('transform', name=const.ROOT_IT)
                    it_src = cmds.group(
                        empty=True, parent=const.ROOT_IT,
                        name=src + '_' + const.SUFFIX_IT_SRC)
                    if self.has_hik:
                        mat = self.__tgt_hik['matrix'].get(src)
                    else:
                        mat = self.__src_bind_pose['matrix'].get(src)
                    cmds.xform(it_src, worldSpace=True, matrix=mat)
                    self.__it_src_dict[src] = it_src

            if target not in self.__it_tgt_dict:
                it_tgt = cmds.group(
                    empty=True, name=target + '_' + const.SUFFIX_IT_TGT)
                mat = self.__tgt_bind_pose['matrix'].get(target)
                cmds.xform(it_tgt, worldSpace=True, matrix=mat)
                self.__it_tgt_dict[target] = it_tgt

                if not isinstance(source, dict):
                    src = self.__it_src_dict[src_names[0]]
                    if relative:
                        cmds.parent(it_tgt, const.ROOT_IT)
                        cmds.pointConstraint(src, it_tgt, maintainOffset=True)
                        cmds.orientConstraint(src, it_tgt, maintainOffset=True)
                    else:
                        cmds.parent(it_tgt, src)
                else:
                    if not cmds.objExists(const.ROOT_IT):
                        cmds.createNode('transform', name=const.ROOT_IT)
                    cmds.parent(it_tgt, const.ROOT_IT)

                    for key, data in source.items():
                        if key == 'position':
                            sources = [self.__it_src_dict[x[0]] for x in data]
                            weights = [x[1] for x in data]
                            # org_pos = cmds.xform(
                            #     it_tgt, query=True,
                            #     worldSpace=True, translation=True)
                            cns = cmds.pointConstraint(
                                sources, it_tgt, maintainOffset=False)[0]
                            attrs = cmds.pointConstraint(
                                cns, query=True, weightAliasList=True)
                            for attr, weight in zip(attrs, weights):
                                cmds.setAttr('{}.{}'.format(cns, attr), weight)
                            # pos = cmds.xform(
                            #     it_tgt, query=True,
                            #     worldSpace=True, translation=True)
                            # offset = [org_pos[i] - pos[i] for i in range(3)]
                            # cmds.setAttr('{}.offset'.format(cns), *offset)

                        elif key == 'aim':
                            aim_vector = mmath.world_axis_to_vector(data[1])
                            up_axis = 'xyz'.replace(data[1], '')[0]
                            up_vector = mmath.world_axis_to_vector(up_axis)
                            driver = self.__it_src_dict[data[0]]
                            cmds.aimConstraint(
                                driver, it_tgt,
                                aimVector=aim_vector.as_tuple(),
                                upVector=up_vector.as_tuple(),
                                worldUpType='objectrotation',
                                worldUpObject=driver,
                                worldUpVector=up_vector.as_tuple(),
                                maintainOffset=True)

    def __cache_time_ranges(self, anim_file, sample_po):
        """Caches the time ranges for the current animation."""
        self.__time_ranges = self.__anim_config.get(const.KEY_RANGE, [])
        if not self.__time_ranges:
            if sample_po and not anim_file.endswith('.ma'):
                ext = os.path.splitext(anim_file)[-1]
                util.log_warn(
                    ('Can\'t sample playback options for {} files. '
                     'Sampling keyframes instead.').format(ext))
                sample_po = False

            if sample_po:
                po = mp.MAParser(anim_file).get_playback_options()
                self.__time_ranges = [[po['minTime'], po['maxTime']]]
            else:
                source_nodes = self.__get_time_sampling_nodes()
                self.__time_ranges = util.get_animated_time_ranges(source_nodes)

        for i in range(len(self.__time_ranges)):
            for j in range(len(self.__time_ranges[i])):
                val = self.__time_ranges[i][j]
                self.__time_ranges[i][j] = int(val)

        if len(self.__time_ranges) == 1:
            start, end = self.__time_ranges[0]
            cmds.playbackOptions(
                minTime=start, maxTime=end,
                animationStartTime=start, animationEndTime=end)

        frame_count = 0
        for time_range in self.__time_ranges:
            frame_count += time_range[1] - time_range[0]
        self.frame_count_changed.emit(frame_count)

    # --- execution helper methods

    def __get_source_node(self, key):
        """Returns a source node from a name key."""
        node = self.__source_nodes.get(key)
        if node is None:
            if self.__hik_src_remap:
                node = self.__hik_src_remap[key]
            else:
                node = cmds.ls('{}:{}'.format(const.NAMESPACE_SRC, key))
                node += cmds.ls('{}:*:{}'.format(const.NAMESPACE_SRC, key))
                if not node:
                    util.log_error('Source node not found: {}'.format(key))
                else:
                    node = node[0]
            self.__source_nodes[key] = node
        return node

    def __get_time_sampling_nodes(self):
        """Returns a source node from a name key."""
        if self.has_hik:
            nodes = []
            for key in self.__config[const.KEY_SRC_HIK].values():
                node = cmds.ls('{}:{}'.format(const.NAMESPACE_SRC, key))
                node += cmds.ls('{}:*:{}'.format(const.NAMESPACE_SRC, key))
                if not node:
                    util.log_error('Source node not found: {}'.format(key))
                else:
                    nodes.append(node[0])
            return nodes
        else:
            return [self.__get_source_node(x) for x in
                    util.iter_source_node_names(self.__config)]

    def __get_source_attr(self, attr_key):
        """Returns a source node attribute from an attr name key."""
        source, attr_name = attr_key.split('.', 1)
        source_node = self.__get_source_node(source)
        if source_node:
            return '{}.{}'.format(source_node, attr_name)

    def __get_target_node(self, key):
        """Returns a target node from a name key."""
        node = self.__target_nodes.get(key)
        if node is None:
            node = cmds.ls('{}:{}'.format(self.__namespace, key))
            if not node:
                cmds.warning('target node not found: {}'.format(key))
                self.__target_nodes[key] = ''
            else:
                node = node[0]
                self.__target_nodes[key] = node
        return node

    def __resolve_dyn_attr_value(
            self, target_attr, val, dyn_attr_data, time_range):
        """Resolves a value for a dynamic attr, and register it into
        a data dict."""
        start_frame, end_frame = time_range

        # list - [source_attr, multiplier]
        if isinstance(val, list):
            source_attr, remapper = val
            source_attr = self.__get_source_attr(source_attr)
            if source_attr:
                # non-animated source attr: get its value and register
                # to the start and end frame of the time range.
                if not util.attr_animated(source_attr):
                    v = cmds.getAttr(source_attr)
                    v = util.remap_value(v, remapper)
                    dyn_attr_data.setdefault(start_frame, {})
                    dyn_attr_data.setdefault(end_frame, {})
                    dyn_attr_data[start_frame][target_attr] = v
                    dyn_attr_data[end_frame][target_attr] = v

                # animated source attr: register the [attr, remapper] pair
                # to the entire time range
                else:
                    for i in range(start_frame, end_frame + 1, 1):
                        dyn_attr_data.setdefault(i, {})
                        dyn_attr_data[i][target_attr] = (source_attr, remapper)

        # a direct value: register it to the start and end
        # frame of the time range.
        else:
            dyn_attr_data.setdefault(start_frame, {})
            dyn_attr_data.setdefault(end_frame, {})
            dyn_attr_data[start_frame][target_attr] = val
            dyn_attr_data[end_frame][target_attr] = val

    def __populate_dyn_attr_data(self, dyn_attr_data, user_data, time_range):
        # caches dynamic attribute values
        for attr, data in user_data.items():
            if '.' not in attr:
                cmds.warning('invalid attribute: {}'.format(attr))
                continue

            target, attr = attr.split('.', 1)
            target_node = self.__get_target_node(target)
            if not target_node:
                continue
            target_attr = '{}.{}'.format(target_node, attr)

            if isinstance(data, dict):
                self.__resolve_dyn_attr_value(
                    target_attr, data['default'], dyn_attr_data, time_range)
                for val, tr in data['overrides']:
                    self.__populate_dyn_attr_data(
                        dyn_attr_data, {target_attr: val}, tr)
                    self.__resolve_dyn_attr_value(
                        target_attr, data['default'],
                        dyn_attr_data, [tr[1] + 1, tr[1] + 1])
            else:
                self.__resolve_dyn_attr_value(
                    target_attr, data, dyn_attr_data, time_range)

    def __set_frame(self, frame):
        """Set the current frame, if necesary."""
        if self.__cur_frame != frame:
            cmds.currentTime(frame, edit=True, update=True)
            self.__cur_frame = frame

    # --- exection methods

    def __start(
            self, anim_file, new_file=True,
            output_file=None, anim_config_file=None):
        """Runs at the beginning of each retargeting operation to
        cache necessary data.
        """
        self.retarget_started.emit()

        # reset internal data
        self.__cur_frame = None
        self.__anim_config = {}
        self.__it_src_dict = {}
        self.__it_tgt_dict = {}
        self.__anim_ref = None
        self.__output_file = None
        self.__time_ranges = []
        self.__source_nodes = {}
        self.__target_nodes = {}
        self.__hik_nodes = []
        self.__hik_src_remap = {}

        # validate pathes
        util.validate_file_path(
            anim_file, const.EXT_MAYA, 'source animation')

        # open the specified target animation file
        if output_file:
            util.validate_file_path(
                output_file, const.EXT_MAYA, 'target animation',
                check_exists=False)
            self.__output_file = output_file

        if output_file and not new_file and os.path.isfile(output_file):
            self.__output_file = output_file
            sutil.safe_open(output_file, open=True, force=True)
            ref_node = sutil.get_reference_nodes(self.target_rig_file)
            if len(ref_node) != 1:
                raise RuntimeError(
                    ('0 or more than 1 target rig reference found in the '
                     'target animation file... char: {} | anim {}').format(
                         self.target_rig_file, output_file))
            ref_node = ref_node[0]

            # update the reference node
            if self.__namespace:
                ref_node.namespace = self.__namespace
            # make sure rig is loaded
            ref_node.load()

        # or, make a new target animation file
        else:
            cmds.file(force=True, newFile=True)
            sutil.safe_open(
                self.target_rig_file, reference=True, namespace=self.__namespace)
            if output_file:
                self.__output_file = output_file
            else:
                head, fn = os.path.split(anim_file)
                fn = os.path.splitext(fn)[0] + '_retargeted.ma'
                self.__output_file = os.path.join(head, fn).replace('\\', '/')

            # use the source anim's frame rate as the working frame rate
            if anim_file.endswith('.ma'):
                frame_rate = mp.MAParser(anim_file).get_units()['time']
                sutil.set_frame_rate(frame_rate)

        # for fbx files, import it into the source namespace
        if util.is_fbx(anim_file):
            self.__anim_ref = None
            cur_ns = cmds.namespaceInfo(currentNamespace=True)
            src_ns = ':' + const.NAMESPACE_SRC
            if not cmds.namespace(exists=src_ns):
                cmds.namespace(add=src_ns)
            cmds.namespace(set=src_ns)
            sutil.safe_open(
                anim_file, type='FBX', i=True,
                ignoreVersion=True, mergeNamespacesOnClash=True,
                renameAll=True, preserveReferences=True,
                importFrameRate=True,
                namespace=':' + const.NAMESPACE_SRC)
            cmds.namespace(set=cur_ns)
        # for maya files, directly reference the source animation file
        else:
            self.__anim_ref = Node.create(
                'reference', anim_file, namespace=const.NAMESPACE_SRC)

        # read animation config file, if any
        if not anim_config_file:
            anim_config_file = os.path.splitext(anim_file)[0]
            anim_config_file += '.' + const.EXT_CONFIG
        if anim_config_file and os.path.isfile(anim_config_file):
            self.__anim_config = util.read_config_file(anim_config_file)

    def __end(self):
        """Runs at the end of each retargeting operation to clean up
        the scene and save it."""

        # remove intermidiate nodes
        for hik in self.__hik_nodes:
            hik.delete()
        if cmds.objExists(const.ROOT_IT):
            cmds.delete(const.ROOT_IT)

        # remove source animation reference
        if self.__anim_ref:
            self.__anim_ref.delete()
        else:
            src_ns = ':' + const.NAMESPACE_SRC
            nodes = cmds.namespaceInfo(
                src_ns, listOnlyDependencyNodes=True, recurse=True)
            if nodes:
                cmds.delete(nodes)
            if cmds.namespace(exists=src_ns):
                for ns in cmds.namespaceInfo(
                        src_ns, listOnlyNamespaces=True, recurse=True) or []:
                    cmds.namespace(removeNamespace=ns)
                cmds.namespace(removeNamespace=src_ns)

        # set final frame rate
        if self.__frame_rate:
            sutil.set_frame_rate(self.__frame_rate)

        # save target animation
        cmds.file(rename=self.__output_file)
        cmds.file(save=True, defaultExtensions=False, type='mayaAscii')

    def __run(
            self, anim_file, new_file=True,
            output_file=None, anim_config_file=None):
        """Main entry method to execute a retargeting request.

        Args:
            anim_file (str): A source animation file to retarget to this rig.
            new_file (bool): If True, always make a new output file.
                Otherwise reuse existing output file and retarget on top of it.
            output_file (str): A file path to save the retargeted animation.
                If None, save the result next to the source file.
            anim_config_file (str): A config file providing additional info
                about the source animation.

        Returns:
            str: The output file path.
        """
        util.log_info(
            'Preparing output file... (Input anim: {})'.format(anim_file))
        last_time = time.time()

        # run start to prepare the output file and necessary data
        self.__start(anim_file, new_file, output_file, anim_config_file)

        # merging global data and anim-specific data
        global_dyn_data = self.__config.get(const.KEY_DYN_ATTR, {})
        dyn_data = copy.copy(global_dyn_data)
        dyn_data.update(self.__anim_config.get(const.KEY_DYN_ATTR, {}))

        global_options = self.__config.get(const.KEY_OPTION, {})
        options = copy.copy(global_options)
        options.update(self.__anim_config.get(const.KEY_OPTION, {}))
        kf_only = options.get(const.KEY_KEY_ONLY, False)
        sample_op = options.get(const.KEY_SAMPLE_PO, False)

        # clear existing interm nodes
        if cmds.objExists(const.ROOT_IT):
            cmds.delete(const.ROOT_IT)

        # cache time ranges
        # this must be done before interm hik rig is created
        self.__cache_time_ranges(anim_file, sample_op)

        # create interm nodes
        if self.has_hik:
            self.__create_interm_hik_rig()
        self.__create_interm_rig()

        util.log_info(
            'Output file ready! (Time elapsed: {:0.2f}s)'.format(
                time.time() - last_time))
        util.log_info(
            'Retargeting started... (Anim: {} | Time ranges: {})'.format(
                anim_file, self.__time_ranges))
        last_time = time.time()

        # retargetting
        for time_range in self.__time_ranges:
            # caches dynamic attribute values
            dyn_attr_data = {}
            self.__populate_dyn_attr_data(dyn_attr_data, dyn_data, time_range)

            for frame in range(time_range[0], time_range[1] + 1, 1):
                self.current_frame_changed.emit(frame)

                # apply dynamic_attributes
                for attr, val in dyn_attr_data.get(frame, {}).items():
                    if isinstance(val, (list, tuple)):
                        source_attr, remapper = val
                        if util.attr_animated(source_attr, frame=frame):
                            self.__set_frame(frame)
                            val = cmds.getAttr(source_attr)
                            val = util.remap_value(val, remapper)
                        else:
                            continue

                    self.__set_frame(frame)
                    cmds.setAttr(attr, val)
                    util.key_attr(attr, in_tangent='flat', out_tangent='flat')

                for target, source in self.__config[const.KEY_TGT_NODE].items():
                    # get iterm source names and nodes
                    src_names = util.get_source_names(source)
                    it_src_nodes = [self.__it_src_dict[x] for x in src_names]
                    source_nodes = {}
                    has_animated_source = False

                    # update source nodes
                    for name, it_src in zip(src_names, it_src_nodes):
                        source_node = self.__get_source_node(name)
                        source_nodes[it_src] = source_node
                        if kf_only and not has_animated_source and \
                           util.xform_animated(source_node, frame=frame):
                            has_animated_source = True
                    if kf_only and not has_animated_source:
                        continue

                    # get the target node and its interm node
                    target_node = self.__get_target_node(target)
                    if not target_node:
                        continue
                    it_tgt = self.__it_tgt_dict[target]

                    self.__set_frame(frame)

                    for it_src, source_node in source_nodes.items():
                        mat = cmds.xform(
                            source_node, query=True,
                            worldSpace=True, matrix=True)
                        cmds.xform(it_src, worldSpace=True, matrix=mat)

                    # update and key target node
                    mat = cmds.xform(
                        it_tgt, query=True, worldSpace=True, matrix=True)
                    cmds.xform(target_node, worldSpace=True, matrix=mat)
                    util.key_xform(
                        target_node,
                        in_tangent='clamped',
                        out_tangent='clamped')

        util.log_info(
            'Retargeting complete! (Time elapsed: {:0.2f}s)'.format(
                time.time() - last_time))

        self.__end()

        util.log_info('Cleaning up...')
        util.log_info(
            'Output file saved to {}. (Time elapsed: {:0.2f}s)'.format(
                self.__output_file, time.time() - last_time))

        return self.__output_file

    def run(
            self, anim_file, new_file=True,
            output_file=None, anim_config_file=None):
        """Main entry method to execute a retargeting request.

        Args:
            anim_file (str): A source animation file to retarget to this rig.
            new_file (bool): If True, always make a new output file.
                Otherwise reuse existing output file and retarget on top of it.
            output_file (str): A file path to save the retargeted animation.
                If None, save the result next to the source file.
            anim_config_file (str): A config file providing additional info
                about the source animation.

        Returns:
            str: The output file path.
        """
        self.status_changed.emit(anim_file, util.ExecStatus.kRunning)
        try:
            self.__run(anim_file, new_file, output_file, anim_config_file)
            self.status_changed.emit(anim_file, util.ExecStatus.kSuccess)
        except BaseException as e:
            self.status_changed.emit(anim_file, util.ExecStatus.kFail)
            raise e
