"""
Node alignment utility function
"""

from maya import cmds

# import mhy.maya.nodezoo
import mhy.maya.utils as mutil
import mhy.maya.maya_math as mmath


@mutil.undoable
@mutil.repeatable
def align_colinear(nodes=None, even_space=False):
    """Moves a list of nodes onto a line formed by the first node
    and the last node.

    Args:
        nodes (list or None): A list of nodes to align.
            If None, use the selected objects.
        even_space (bool): Evenly space each node on the line?

    Returns:
        None
    """
    if not nodes:
        nodes = cmds.ls(selection=True, type='transform') or []

    if len(nodes) < 3:
        cmds.warning('Need 3+ objects to align colinear!')
        return

    pnt_a = mmath.get_position(nodes[0])
    pnt_b = mmath.get_position(nodes[-1])
    nodes = nodes[1:-1]

    if even_space:
        nodes.sort()
        points = mmath.get_inbetween_positions(
            pnt_a, pnt_b, len(nodes), mode='mid')
        for node, pnt in zip(nodes, points):
            cmds.xform(node, worldSpace=True, translation=pnt)
    else:
        for node in nodes:
            tgt = mmath.project_point(node, pnt_a, pnt_b, as_tuple=True)
            cmds.xform(node, worldSpace=True, translation=tgt)


@mutil.undoable
@mutil.repeatable
def align_coplanar(nodes=None):
    """Moves a list of nodes onto a plane formed by the first 3 nodes.

    Args:
        nodes (list or None): A list of nodes to align.
            If None, use the selected objects.

    Returns:
        None
    """
    if not nodes:
        nodes = cmds.ls(selection=True, type='transform')

    if len(nodes) < 4:
        cmds.warning('Need 4+ objects to align coplanar!')
        return

    # get pos and p
    points = [mmath.get_position(n) for n in nodes]

    u = points[1] - points[0]
    v = points[2] - points[1]
    n = (u ^ v).normal()

    # per point math
    new_points = []
    for node, pnt in zip(nodes, points):
        q = pnt - points[0]
        dist = q * n
        new_points.append(pnt - n * dist)

    # move points
    for node, pnt in zip(nodes, new_points):
        cmds.xform(node, worldSpace=True, translation=pnt.as_tuple())


def snap(sources=None, targets=None):
    """Snaps a list of source nodes onto the center of the target nodes.

    Args:
        sources (Node or list): One node or a list of source nodes to snap.
            If None, use the last selected item.
        targets (Node or list): One node or a list of target nodes to snap to.
            If None, use the currently selected item.

    Returns:
        None
    """
    if not targets:
        targets = cmds.ls(selection=True)

    if not sources:
        sources = cmds.ls(selection=True)
        if not sources:
            cmds.warning('Nothing selected!')
            return
        sources = sources[-1]

    if not targets or not sources:
        cmds.warning('No target or source object provided.')
        return

    if not isinstance(targets, (list, tuple)):
        targets = [targets]
    if not isinstance(sources, (list, tuple)):
        sources = [sources]

    targets = set(targets) - set(sources)

    ctr = mmath.get_bbx_center(targets, as_tuple=True)
    for node in sources:
        if '.' in node or \
           'transform' not in cmds.nodeType(node, inherited=True):
            cmds.warning('Source object {} is not a transform!'.format(sources))
            continue
        cmds.xform(node, worldSpace=True, translation=ctr)
