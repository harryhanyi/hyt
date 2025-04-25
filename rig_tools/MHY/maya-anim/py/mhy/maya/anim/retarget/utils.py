import os
import copy
import json
import six
from collections import OrderedDict

from maya import cmds

import mhy.python.core.logger as logger
from mhy.maya.standard.name import NodeName
import mhy.maya.scene as sutil

import mhy.maya.anim.retarget.constants as const


class ExecStatus():
    """Retarget execution status."""

    kRunning = -1
    kFail = 0
    kSuccess = 1
    kNone = 2


def log_info(msg):
    logger.info('[RETARGETER] {}'.format(msg))


def log_warn(msg):
    logger.warn('[RETARGETER] {}'.format(msg))


def log_error(msg):
    raise RetargetError('[RETARGETER] {}'.format(msg))


class RetargetError(Exception):
    """Generic retargeter error."""
    pass


def clean_name(name):
    """Returns the clean name of a given node name.
    (without namespaces and parent names)"""
    return str(name).split('|')[-1].split(':')[-1]


def validate_file_path(path, exts=None, file_type=None, check_exists=True):
    """Validates a file path, ensures it exists and matches
    the required extensions.

    Args:
        path (str): A path to validate.
        exts (str or list): One or more required extensions.
        file_type (str): The file type string.
            Only used in error messages.
        check_exists (bool): If True, also check if the file exists.

    Returns:
        None

    Raises:
        ValueError: If the file doesn't exist or doesn't
            meet extension requirements.
    """
    if not isinstance(exts, (tuple, list)):
        exts = [exts]

    if not path or \
       not os.path.splitext(path)[-1][1:] in exts:
        if file_type:
            msg = 'Invalid {} file: {}'.format(file_type, path)
        else:
            msg = 'Invalid file: {}'.format(path)
        msg += ' Valid extensions are {}'.format(exts)
        raise ValueError(msg)

    if check_exists and not os.path.isfile(path):
        raise ValueError('File not found: {}'.format(path))


def _mirror_config_data(data):
    """Fills the missing side in a config data by mirroring
    from the provided side."""
    mirrored_data = copy.deepcopy(data)
    for key in (const.KEY_SRC_HIK, const.KEY_TGT_HIK):
        if key not in data:
            continue
        for element, node in data[key].items():
            if element.startswith('Left'):
                m_element = element.replace('Left', 'Right', 1)
            elif element.startswith('Right'):
                m_element = element.replace('Right', 'Left', 1)
            else:
                continue

            if m_element not in data[key]:
                m_node = NodeName.flip_node_name(node)
                mirrored_data[key][m_element] = m_node

    for key in (const.KEY_TGT_NODE, const.KEY_DYN_ATTR):
        mirrored_data.setdefault(key, {})
        if key not in data:
            continue
        for node, val in data[key].items():
            fnode = NodeName.flip_node_name(node)
            if node != fnode and fnode not in mirrored_data[key]:
                fval = val
                if val and isinstance(val, six.string_types):
                    fval = NodeName.flip_node_name(val)
                elif isinstance(val, dict):
                    fval = {}
                    for k, v in val.items():
                        if k == 'position':
                            v = [[NodeName.flip_node_name(x[0]), x[1]]
                                 for x in v]
                            fval['position'] = v
                        elif k == 'aim':
                            fval['aim'] = [NodeName.flip_node_name(v[0]), v[1]]
                        else:
                            fval[k] = v

                mirrored_data[key][fnode] = fval

    return mirrored_data


def is_fbx(file_path):
    """Checks if a file path is fbx."""
    return file_path.lower().endswith('.fbx')


def read_config_file(config_file, auto_fill=True):
    """Reads in a character config file (JSON) and auto-fills missing data.

    Args:
        config_file (str): A config file to read.
        auto_fill (bool): If True, fill data for the missing side.

    Returns:
        dict: The config data.
    """
    data = {}
    with open(config_file, 'r') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    # validate config file
    if const.KEY_SRC_HIK in data:
        if const.KEY_TGT_HIK not in data:
            log_error(
                'Incomplete human ik data. Missing target skeleton definition.')
        hik_data = data[const.KEY_SRC_HIK]
        if len(hik_data) != len(set(hik_data.values())):
            log_error('Source human ik data contains duplicated joints.')

    if const.KEY_TGT_HIK in data:
        if const.KEY_SRC_HIK not in data:
            log_error(
                'Incomplete human ik data. Missing source skeleton definition.')
        hik_data = data[const.KEY_TGT_HIK]
        if len(hik_data) != len(set(hik_data.values())):
            log_error('Target human ik data contains duplicated joints.')

        if const.KEY_TGT_NODE not in data:
            log_error('Incomplete config data. Missing key "target_to_source".')

        nodes = set()
        for each in data[const.KEY_TGT_NODE].values():
            nodes = nodes | set(get_source_names(each))
        unmapped = nodes - set(hik_data.values())
        if unmapped:
            log_error(
                'Mapped joints not found in target human ik data: {}'.format(
                    unmapped))

    # backwards compatibility warning
    if 'target_to_source' in data:
        log_error(
            ('Key "target_to_source" has been renamed to "{}". '
             'Please update your config file: {}').format(
                 const.KEY_TGT_NODE, config_file))

    if auto_fill:
        return _mirror_config_data(data)
    return data


def get_source_names(source_value):
    """Returns the source rig node names fram a config value."""
    if isinstance(source_value, dict):
        src_names = set()
        for key, val in source_value.items():
            if key == 'position':
                src_names = src_names | set([x[0] for x in val])
            elif key == 'aim':
                src_names.add(val[0])
        return list(src_names)
    else:
        return [source_value]


def iter_source_node_names(retarget_config):
    """Iterates over source node names in a retarget config dict."""
    node_set = set()
    for source in retarget_config[const.KEY_TGT_NODE].values():
        for node in get_source_names(source):
            if node not in node_set:
                node_set.add(node)
                yield node


def get_animated_time_ranges(nodes, flatten=True):
    """Returns time range data from keyframes on a set of nodes.

    Args:
        nodes (list): A list of nodes to scan.
        flatten (bool): If True, flatten data into a single list,
            otherwise returns a dict of
            {anim layer object: range list} pairs.

    Returns:
        dict or list
    """
    time_ranges = {}
    layers = sutil.get_anim_layers(include_base=True)
    if not layers:
        layers = [None]

    for layer in layers:
        if layer:
            layer.isolate()

        min_key = None
        max_key = None
        for node in nodes:
            keys = cmds.keyframe(node, query=True, timeChange=True)
            if keys:
                mink = min(keys)
                if min_key is None or mink < min_key:
                    min_key = mink
                maxk = max(keys)
                if max_key is None or maxk > max_key:
                    max_key = maxk

        if min_key is not None and max_key is not None:
            time_ranges[layer] = [(float(min_key), float(max_key))]

    if flatten and not time_ranges:
        return []
    elif flatten:
        flat_ranges = [None, None]
        for layer, ranges in time_ranges.items():
            if flat_ranges[0] is None or flat_ranges[0] > ranges[0][0]:
                flat_ranges[0] = ranges[0][0]
            if flat_ranges[1] is None or flat_ranges[1] < ranges[0][1]:
                flat_ranges[1] = ranges[0][1]
        return [flat_ranges]
    else:
        return time_ranges


def key_attr(attr, anim_layer=None, in_tangent='flat', out_tangent='flat'):
    """Sets a keyframe on an attribute on the current frame.

    Args:
        attr (string): An attribute to work with.
        anim_layer (string): Name of an anim layer to set the keyframe in.
    """
    if not anim_layer or anim_layer == const.BASE_LAYER:
        cmds.setKeyframe(attr)
    else:
        cmds.setKeyframe(
            attr, animLayer=anim_layer,
            inTangentType=in_tangent, outTangetType=out_tangent)


def iter_xform_attrs(skip_translate=False):
    """A generator that yields transform attributes one at a time.

    Args:
        skip_translate (bool): Skip translation?

    Yields:
        str: transform attribute name.
    """
    for attr in 'trs' if not skip_translate else 'rs':
        for ax in 'xyz':
            yield attr + ax


def key_xform(
        xform, anim_layer=None, skip_translate=False,
        in_tangent='flat', out_tangent='flat'):
    """Sets keyframes on all transform attributes on the current frame.

    Args:
        node (string): A transform node to work with.
        anim_layer (string): Name of an anim layer to set the keyframe in.
        skip_translate (bool): Skip translation?
    """
    for attr in iter_xform_attrs(skip_translate=skip_translate):
        key_attr(
            '{}.{}'.format(xform, attr), anim_layer=anim_layer,
            in_tangent=in_tangent, out_tangent=out_tangent)


def attr_animated(attr, frame=None):
    """Checks if an attribute is animated.

    Args:
        frame (int or None): The frame to check.
            If None, check all frames.

    Returns:
        bool
    """
    kwargs = {'query': True, 'timeChange': True}
    if frame is not None:
        kwargs['time'] = (frame, frame)

    if cmds.keyframe(attr, **kwargs):
        return True
    return False


def xform_animated(node, frame=None):
    """Checks if any transform attributes is animated.

    Args:
        frame (int or None): The frame to check.
            If None, check all frames.

    Returns:
        bool
    """
    for attr in iter_xform_attrs():
        status = attr_animated('{}.{}'.format(node, attr), frame=frame)
        if status:
            return status
    return False


def get_attr_keys(attr, time_ranges):
    """Returns a list of keyframes of an attribute,
    within a list of time ranges.

    Args:
        attr (string): An attribute to check.
        time_ranges (list): A list of time ranges. e.g. [[1, 90], [200, 280]]

    Returns:
        [int]: A list of keyframes.
    """
    keys = set()
    for tm in time_ranges:
        keys = keys | set(tm)

    for key in set(cmds.keyframe(attr, query=True, timeChange=True) or []):
        key = float(key)
        for tm in time_ranges:
            s = float(tm[0])
            e = float(tm[1])
            if key >= s and key <= e:
                keys.add(key)
                break

    return sorted(list(keys))


def get_xform_keys(xform, time_ranges, as_set=False):
    """Returns a list of keyframes of a transform node,
    within a list of time ranges.

    Args:
        xform (string): A transform node to work with.
        time_ranges (list): A list of time ranges. e.g. [[1, 90], [200, 280]]

    Returns:
        [int]: A list of keyframes.
    """
    keys = set()

    for tm in time_ranges:
        keys = keys | set(tm)

    for attr in 'trs':
        for key in set(cmds.keyframe(
                xform + '.' + attr, query=True, timeChange=True) or []):
            key = float(key)
            for tm in time_ranges:
                s = float(tm[0])
                e = float(tm[1])
                if key >= s and key <= e:
                    keys.add(key)
                    break

    if as_set:
        return keys
    return sorted(list(keys))


def remap_value(val, remapper):
    """Remaps a value using a given remapper.

    Valid remapper format:
        + (float) multiplier
        + (dict) {old_value: new_value} pairs.

    Args:
        val (numeric): A value to remap.
        remapper (float or dict): A remapper.

    Returns:
        The remapped value.
    """
    if isinstance(remapper, dict):
        return remapper.get(str(val), val)
    return val * remapper


def get_closest_parent(node, parents):
    """Finds and returns the closest parent of a given node."""
    parents = set(parents)
    parent = node
    while parent:
        parent = cmds.listRelatives(parent, parent=True, fullPath=True)
        if parent:
            parent = parent[0]
            if parent in parents:
                return parent
