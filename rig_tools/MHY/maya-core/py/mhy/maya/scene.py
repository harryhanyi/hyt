"""
This modules contains maya scene functions
"""
from maya import cmds, OpenMaya

# use node class dict to get class methods, to support 2-way imports.
from mhy.maya.nodezoo._manager import _NODE_TYPE_LIB


def safe_open(*args, **kwargs):
    """Wrappers cmds.file() to avoid interruption when error raised
    while opening file."""
    rnn = kwargs.get('returnNewNodes', kwargs.get('rnn', False))
    nodes = []
    if rnn:
        imp = kwargs.get('i')
        ref = kwargs.get('reference', kwargs.get('r'))
        if ref or imp:
            nodes = cmds.ls(dependencyNodes=True)
    result = None
    try:
        result = cmds.file(*args, **kwargs)
    except RuntimeError as e:
        OpenMaya.MGlobal.displayError(str(e))
    if rnn and result is None:
        return list(set(cmds.ls(dependencyNodes=True)) - set(nodes))
    return result


def get_reference_nodes(file_path=None):
    """ Returns reference nodes in the scene.

    Args:
        file_path (str or None): If not None, return
            reference nodes associated with this file.
            Otherwise return all reference nodes.

    Returns:
        list: A list of reference node objects.
    """
    cls = _NODE_TYPE_LIB['reference']
    return cls.get_reference_nodes(file_path=file_path)


FRAME_RATE_DICT = {
    'film': 24,
    'show': 48,
    'pal': 25,
    'ntsc': 30,
    'palf': 50,
    'ntscf': 60
}


def _sanitize_frame_rate(frame_rate):
    """Converts a frame rate from number to time unit string."""
    if isinstance(frame_rate, (int, float)):
        for key, val in FRAME_RATE_DICT:
            if val == frame_rate:
                return key
        return '{}fps'.format(frame_rate)
    return frame_rate


def is_frame_rates_valid(frame_rate):
    """Checks if a frame rate is valid."""
    frame_rate = _sanitize_frame_rate(frame_rate)
    if frame_rate.endswith('fps'):
        return True
    if frame_rate in FRAME_RATE_DICT:
        return True
    return False


def get_frame_rate(as_string=True):
    """Returns the current frame rate.

    Args:
        as_str (bool): If True, returns the string format.
            Otherwise convert to float.

    Returns:
        str or float
    """
    r = cmds.currentUnit(query=True, time=True)
    if as_string:
        return r
    else:
        if r.endswith('fps'):
            return float(r[:-3])
        return FRAME_RATE_DICT.get(r)


def set_frame_rate(frame_rate):
    """Sets the current frame rate.

    Args:
        frame_rate (float or str): The frame rate to set to.

    Returns:
        None
    """
    if not is_frame_rates_valid(frame_rate):
        raise ValueError('Invalid frame rate: {}'.format(frame_rate))
    cmds.currentUnit(time=_sanitize_frame_rate(frame_rate))


def get_anim_layers(include_base=False):
    """Returns a list of anim layers in the scene with
    hierarchical order.

    Args:
        include_base (bool): Include the base layer?

    Returns:
        list
    """
    cls = _NODE_TYPE_LIB['animLayer']
    return cls.get_anim_layers(include_base=include_base)
