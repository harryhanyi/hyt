"""
Open Maya utilities.
"""
import re
import six
import bisect

from maya import cmds
from maya.api import OpenMayaAnim, OpenMaya

from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.nodezoo.node import Node


def mesh_size(mesh_name):
    """
    return model size.

    Args:
        mesh_name:

    Returns:
        list: The size of the bounding box of mesh in x, y, z axises
    """
    bbox = cmds.polyEvaluate(mesh_name, boundingBox=1)
    return [abs(bbox[0][1]-bbox[0][0]), abs(bbox[1][1]-bbox[1][0]), abs(bbox[2][1]-bbox[2][0])]


def is_float_equal(value0, value1, epsilon=0.00001):
    """
    Compare two float value the same.
    """
    return abs(value0-value1) < epsilon


def round_to_value(value, decimal=Settings.pose_decimal):
    return round(value, decimal)


def round_to_str(value, decimal=Settings.pose_decimal):
    decimal_steps = pow(10, decimal)
    return '{0:.2g}'.format(float(round(value*decimal_steps)) / decimal_steps)


def is_string(value):
    """
    check if an value's type is string.
    """
    return isinstance(value, six.string_types)


def anim_curve_cleanup(anim_curve_fn):
    while anim_curve_fn.numKeys:
        anim_curve_fn.remove(0)


def get_anim_curve_fn(curve_anim_node_name):
    """
    get curveAnim function from curve node name.
    """
    try:
        select_list = OpenMaya.MSelectionList()
        select_list.add(curve_anim_node_name)
        node_obj = select_list.getDependNode(0)
        if not node_obj:
            return None
        return OpenMayaAnim.MFnAnimCurve(node_obj)
    except Exception:
        return None


def clear_curve(curve_fn):
    """
    Remove all the keys of the animCurve Node.
    """
    while curve_fn.numKeys != 0:
        curve_fn.remove(0)


def copy_curve(src, dst, value_func=None):
    """
        copy node date between two curve node names.
    """
    src_curve_fn = get_anim_curve_fn(src)
    dst_curve_fn = get_anim_curve_fn(dst)
    clear_curve(dst_curve_fn)
    for index in range(src_curve_fn.numKeys):
        key = src_curve_fn.input(index)
        value = src_curve_fn.value(index)
        if value_func:
            value = value_func(value)
        tit = src_curve_fn.inTangentType(index)
        tot = src_curve_fn.outTangentType(index)
        dst_curve_fn.addKey(key, value, tangentInType=tit,
                            tangentOutType=tot)


def get_alias_index_name(node_name, alias_name):
    result = []
    attribute_list = cmds.aliasAttr(node_name, query=True)
    if attribute_list is None:
        return result
    alias_length = len(attribute_list)/2
    for alias_index in range(alias_length):
        name = attribute_list[alias_index*2]
        if name == alias_name:
            return attribute_list[alias_index*2+1]
    return result


def get_attribute_indices(node_name, attribute_name):
    result = []
    attribute_list = cmds.aliasAttr(node_name, query=True)
    if attribute_list is None:
        return result
    prefix = attribute_name + '['
    prefix_length = len(prefix)
    alias_length = int(len(attribute_list)/2)
    for alias_index in range(alias_length):
        attribute = attribute_list[alias_index*2+1]
        if len(attribute) >= prefix_length+2:
            if prefix == attribute[:prefix_length]:
                index = int(attribute[prefix_length:-1])
                result.append(index)
    return result


def get_a_free_index(indices):
    indices = sorted(indices)
    free_index = 0
    for index in indices:
        if free_index != index:
            return free_index
        free_index += 1
    return free_index


def get_a_free_index_attribute(node_name, attribute_name):
    indices = get_attribute_indices(node_name, attribute_name)
    index = get_a_free_index(indices)
    index_attribute_name = "{}.{}[{}]".format(node_name, attribute_name, index)
    return index, index_attribute_name


def split_index_attribute(attribute_name):
    split_str_list = attribute_name.split('[')
    if len(split_str_list) == 2:
        return split_str_list[0], int(split_str_list[1][:-1])
    return None, None


def get_alias_indices(node_name, array_attribute_name):
    result = {}
    attribute_list = cmds.aliasAttr(node_name, query=True)
    if attribute_list is None:
        return result
    alias_length = len(attribute_list)/2
    for alias_index in range(alias_length):
        attribute = attribute_list[alias_index*2+1]
        attribute_name, index = split_index_attribute(attribute)
        if attribute_name == array_attribute_name:
            result[attribute_list[alias_index*2]] = index
    return result


def remove_all_in_list(array, value):
    while value in array:
        array.remove(value)
    return array


def log_message(pose_name, percent):
    print("{}%% {}".format(percent, pose_name))


def progress_lambda_begin(title, status, isInterruptable):
    if Settings.batch_mode:
        print("{}.\n{}.\n".format(title, status))
        return lambda pose_name, percent: log_message(pose_name, percent)

    cmds.progressWindow(title=title,
                        progress=0.0,
                        status=status,
                        isInterruptable=isInterruptable)
    return lambda pose_name, percent: \
        cmds.progressWindow(edit=True, progress=percent, status=pose_name)


def progress_lambda_end():
    if not Settings.batch_mode:
        cmds.progressWindow(endProgress=True)


def get_all_attributes(node_name):
    attributes_dict = {}
    attributes = cmds.listAttr(node_name)
    for attribute in attributes:
        attribute_name = '{}.{}'.format(node_name, attribute)
        try:
            attribute_type = cmds.getAttr(attribute_name, type=True)
            if attribute_type in ['message', 'TdataCompound']:
                continue
            attributes_dict[attribute] = cmds.getAttr(attribute_name)
        except RuntimeError:
            continue
    return attributes_dict


def is_int(value):
    """
    Check if the value can be converted to an integer
    Args:
        value(object): Any type of object

    Returns:
        bool: If value can be casted to int

    """
    try:
        int(value)
        return True
    except ValueError:
        return False

# =========================================================
# Mirror functions
# =========================================================


def create_mirror_list(geo_base, mirror_plane='ZY',
                       tolerance=0.00001,
                       ):
    """

    Args:
        geo_base:
        mirror_plane:
        tolerance:

    Returns:

    """
    # ===========================================================================
    # CREATE AN MIRROR WARNING WHEN GEOMETRY ISNT SYMMETRICAL
    # ===========================================================================

    if mirror_plane == 1:
        mirror_plane = 'XY'
    elif mirror_plane == 2:
        mirror_plane = 'YZ'
    elif mirror_plane == 3:
        mirror_plane = 'XZ'

    if len(geo_base) != 1:
        for i in geo_base:
            list_con = cmds.listConnections(i, c=True)
            try:
                for c in list_con:
                    if '.worldMesh' in c:
                        geo_base = i
                        break
            except RuntimeError:
                pass
    else:
        geo_base = geo_base[0]

    x_list_b = cmds.xform(geo_base + '.cp[*]', q=True, os=True, t=True)
    count_comp = int(len(x_list_b) / 3)
    list_string = []
    for x in range(count_comp):
        list_string.append(x)
    axis = mirror_plane_return(mirror_plane, mode='axis')

    cmds.refresh()
    geo_base_points = []
    sub_point = []
    last_value = x_list_b[-1]
    for i in range(len(x_list_b)):
        if len(sub_point) < 3:
            sub_point.append(x_list_b[i])
            if x_list_b[i] == last_value and i == (len(x_list_b) - 1):
                sub_point.append(len(geo_base_points))
                geo_base_points.append(sub_point)
        else:
            sub_point.append(len(geo_base_points))
            geo_base_points.append(sub_point)
            sub_point = [x_list_b[i]]

    geo_base_points.sort(key=lambda c: c[axis])
    geo_axis_points = x_list_b[axis::3]
    geo_axis_points.sort()
    match_list = []
    for v in range(len(geo_base_points)):

        point_a = (geo_base_points[v][0],
                   geo_base_points[v][1],
                   geo_base_points[v][2])
        value_axis = abs(point_a[axis])

        r_list = bisect_list(geo_axis_points, value_axis, tolerance)

        for p in range(r_list[0], r_list[1]):
            point_b = (geo_base_points[p][0],
                       geo_base_points[p][1],
                       geo_base_points[p][2])

            if is_mirror_py(point_a, point_b, mirror_plane, tolerance):
                if point_a[0] >= 0:
                    match_list.append(
                        [geo_base_points[p][3],
                         geo_base_points[v][3]])
                else:
                    match_list.append([geo_base_points[p][3],
                                       geo_base_points[v][3]])
                break

    return match_list


def bisect_list(list_point, axis_value, tolerance):
    """

    Args:
        list_point:
        axis_value:
        tolerance:

    Returns:

    """
    range_list = []
    min_value = axis_value - tolerance
    max_value = axis_value + tolerance
    range_list.append(bisect.bisect_left(list_point, min_value))
    range_list.append(bisect.bisect_left(list_point, max_value))

    return range_list


def mirror_plane_return(mirror_plane, mode='nAxis'):
    if mirror_plane == 'ZY' or mirror_plane == 'YZ':
        axis = 0
        n_axis = (-1.0, 1.0, 1.0)
        z_axis = (0, 1.0, 1.0)
    elif mirror_plane == 'ZX' or mirror_plane == 'XZ':
        axis = 1
        n_axis = (1.0, -1.0, 1.0)
        z_axis = (1.0, 0, 1.0)
    elif mirror_plane == 'XY' or mirror_plane == 'YX':
        axis = 2
        n_axis = (1.0, 1.0, -1.0)
        z_axis = (1.0, 1.0, 0)
    else:
        return

    if mode == 'nAxis':
        return n_axis
    elif mode == 'axis':
        return axis
    elif mode == 'zAxis':
        return z_axis


def is_mirror_py(point_a, point_b, mirror_plane, tolerance):
    """
    Check if point a is mirror target of point b against given mirror plane
    Args:
        point_a(list or tuple):
        point_b(list or tuple):
        mirror_plane(str):  'ZY' or 'ZX' or 'XY'
        tolerance(float):

    Returns:

    """
    n_axis = mirror_plane_return(mirror_plane, mode='nAxis')
    mirror_a = (n_axis[0] * point_a[0], n_axis[1] * point_a[1], n_axis[2] * point_a[2])
    for i in range(3):
        if abs(mirror_a[i] - point_b[i]) > tolerance:
            return False

    return True


def unflatten_list(string_list):
    compile_exp = re.compile(r'\d+')
    range_vtx_sublists = []

    for u in string_list:
        range_vtx = list(compile_exp.findall(u.split('.')[-1]))
        range_vtx_sublists.append(range_vtx)

    index_sort = []
    for u in range_vtx_sublists:
        # If sublist have more than 1 item, ex: vtx[97:108]
        if len(u) > 1:
            idx_list = list(range(int(u[0]), int(u[1]))) + [int(u[1])]
            for i in idx_list:
                index_sort.append(int(i))
        else:
            index_sort.append(int(u[0]))

    return index_sort


def index_point_to_delta_data(point_index_list):
    """
    Split merged point and index data into two lists
    Args:
        point_index_list(list): A list of point + index [x, y, z, index]

    Returns:
        tuple: Point list and component index list

    """
    point_data = []
    component_data = []
    lambda_func = lambda c: c[-1]
    point_index_list.sort(key=lambda_func)

    for dm in point_index_list:
        point_data.append((dm[0], dm[1], dm[2], 1.0))
        # Pattern for the component Array
        component_data.append('vtx[{}]'.format(dm[3]))
    return point_data, component_data


def combine_point_index(blend_shape_node, index, in_between):
    """

    Args:
        blend_shape_node(str): The name of blend shape
        index(int): The index of target
        in_between(int): The in between index. Usually the value is between 5000 - 6000

    Returns:
        list: A list of [x, y, z, index]

    """
    bs_node = Node(blend_shape_node)
    item_attr = bs_node.inputTarget[0].inputTargetGroup[index].inputTargetItem[in_between]
    point_data = item_attr.inputPointsTarget.value
    component_data = item_attr.inputComponentsTarget.value

    component_data = unflatten_list(component_data)
    point_index = []

    for p, idx in zip(point_data, component_data):
        point_index.append((p[0], p[1], p[2], idx))

    return point_index


def mirror_point_index(point, idx, n_axis):
    """
    Mirror point index based on a axis values
    Args:
        point:
        idx:
        n_axis:

    Returns:

    """
    if n_axis:
        m_p_index = ((point[0] * n_axis[0],
                      point[1] * n_axis[1],
                      point[2] * n_axis[2],
                      idx))
    else:
        m_p_index = (point[0], point[1], point[2], idx)
    return m_p_index
