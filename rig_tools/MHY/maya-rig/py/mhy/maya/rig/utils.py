"""
Rigging utility functions.
"""

import json
import six

from maya import cmds, OpenMaya

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.node.transform import resolve_xform_attr_string
import mhy.maya.rig.constants as const


# --- rig root groups


ATTR_HIDE_ON_PLAY = 'hide_ctrls_on_playback'


def get_or_create_rig_root():
    """Returns the rig root node. Create one if not exists."""
    if not cmds.objExists(const.RIG_ROOT):
        return Node.create('transform', name=const.RIG_ROOT)
    return Node(const.RIG_ROOT)


def get_or_create_ws_node():
    """Returns the worldspace node. Create one if not exists."""
    if not cmds.objExists(const.WS_NODE):
        node = Node.create(
            'transform', name=const.WS_NODE, parent=get_or_create_rig_root())
        node.inheritsTransform.value = False
        node.inheritsTransform.locked = True
        node.lock(attrs='trs')
        return node
    return Node(const.WS_NODE)


def get_or_create_rig_skel_root():
    """Returns the skeleton root node. Create one if not exists."""
    if not cmds.objExists(const.RIG_SKEL_ROOT):
        node = Node.create(
            'transform',
            name=const.RIG_SKEL_ROOT,
            parent=get_or_create_rig_root())
        node.lock(attrs='trs')
        return node
    return Node(const.RIG_SKEL_ROOT)


def get_or_create_bind_skel_root():
    """Returns the skeleton root node. Create one if not exists."""
    if not cmds.objExists(const.BIND_SKEL_ROOT):
        node = Node.create(
            'transform',
            name=const.BIND_SKEL_ROOT,
            parent=get_or_create_rig_root())
        node.lock(attrs='trs')
        return node
    return Node(const.BIND_SKEL_ROOT)


def get_or_create_limb_root():
    """Returns the limb root node. Create one if not exists."""
    if not cmds.objExists(const.LIMB_ROOT):
        node = Node.create(
            'transform', name=const.LIMB_ROOT, parent=get_or_create_rig_root())
        node.lock(attrs='trs')
        return node
    return Node(const.LIMB_ROOT)


def get_or_create_mesh_root():
    """Returns the mesh root node. Create one if not exists."""
    if not cmds.objExists(const.RIGMESH_ROOT):
        node = Node.create(
            'transform', name=const.RIGMESH_ROOT,
            parent=get_or_create_ws_node())
        node.lock(attrs='trs')
        return node
    return Node(const.RIGMESH_ROOT)
    
def get_or_create_metahuman_root():
    """Returns the metahuman root node. Create one if not exists."""
    if not cmds.objExists(const.MH_ROOT):
        node = Node.create(
            'transform', name=const.MH_ROOT,
            parent=get_or_create_ws_node())
        node.lock(attrs='trs')
        return node
    return Node(const.MH_ROOT)


def init_rig_root_groups():
    """Initializes rig root groups."""
    rig_root = get_or_create_rig_root()
    get_or_create_ws_node()
    rig_skel_root = get_or_create_rig_skel_root()
    rig_skel_root.v.value = False
    bind_skel_root = get_or_create_bind_skel_root()
    limb_root = get_or_create_limb_root()
    get_or_create_mesh_root()
    get_or_create_metahuman_root()

    if not rig_root.has_separator_attr('vis'):
        rig_root.add_separator_attr('vis')

    # hid ctrl on playback attr
    if not rig_root.has_attr(ATTR_HIDE_ON_PLAY):
        attr = rig_root.add_attr(
            'bool', name=ATTR_HIDE_ON_PLAY, defaultValue=False)
        attr.channelBox = True
        attr >> limb_root.hideOnPlayback

    # skeleton vis attr
    for node, attr, dv in zip(
            [bind_skel_root],
            ['skeleton'],
            [False]):
        if rig_root.has_attr(attr):
            continue
        attr = rig_root.add_attr('bool', attr, defaultValue=dv)
        attr.channelBox = True
        attr >> node.v


# --- utility network setups


def create_sum(input_attrs, output_attr=None, dimension=1, name='sum'):
    """Creates a sum network with a plusMinusAverage node.

    Args:
        input_attrs (list): A list of input attributes to sum.
        output_attr (str): An output attribute to recieve the sumed value.
        name (str): Name of the plusMinusAverage node.

    Returns:
        Attribute: The output attribute object.
    """
    sum_node = Node.create('plusMinusAverage', name=name)
    for i, attr in enumerate(input_attrs):
        cmds.connectAttr(attr, '{}.input{}D[{}]'.format(sum_node, dimension, i))
    if output_attr:
        cmds.connectAttr('{}.output{}D'.format(sum_node, dimension), output_attr, force=True)
    return sum_node.attr('output{}D'.format(dimension))


def xform_connect(
        driver, driven, attrs='all', extra_attrs=None,
        inverse=False, lock=True):
    """Connects attributes between a driver node and a driven node.

    Args:
        driver (str): The driver node.
        driven (str): The driven node.
        attrs (str): A string combination of transform channels to connect.
            Supported channels are: t, r, s,
            tx, ty, tz, rx, ry, rz, sx, sy, sz.
            If "all", include all channels.
        extra_attrs (list): A list of extra attributes to connect.
        inverse (bool): If True, inverse the value then connect.
        lock (bool): If True, connected attrs on the driven
            node are locked and hidden.

    Returns: None

    Raises:
        RuntimeError: If an attribute does not exists or is not connectable.
    """
    # collect attributes
    attrs = resolve_xform_attr_string(attrs, skip_parent=True, skip_vis=True)
    if extra_attrs:
        if not isinstance(extra_attrs, (list, tuple)):
            attrs.append(extra_attrs)
        else:
            attrs += list(extra_attrs)

    if isinstance(driver, str):
        driver = Node(driver)
    if isinstance(driven, str):
        driven = Node(driven)

    for attr in attrs:
        driver_attr = driver.attr(attr)
        driven_attr = driven.attr(attr)

        if inverse:
            md = Node.create(
                'multDoubleLinear', n='{}_{}INVERSE'.format(driver.name, attr))
            driver.attr(attr) >> md.attr('input1')
            md.set_attr('input2', -1)
            md.attr('output') >> driven.attr(attr)
        else:
            driver_attr >> driven_attr

        if lock:
            driven_attr.keyable = False
            driven_attr.locked = True
            driven_attr.channelBox = False


def create_condition(termA_attr, termB_attr, true_attr, false_attr, operation):
    """Creates a condition network.

    Args:
        termA_attr (str or float): An attr or value to apply to the first term.
        termB_attr (str or float): An attr or value to apply to the second term.
        true_attr (str or float): An attr or value to apply to ifTrue result.
        false_attr (str or float): An attr or value to apply to ifFalse result.
        operation (int): The operation index.

    Returns:
        Attribute: The output attribute object.
    """
    # create the condition node
    name = str(termA_attr).split('|')[-1].replace('.', '_')
    name += '_' + str(termB_attr).split('|')[-1].replace('.', '_')
    name += '_' + str(operation) + '_cnd'
    cnd = Node.create('condition', name=name)
    cnd.set_attr('operation', operation)

    # connect/set terms
    for term, attr in zip(
            (termA_attr, termB_attr), ('firstTerm', 'secondTerm')):
        if isinstance(term, (int, float)):
            cnd.set_attr(attr, term)
        else:
            cmds.connectAttr(term, '{}.{}'.format(cnd, attr), force=True)

    # connect/set results
    for result, attr in zip(
            (true_attr, false_attr),
            ('colorIfTrueR', 'colorIfFalseR')):
        if isinstance(result, (int, float)):
            cnd.set_attr(attr, result)
        else:
            cmds.connectAttr(result, '{}.{}'.format(cnd, attr), force=True)

    return cnd.attr('outColorR')


def create_multiplier(
        driver_attr, driven_attr, multiplier, offset=0, reverse=False):
    """Creates a single-channel multiply network.

    Args:
        driver_attr (str): The driver attribute.
        driven_attr (str): The driven attribute.
        multiplier (float): A multiplier value.
        offset (float): A offset value to add to the final result.
        reverse (bool): If True, reverse the driver atter before
            mulitipling, then reverse it back.

    Returns:
        Attribute: The output attribute.
    """
    prefix = str(driven_attr).split('|')[-1].replace('.', '_')
    if reverse:
        rvsA = Node.create('reverse', name=prefix + '_scaleA_rvs')
        rvsB = Node.create('reverse', name=prefix + '_scaleB_rvs')
    mdl = Node.create('multDoubleLinear', name=prefix + '_mdl')

    if reverse:
        cmds.connectAttr(driver_attr, rvsA.inputX)
        rvsA.outputX >> mdl.input1
    else:
        cmds.connectAttr(driver_attr, mdl.input1)

    mdl.set_attr('input2', multiplier)

    if reverse:
        cmds.connectAttr(mdl.output, rvsB.inputX)
        out_attr = rvsB.outputX
    else:
        out_attr = mdl.output

    if offset != 0:
        adl = Node.create('addDoubleLinear', name=prefix + '_adl')
        cmds.connectAttr(out_attr, adl.input1)
        adl.input2.value = offset
        if driven_attr:
            cmds.connectAttr(adl.output, driven_attr, force=True)
        return adl.output
    elif driven_attr:
        cmds.connectAttr(out_attr, driven_attr, force=True)
        return out_attr


def create_negation(driver, driven, attrs='t'):
    """Creates a transform attribute negation network.

    Args:
        driver (str): The driver node.
        driven (str): The driven node.
        attrs (str): A string combination of transform channels to connect.
            Supported channels are: t, r, s,
            tx, ty, tz, rx, ry, rz, sx, sy, sz.
            If "all", include all channels.

    Returns: None
    """
    driver = Node(driver)
    driven = Node(driven)
    prefix = driver.name

    tmd = None
    smd = None

    for attr in resolve_xform_attr_string(
            attrs, skip_parent=True, skip_vis=True):
        ax = attr[-1].upper()

        if attr.startswith('t'):
            if not tmd:
                tmd = Node.create(
                    'multiplyDivide', name='{}_t_NEG'.format(prefix))
            driver.attr(attr) >> tmd.attr('input1' + ax)
            tmd.attr('input2' + ax).value = -1
            tmd.attr('output' + ax) >> driven.attr(attr)

        elif attr.startswith('r'):
            cv = Node.create(
                'unitConversion', name='{}_r_UNCVR'.format(prefix))
            driver.attr(attr) >> cv.attr('input')
            cv.conversionFactor.value = -1
            cv.attr('output') >> driven.attr(attr)

        elif attr.startswith('s'):
            if not smd:
                smd = Node.create(
                    'multiplyDivide', name='{}_s_NEG'.format(prefix))
                smd.operation.value = 2  # set to divide
            smd.set_attr('input1' + ax, 1)
            driver.attr(attr) >> smd.attr('input2' + ax)
            smd.attr('output' + ax) >> driven.attr(attr)


def create_curve_stretch_output(curve, as_ratio=True):
    """Returns an attribute that captures a curves stretch amount.

    Args:
        curve (str or Node): A curve node to work with.
        as_ratio (bool): If True, the output attr will be the stretch ratio.
            Otherwise it will be the stretch amount.

    Returns:
        Attribute: The stretch amount attribute.
    """
    # get the curve shape node
    crv = Node(curve)
    crv_shape = crv.get_shapes(type_='nurbsCurve')
    if crv_shape:
        crv_shape = crv_shape[0]
    else:
        raise ValueError('Invalid curve: {}'.format(curve))

    # create a curve info node
    ci = Node.create('curveInfo', name='{}Info'.format(crv_shape.name))
    crv_shape.worldSpace[0] >> ci.inputCurve
    orig_len = cmds.arclen(crv_shape)

    # create math nodes
    if as_ratio:
        mdl = Node.create('multDoubleLinear', name='{}_mdl'.format(crv_shape))
        ci.arcLength >> mdl.input1
        mdl.input2.value = 1.0 / orig_len
        return mdl.output
    else:
        adl = Node.create('addDoubleLinear', name='{}_adl'.format(crv_shape))
        ci.arcLength >> adl.input1
        adl.input2.value = -orig_len
        return adl.output


def create_stretchy_xforms(xforms, attrs='t'):
    """Given a list of flat transform nodes, set up a network to stretch
    the transforms by translating the first one.

    Args:
        xforms (list): A list of transform nodes to work with.
        attrs (str): A string combination of translate channels to connect.
            If "all", include all translate channels.

    Returns: None
    """
    if not isinstance(xforms, (list, tuple)) or len(xforms) < 3:
        raise ValueError('Need at lest 3 transforms.')
    xforms = [Node(x) for x in xforms]

    name = NodeName(xforms[0].name)
    dist = Node.create('distanceBetween', name=name.replace_ext('DIST'))
    xforms[0].worldMatrix[0] >> dist.inMatrix1
    xforms[-1].worldMatrix[0] >> dist.inMatrix2
    cur_dist = dist.distance.value

    mult_value = {}
    for xform in xforms[1:-1]:
        xform.worldMatrix[0] >> dist.inMatrix2
        mult_value[xform] = dist.distance.value / cur_dist
    cmds.delete(dist)

    for attr in resolve_xform_attr_string(attrs, skip_parent=True, skip_vis=True):
        if attr.startswith('t'):
            driver_attr = xforms[-1].attr(attr)
            for node, mult in mult_value.items():
                create_multiplier(driver_attr, node.attr(attr), mult)


def set_driven_keys(
        driver_attr, driven_attr, value_pairs,
        in_tangent_type='spline', out_tangent_type='spline',
        pre_inf='linear', post_inf='linear',
        insert_blend=False):
    """Creates a set driven key setup.

    Args:
        driver_attr (str): The driver attribute.
        driven_attr (str): The driven attribute.
        value_pairs (list): A list of pair values.
            e.g. ((driverVal01, drivenVal01), (driverVal02, drivenVal02))
        in_tangent_type, out_tangent_type, insert_blend:
            see cmds.setDrivenKeyframe()
        pre_inf, post_inf: see cmds.setInfinity()

    Returns:
        Node: The sdk node.
    """

    # create sdk
    for driver_value, driven_value in value_pairs:
        cmds.setDrivenKeyframe(
            driven_attr, currentDriver=driver_attr,
            driverValue=driver_value, value=driven_value,
            inTangentType=in_tangent_type, outTangentType=out_tangent_type,
            insertBlend=insert_blend)

    # set pre/post infinity
    if pre_inf:
        cmds.setInfinity(driven_attr, preInfinite=pre_inf)
    if post_inf:
        cmds.setInfinity(driven_attr, postInfinite=post_inf)

    node = cmds.listConnections(
        driven_attr, source=True, destination=False, plugs=False)[0]
        
    return Node(node)


def add_influence_tag_attribute(obj, driver_attributes=None):
    """
    Add the influence tag attribute. It's optional to set attribute filter and neutral value by
    setting driver_attributes arguments
    Args:
        obj:
        driver_attributes(dict or None): If specify attributes to be added as driven channels.

    Returns:
        str: The name of added attribute

    """
    if isinstance(obj, six.string_types) and not cmds.objExists(obj):
        OpenMaya.MGlobal.displayError("{} does not exists".format(obj))
        return
    obj = Node(obj)
    if not obj.has_attr(const.POSE_DRIVEN_ATTR):
        obj.add_attr('string', name=const.POSE_DRIVEN_ATTR)

    if driver_attributes:
        data_str = json.dumps(driver_attributes)
        obj.set_attr(const.POSE_DRIVEN_ATTR, data_str)
    return obj.attr(const.POSE_DRIVEN_ATTR).name


def writeElementList(data, filepath, sort=True, ind=4):
    ''' Simple method to export json '''
    with open(filepath, 'w') as outfile:
        outfile.write(json.dumps(data, sort_keys=sort, indent=ind))


def loadElementList(filepath):
    '''Simple method to load json'''
    with open(filepath) as outfile:
        result = json.load(outfile)
    return result
    
  
def convert_to_maya_path(path):
    """
    Convert backsashes in window path to forward slashes.
    Args:
        path: Any window path string.

    Returns:
        str: The path of converted string
        
    ** Important **
        Need to ddd letter r in front of the path string as input path

    """
    
    path_split = path.split('\\')
    return_path = '/'.join(path_split)
    
    return return_path
        

def unlock_poly_normal(mesh):
    """
    """    
    mesh = Node(mesh)
    if not mesh.is_shape:
        try:
            mesh = mesh.get_shapes(type_='mesh')[-1]
        except:
            raise ValueError('Need to input a mesh node.')

    cmds.polyNormalPerVertex(mesh, unFreezeNormal=True)
    cmds.polySoftEdge(mesh, angle=180)
    
    cmds.delete(mesh, constructionHistory=True)


def get_static_points(base_points, target_points):
    """Compare between two point array,
    remove the points not changing position.
    Args:
        base_points: points array from the base mesh.
        target_points: points array from the modified mesh.
    
    Returns: a list of point index numbers of the moved points.
    """
   
    static_pnts_id_ls = []
    for id, pnts_tuple in enumerate(zip(base_points, target_points)):
        try:
            dist = pow(sum([(a - b)*(a - b) for a, b in zip(pnts_tuple[0], pnts_tuple[1])]), 0.5)
            if not dist:
                static_pnts_id_ls.append(id)
        except:
            continue
    
    return static_pnts_id_ls
        

def get_deformed_points(deformed_obj, deformer_driver, driver_attr, attr_value):
    """
    """
    def_shape = deformed_obj
    if not cmds.nodeType(deformed_obj)=='mesh':
        try:
            def_shape = Node(deformed_obj).get_shapes()[-1]
        except:
            raise RuntimeWarning("{} is not a shape or geo transform node".format(deformed_obj))
            return None
    
    def_driver = Node(deformer_driver)
    def_driver_attr = def_driver.attr(driver_attr)
    
    orig_val = def_driver_attr.value
    orig_points = def_shape.get_points(space='object')
    def_driver_attr.value = attr_value
    def_points = def_shape.get_points(space='object')
    def_driver_attr.value = orig_val

    static_pnt_id_ls = get_static_points(orig_points, def_points)
    static_points = ['{}.vtx[{}]'.format(deformed_obj, id) for id in static_pnt_id_ls]
    
    return static_points
    
    
def prune_deformer_membership(static_points, deformer):
    """
    """
    def_set = cmds.listConnections(deformer, type='objectSet')
    if def_set:
        def_set = def_set[0]
    else:
        raise RuntimeWarning('{} does not have deformer sets'.format(deformer))
        return None
        
    cmds.sets(static_points, rm=def_set)
    return [deformer, def_set]
    
