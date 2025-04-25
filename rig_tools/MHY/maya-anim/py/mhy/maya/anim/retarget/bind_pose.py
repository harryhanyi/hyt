import os
import json
import shutil
from collections import OrderedDict

from maya import cmds

import mhy.maya.scene as sutil

import mhy.maya.anim.retarget.constants as const
import mhy.maya.anim.retarget.utils as util


CACHE_PATH = os.path.expanduser('~')
if CACHE_PATH.endswith('Documents'):
    CACHE_PATH = CACHE_PATH.replace('Documents', '')[:-1]
CACHE_PATH = os.path.join(CACHE_PATH, '.cache', 'MHY', 'anim_retargeter')


def clear_cache():
    """Deletes all bind pose cache."""
    if os.path.isdir(CACHE_PATH):
        try:
            shutil.rmtree(CACHE_PATH)
            util.log_info('Cleared bind pose cache.')
        except OSError as e:
            util.log_error(
                'Failed clearing bind pose cache: {}'.format(e.strerror))


def _invert_dict(data):
    """Swaps key and value in a dict data."""
    inverted_dict = {}
    for key, val in data.items():
        inverted_dict[val] = key
    return inverted_dict


class BindPose(object):
    """
    Convenience class for caching and reading bind pose data.
    """

    def __init__(self, config_file, src_rig, tgt_rig):
        """Initializes a retargeter object.

        Args:
            config_file (str): The retarget config file path.
            src_rig (str): The source rig file path.
            tgt_rig (str): The target rig file path.
        """
        util.validate_file_path(
            config_file, const.EXT_CONFIG, 'retarget config')
        self.__config_file = config_file
        if src_rig:
            util.validate_file_path(src_rig, const.EXT_MAYA, 'source rig')
        self.__src_rig = src_rig
        util.validate_file_path(tgt_rig, const.EXT_MAYA, 'target rig')
        self.__tgt_rig = tgt_rig

    def get_bind_pose_data(self, source_type):
        """Extracts bind pose data in the current scene.

        Args:
            source_type (str): the source type.
                values are: "source", "target", "source_hik", or "target_hik"

        Returns:
            dict: The cache data.
        """
        # read retarget config file
        util.validate_file_path(
            self.__config_file, const.EXT_CONFIG, 'retarget config')
        config = util.read_config_file(self.__config_file)
        has_hik = const.KEY_SRC_HIK in config

        # figure out the rig file path, and nodes to process
        element_dict = None
        bp_node = set()
        if source_type == 'source_hik':
            element_dict = config.get(const.KEY_SRC_HIK)
            if not element_dict:
                cmds.warning(
                    'Config missing source hik: {}'.format(self.__config_file))
            node_names = set(element_dict.values())
            element_dict = _invert_dict(element_dict)
        elif source_type == 'target_hik':
            element_dict = config.get(const.KEY_TGT_HIK)
            if not element_dict:
                cmds.warning(
                    'Config missing target hik: {}'.format(self.__config_file))
            node_names = set(element_dict.values())
            element_dict = _invert_dict(element_dict)
        elif source_type == 'source':
            node_names = util.iter_source_node_names(config)
        else:
            node_names = set(config[const.KEY_TGT_NODE].keys())

        # establish bind pose data
        bp_data = {
            'matrix': OrderedDict()
        }
        if has_hik:
            bp_data['parent'] = {}
            bp_data['hik_element'] = {}

        # process nodes
        node_long_names = []
        for node_name in node_names:
            long_name = cmds.ls(
                '{}:{}'.format(const.NAMESPACE_SRC, node_name), long=True)
            if not long_name:
                long_name = cmds.ls(
                    '{}:*:{}'.format(const.NAMESPACE_SRC, node_name), long=True)
            if not long_name:
                long_name = cmds.ls(node_name, long=True)

            if len(long_name) != 1:
                util.log_error(
                    ('Node "{}" not found in {} rig '
                     'or is not unique.').format(
                         node_name, source_type.replace('_hik', '')))
            long_name = long_name[0]

            # for source human ik skeletons record the skeleton bind pose nodes
            if source_type == 'source_hik' and \
               cmds.nodeType(long_name) == 'joint':
                bp = cmds.listConnections(
                    long_name + '.bindPose',
                    source=False, destination=True, plugs=False)
                if bp:
                    bp_node = bp_node | set(bp)

            node_long_names.append(long_name)

        # go to bind pose
        if len(bp_node) > 1:
            raise RuntimeError(source_type + ' contains multiple bind poses.')
        elif bp_node:
            bp_node = bp_node.pop()
            cmds.dagPose(bp_node, restore=True)

        node_long_names.sort()
        for long_name in node_long_names:
            sn = util.clean_name(long_name)
            bp_data['matrix'][sn] = cmds.xform(
                long_name, query=True, worldSpace=True, matrix=True)

            if source_type.endswith('_hik'):
                parent = util.get_closest_parent(long_name, node_long_names)
                if parent:
                    bp_data['parent'][sn] = util.clean_name(parent)
                bp_data['hik_element'][sn] = element_dict[sn]

        return bp_data

    def cache_bind_pose(self, source_type):
        """Caches bind pose data.

        Args:
            source_type (str): the source type.
                values are: "source", "target", "source_hik", or "target_hik"

        Returns:
            dict: The cache data.
        """
        # read retarget config file
        util.validate_file_path(
            self.__config_file, const.EXT_CONFIG, 'retarget config')
        config = util.read_config_file(self.__config_file)
        has_hik = const.KEY_SRC_HIK in config

        if source_type == 'source_hik':
            rig_file = self.__src_rig
        elif source_type == 'target_hik':
            rig_file = self.__tgt_rig
        elif source_type == 'source':
            if has_hik:
                rig_file = self.__tgt_rig
            else:
                rig_file = self.__src_rig
        else:
            rig_file = self.__tgt_rig

        # open the rig
        cur_file = cmds.file(query=True, sceneName=True) or ''
        cur_file = cur_file.replace('\\', '/')
        if not cur_file or cur_file != rig_file:
            kwargs = {'force': True}
            if util.is_fbx(rig_file):
                cmds.file(force=True, newFile=True)
                kwargs['i'] = True
            else:
                kwargs['open'] = True
            sutil.safe_open(rig_file, **kwargs)

        # get bind pose data
        bp_data = self.get_bind_pose_data(source_type=source_type)

        # insert header data
        bp_data['header'] = {
            'rig_file': rig_file,
            'config_file': self.__config_file,
            'rig_timestamp': os.path.getmtime(rig_file),
            'config_timestamp': os.path.getmtime(self.__config_file)
        }

        # dump data
        if not os.path.isdir(CACHE_PATH):
            os.makedirs(CACHE_PATH)
        bp_file = os.path.join(
            CACHE_PATH, 'bind_pose_{}.{}'.format(source_type, const.EXT_CONFIG))

        with open(bp_file, 'w+') as f:
            json.dump(bp_data, f, indent=2)
            util.log_info(
                'Cached {} bind pose to {}'.format(source_type, bp_file))

        return bp_data

    def read_bind_pose(self, source_type, auto_update=True):
        """Reads bind pose data cache.

        Args:
            source_type (str): the source type.
                values are: "source", "target", "source_hik", or "target_hik"
            auto_update (bool): If True, automatically updates the bind pose
                data if its invalid or out-dated.

        Returns:
            dict: The bind pose data.
        """
        bp_file = os.path.join(
            CACHE_PATH, 'bind_pose_{}.{}'.format(source_type, const.EXT_CONFIG))
        if source_type.startswith('source'):
            rig_file = self.__src_rig
        else:
            rig_file = self.__tgt_rig

        # ensure cache data exists
        if not os.path.isfile(bp_file):
            if auto_update:
                util.log_info(
                    'Auto updating {} bind pose cache...'.format(source_type))
                return self.cache_bind_pose(source_type)
            else:
                raise RuntimeError('bind pose cache not found!')

        # load cache data
        bp_data = None
        with open(bp_file, 'r') as f:
            bp_data = json.load(f, object_pairs_hook=OrderedDict)

        # ensure cache data is valid
        if not bp_data or 'header' not in bp_data or 'matrix' not in bp_data:
            if auto_update:
                util.log_info(
                    'Auto updating {} bind pose cache...'.format(source_type))
                bp_data = self.cache_bind_pose(source_type)
            else:
                raise RuntimeError(
                    'Invalid bind pose cache: {}'.format(bp_file))

        # ensure cache data is up-to-date
        conf_file = self.__config_file
        if bp_data['header']['rig_file'] != rig_file or \
           bp_data['header']['rig_timestamp'] < os.path.getmtime(rig_file) or \
           bp_data['header']['config_file'] != conf_file or \
           bp_data['header']['config_timestamp'] < os.path.getmtime(conf_file):
            if auto_update:
                util.log_info(
                    'Auto updating {} bind pose cache...'.format(source_type))
                bp_data = self.cache_bind_pose(source_type)

        return bp_data
