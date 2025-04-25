import math

from maya import cmds, OpenMaya


def get_position(arg):
    """Resolves the input argument into a world positon.

    Args:
        arg (str, Transform, list, MVector, MPoint): A node or a vector.

    Returns:
        MVector: The resolved position.
    """
    if isinstance(arg, (list, tuple)):
        return OpenMaya.MVector(*arg)
    else:
        node = str(arg)
        if cmds.objExists(node):
            pos = cmds.xform(
                node, query=True, worldSpace=True, translation=True)
            return OpenMaya.MVector(*pos)
        else:
            return OpenMaya.MVector(arg)


def distance(a, b):
    """Returns the distance between 2 vectors or 2 nodes.

    Args:
        a (str, Transform, list, MVector): A node or a vector to work with.
        b (str, Transform, list, MVector): A node or a vector to work with.

    Returns:
        float: the distance value.
    """
    a = get_position(a)
    b = get_position(b)
    return (a - b).length()


def get_fractional_position(start, end, fraction=.5, as_tuple=True):
    """Returns the position between a given start position and end position.

    Args:
        start (str, Transform, list, MVector): The start position.
        end (str, Trnasform, list, MVector): The end position.
        fraction (float): The percentage of the new position.
            range: 0 ~ 1. 0: start position, 1: end position.
        as_tuple (bool): If True, return the fractional position as a tuple.
            Otherwise return a MVector.

    Returns:
        MVector or tuple: The fractional position.
    """
    start = get_position(start)
    end = get_position(end)

    pos = (start - end) * fraction
    pos = start - pos

    if as_tuple:
        return (pos[0], pos[1], pos[2])
    return pos


def get_inbetween_positions(start, end, num, mode='start', as_tuple=True):
    """Returns n number of evenly divided position between 2 positions.

    Args:
        start (str, Transform, list, MVector): The start position.
        end (str, Trnasform, list, MVector): The end position.
        num (bool): Number of inbetween positions.
        mode (str): Method used to distribute the positions.
            + "start": First position at start of the ribbon,
                no position at the end.
            + "end": Last position at end of the ribbon,
                no position at the start.
            + "start_end": Create positions at both ends.
            + "mid": No position on the ends.
        as_tuple (bool): If True, return a list of tuples.
            Otherwise return a list of MVector.

    Returns:
        list: A list of positions.
    """
    start = get_position(start)
    end = get_position(end)

    if mode in ('start', 'end'):
        mid_num = num - 1
    elif mode == 'start_end':
        mid_num = num - 2
    else:
        mid_num = num

    if mid_num < 0:
        raise RuntimeError('Not enough mid joints!')

    vec = end - start
    segment = vec.length() / float(mid_num + 1)
    vec.normalize()
    points = [start + vec * (segment * (i + 1)) for i in range(mid_num)]
    if mode.startswith('start'):
        points = [start] + points
    if mode.endswith('end'):
        points.append(end)
    if as_tuple:
        return [v.as_tuple() for v in points]
    return points


def project_point(point, start, end, as_tuple=True):
    """Projects a point onto a line and returns the projected point.

    Args:
        point (str, Transform, list, MVector): A point to project.
        start (str, Transform, list, MVector): The start position of the line.
        end (str, Transform, list, MVector): The end position of the line.

    Returns:
        MVector or tuple: The projected position.
    """
    point = get_position(point)
    start = get_position(start)
    end = get_position(end)
    ref_vec = end - start
    full_dis = ref_vec.length()

    src_vec = point - start
    tgt_dis = (ref_vec * src_vec) / full_dis
    tgt_vec = ref_vec * (tgt_dis / full_dis)
    tgt = tgt_vec + start
    if as_tuple:
        return (tgt[0], tgt[1], tgt[2])
    return tgt


def get_position_center(positions, as_tuple=True):
    """Returns the center position from a list of positions or nodes.

    Args:
        positions (list): A list of positions or nodes.
        as_tuple (bool): If True, return the center position as a tuple.
            Otherwise return a MVector.

    Returns:
        MVector or tuple: The center position.
    """
    center = OpenMaya.MVector()
    for pos in positions:
        center += get_position(pos)
    center /= len(positions)

    if as_tuple:
        return (center[0], center[1], center[2])
    return center


def get_bbx_center(comps, as_tuple=True):
    """Returns the bounding box center of a list of objects or components.

    Args:
        comps (tuple): A list of objects or components to work with.
        as_tuple (bool): If True, return the center position as a tuple.
            Otherwise return a MVector.

    Returns:
        MVector or tuple: The center position.
    """
    bbx = cmds.exactWorldBoundingBox(comps, ignoreInvisible=True)
    center = ((bbx[3] - bbx[0]) / 2.0 + bbx[0],
              (bbx[4] - bbx[1]) / 2.0 + bbx[1],
              (bbx[5] - bbx[2]) / 2.0 + bbx[2])
    if as_tuple:
        return center
    return OpenMaya.MVector(*center)


def get_object_center(objects, bbx=True, as_tuple=True):
    """Returns the center of a list of objects or components.

    Args:
        objects (list): A list of objects or components to work with.
        bbx (bool): If True, operates at the component level (using bounding
            box center). Otherwise operates on each object in the list directly.
        as_tuple (bool): If True, return the center position as a tuple.
            Otherwise return a MVector.

    Returns:
        MVector or tuple: The center position.
    """
    if not isinstance(objects, (list, tuple)):
        objects = [objects]

    positions = []
    for obj in objects:
        if bbx:
            positions.append(get_bbx_center(obj, as_tuple=True))
        else:
            for each in cmds.ls(obj, flatten=True):
                positions.append(cmds.xform(
                    each, query=True, worldSpace=True, translation=True))

    return get_position_center(positions, as_tuple=as_tuple)


def get_object_size(objects):
    """Returns the size of one or more objects.

    Returns:
        tuple: size in x, y, z axis.
    """
    bbx = cmds.exactWorldBoundingBox(
        objects, calculateExactly=True, ignoreInvisible=True)
    return (bbx[3] - bbx[0], bbx[4] - bbx[1], bbx[5] - bbx[2])


def intersect_line(a1, a2, b1, b2, as_tuple=True):
    """Returns the intersection point of 2 lines.

    Args:
        a1, a2 (str, Transform, list, MVector): Nodes or vectors defining 2
            points on a line.
        b1, b2 (str, Transform, list, MVector): Nodes or vectors defining 2
            points on a line.
        as_tuple (bool): If True, return the intersection points as a tuple.
            Otherwise return a MVector.

    Returns:
        tuple or None: (p1, p2) closest intersection point on line1 an line2,
        or None if the 2 lines are parallel with each other.
    """
    # get positions
    a1 = get_position(a1)
    a2 = get_position(a2)
    b1 = get_position(b1)
    b2 = get_position(b2)

    # get normal vectors
    vec_a = a2 - a1
    vec_a.normalize()
    vec_b = b2 - b1
    vec_b.normalize()

    # return None if lines are parallel
    u = vec_a * vec_b
    if u == 1:
        return

    # find the separation projections
    t1 = (b1 - a1) * vec_a
    t2 = (b1 - a1) * vec_b

    # compute distances along vectors
    d = (t1 - u * t2) / (1 - u * u)

    # get the intersection point
    p = a1 + (vec_a * d)

    if as_tuple:
        return (p[0], p[1], p[2])
    return p


def get_closest_transform(pos, xforms):
    """Returns the closest transform to a given position.

    Args:
        pos (str, Transform, list, MVector): A node or a vector to use
            as the source position.
        xforms (list): A list of nodes or vectors.

    Returns:
        The closest item in the xforms list to the given position.
    """
    closest = None
    dist = None
    for each in xforms:
        d = distance(pos, each)
        if dist is None or d < dist:
            closest = each
            dist = d
    return closest


def trig_get_angle(
        adjacent=None, hypotenuse=None, opposite=None, as_degree=False):
    """Returns an angle with distance using trigonometry algorithm."""
    if adjacent and hypotenuse and not opposite:
        cosine = adjacent / hypotenuse
        radian = math.acos(cosine)
    elif adjacent and not hypotenuse and opposite:
        tangent = opposite / adjacent
        radian = math.atan(tangent)
    elif not adjacent and hypotenuse and opposite:
        sine = opposite / hypotenuse
        radian = math.asin(sine)
    else:
        raise ValueError('Need at least 2 input value.')

    if as_degree:
        return math.degrees(radian)
    return radian


def curve_interp(x):
    """Smooth curve interp converter."""
    return 1.0 + 2.0 * x * x * x - 3.0 * x * x


def world_axis_to_vector(axis, length=1):
    """Converts a world axis string to vector.

    Args:
        axis (str): The axis string: x, y, z, -x, -y, or -z
        length (float): The vector length.

    Returns:
        MVector
    """
    if axis.lower() == 'x':
        vec = OpenMaya.MVector(1, 0, 0)
    elif axis.lower() == 'y':
        vec = OpenMaya.MVector(0, 1, 0)
    elif axis.lower() == 'z':
        vec = OpenMaya.MVector(0, 0, 1)
    elif axis.lower() == '-x':
        vec = OpenMaya.MVector(-1, 0, 0)
    elif axis.lower() == '-y':
        vec = OpenMaya.MVector(0, -1, 0)
    elif axis.lower() == '-z':
        vec = OpenMaya.MVector(0, 0, -1)
    else:
        raise ValueError('Invalid input axis!')

    return vec * length


def vector_to_world_axis(vec):
    """Converts a vector to world axis.

    Args:
        vector (tuple or MVector): A vector to convert.

    Returns:
        str or None: The world axis string, or None if
        the vector doesn't match any world axis.
    """
    if isinstance(vec, (tuple, list)):
        vec = OpenMaya.MVector(*vec)
    vec.normalize()

    if vec.isEquivalent(OpenMaya.MVector(1, 0, 0)):
        return 'x'
    elif vec.isEquivalent(OpenMaya.MVector(0, 1, 0)):
        return 'y'
    elif vec.isEquivalent(OpenMaya.MVector(0, 0, 1)):
        return 'z'
    elif vec.isEquivalent(OpenMaya.MVector(-1, 0, 0)):
        return '-x'
    elif vec.isEquivalent(OpenMaya.MVector(0, -1, 0)):
        return '-y'
    elif vec.isEquivalent(OpenMaya.MVector(0, 0, -1)):
        return '-z'


def axis_to_vector(node, axis, length=1, as_tuple=False):
    """Converts a local axis of a given node to vector.

    Args:
        node (str or Transform): A node to extract the local vector from.
        axis (string): The axis to extract. e.g. "x", "-x", etc.
        length (float): The vector length.
        as_tuple (bool): If True, return a tuple, otherwise return MVector.

    Returns:
        MVector or tuple: The axis vector.
    """
    mtx = cmds.getAttr('{}.worldMatrix'.format(node))
    util = OpenMaya.MScriptUtil()
    util.createFromList(mtx, 16)
    mtx = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(util.asFloat4Ptr()))
    quat = mtx.rotation()
    vec = world_axis_to_vector(axis, length)
    vec = vec.rotateBy(quat)
    if as_tuple:
        return vec[0], vec[1], vec[2]
    return vec


def closest_axis_to_vector(source, target_vec, exclude_axis=None):
    """Returns the closest axis of a source node to a target axis.

    Args:
        source (str or Transform): The source transform node.
        target_vec (list or MVector): The target vector to compare against.
        exclude_axis (str): An axis on the source node to exclude.

    Returns:
       str: The closest axis on the source node.
    """
    if isinstance(target_vec, (list, tuple)):
        target_vec = OpenMaya.MVector(*target_vec)

    ang_dict = {}
    for axis in ('x', '-x', 'y', '-y', 'z', '-z'):
        if exclude_axis and axis.endswith(exclude_axis):
            continue
        vec = axis_to_vector(source, axis)
        ang = vec.angle(target_vec)
        ang_dict[ang] = axis
    return ang_dict[min(ang_dict.keys())]


def closest_axis(source, target, target_axis, exclude_axis=None):
    """Returns the closest axis of a source node to a target axis.

    Args:
        source (str or Transform): The source transform node.
        target (str or Transform): The target transform node.
        target_axis (str): The target axis.
        exclude_axis (str): An axis on the source node to exclude.

    Returns:
       str: The closest axis on the source node.
    """
    target_vec = axis_to_vector(target, target_axis)
    return closest_axis_to_vector(source, target_vec, exclude_axis=exclude_axis)


def closest_world_axis(target, target_axis, exclude_axis=None):
    """Returns the closest world axis to a target transform node.

    Args:
        target (str or Transform): The target transform node.
        target_axis (str): The target axis.
        exclude_axis (str): An world axis to exclude.

    Returns:
       str: The closest world axis.
    """
    target_vec = axis_to_vector(target, target_axis)
    ang_dict = {}
    for axis in ('x', '-x', 'y', '-y', 'z', '-z'):
        if exclude_axis and axis.endswith(exclude_axis):
            continue
        vec = world_axis_to_vector(axis)
        ang = vec.angle(target_vec)
        ang_dict[ang] = axis
    return ang_dict[min(ang_dict.keys())]


def flatten_orientation(xform, axis):
    """Flattens the orientation of a given xform to the closest world axis.

    Args:
        xform (str or Transform): The transform node to flatten.
        axis (str): An axis on the transform node to flatten to
            its closest world axis.

    Returns:
        None
    """
    vec = axis_to_vector(xform, axis)
    w_axis = closest_world_axis(xform, axis)
    w_vec = world_axis_to_vector(w_axis)
    quat = OpenMaya.MQuaternion(vec, w_vec)

    mtx = cmds.getAttr('{}.worldMatrix'.format(xform))
    util = OpenMaya.MScriptUtil()
    util.createFromList(mtx, 16)
    mtx = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(util.asFloat4Ptr()))

    mtx.rotateBy(quat, OpenMaya.MSpace.kWorld)
    cmds.xform(xform, worldSpace=True, matrix=mtx.as_tuple())
    if cmds.nodeType(xform) == 'joint':
        cmds.makeIdentity(xform, apply=True, scale=True)
