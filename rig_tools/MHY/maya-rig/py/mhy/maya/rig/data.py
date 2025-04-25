"""
Rig data export/import utilities.
"""

import os
import json
import six
import math
from collections import OrderedDict

from mhy.maya.rig.node.marker import ATTR_IS_LEAF, ATTR_ROT_TYPE

from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
from mhy.maya.utils import undoable
import mhy.maya.nodezoo.utils as nutil
from mhy.maya.nodezoo.constant import SurfaceAssociation

import mhy.maya.rig.marker_system as ms
import mhy.maya.rig.node.export_set as es
import mhy.maya.rig.utils as utils
import mhy.maya.rig.constants as const

import mhy.maya.rigtools.pose_editor.api.pose_controller as pc

# TODO(tye): Need to move api dependencies to back end repo
import mhy.maya.animtools.picker_manager.api.pickers as picker_api

# TODO: import_constrain_data


_MS_VERSION = 0.1
_EXT_DEFORMER_UNCOMP = 'nzd'
_EXT_DEFORMER_COMP = 'gnzd'
_EXT_POSE = 'mhy'
_EXT_PICKER = 'lpk'
_MARKER_ATTR_BLACKLIST = (
    'lockInfluenceWeights',
    'attributeAliasList',
    ATTR_IS_LEAF,
    ATTR_ROT_TYPE)


# --- helpers
def _validate_export_path(data_name, data_file, ext='json'):
    """Validates an exprot path and create dirs if necessary.

    Args:
        data_name (str): The name of this data format.
        data_file (str): A data file path to validate.
        ext (str or list): The expected file extension(s).

    Returns:
        bool: The validation status.
    """
    if not isinstance(ext, (list, tuple)):
        ext = [ext]

    status = True
    if not data_file:
        cmds.warning('Empty {} data file provided.'.format(data_name))
        status = False
    else:
        found = False
        for e in ext:
            if data_file.endswith('.{}'.format(e)):
                found = True
                break
        if not found:
            cmds.warning(
                '{} data file is not {}: {}'.format(
                    data_name.capitalize(), ext, data_file))
            status = False

    # create directories if necessary
    if status:
        fdir = os.path.dirname(data_file)
        if not os.path.isdir(fdir):
            os.makedirs(fdir)

    return status


def _validate_import_path(data_name, data_file, ext='json'):
    """Validates an import path.

    Args:
        data_name (str): The name of this data format.
        data_file (str): A data file path to validate.
        ext (str or List): The expected file extension(s).

    Returns:
        bool: The validation status.
    """
    status = _validate_export_path(data_name, data_file, ext=ext)
    if status:
        if not os.path.isfile(data_file):
            cmds.warning(
                '{} data file doesn\'t exist: {}'.format(
                    data_name.capitalize(), data_file))
            status = False
    return status


# --- marker data

def _iter_marker_nodes():
    """Iterates over all marker nodes in the scene in hierarchy order."""
    for root in cmds.ls('*_' + const.EXT_MARKER_ROOT, type='transform') or []:
        marker_sys = ms.MarkerSystem(root)
        up_ctrls = set()
        for node in marker_sys.iter_markers(plane_marker_last=True):
            yield node
            up_ctrl = node.up_ctrl
            if up_ctrl and up_ctrl not in up_ctrls:
                yield up_ctrl


def _get_marker_node_data(node):
    """Returns a dict containing serialized data for a given node."""
    data = {}
    if node.tx.is_free_to_change:
        data['matrix'] = node.get_matrix(space='world')
    for attr in [node.v] + node.list_attr(userDefined=True):
        if attr.name in _MARKER_ATTR_BLACKLIST or \
           not attr.is_free_to_change or\
           attr.is_child or \
           attr.value is None:
            continue
        data[attr.name] = attr.value
    if NodeName.is_valid(node) and \
       NodeName(node).ext == const.EXT_MARKER_ROOT:
        marker_sys = ms.MarkerSystem(node)
        parent = marker_sys.get_parent_marker()
        if parent:
            data['parent_marker'] = parent.name
            data['connect_mode'] = marker_sys.get_marker_connect_mode()
    return data


def _set_marker_node_data(node, data):
    """Applies a dict data onto a given node."""
    node = Node(node)
    for key, val in data.items():
        if key in _MARKER_ATTR_BLACKLIST:
            continue
        if key == 'matrix':
            node.set_matrix(val, space='world')
        elif key == 'parent_marker' and val:
            if cmds.objExists(val):
                # backward compatibility
                if 'follow' in data:
                    mode = 'follow' if data['follow'] else 'none'
                else:
                    mode = data.get('connect_mode', 'none')
                ms.MarkerSystem(node).set_parent_marker(val, mode=mode)
        elif key == 'connect_mode' or key == 'follow':
            continue
        elif node.has_attr(key):
            attr = node.attr(key)
            if attr.is_free_to_change:
                attr.value = val


def export_marker_data(data_file):
    """Serializes all markers in the scene and export
    it to a JSON file.

    Args:
        data_file (path): A JSON file to write the marker data.

    Returns:
        None
    """
    if not cmds.objExists(const.MARKER_ROOT):
        cmds.warning('Marker not found!')
        return

    # construct data dict
    data = OrderedDict()
    data['header'] = OrderedDict()
    data['header']['version'] = _MS_VERSION
    data['header']['colored'] = ms._is_line_colored()
    data['hier_nodes'] = OrderedDict()
    data['markers'] = OrderedDict()

    # gather hierarchy nodes
    hier_nodes = cmds.ls('*_{}'.format(const.EXT_MARKER_ROOT), long=True) or []
    hier_nodes += cmds.ls(
        '*_{}'.format(const.EXT_MARKER_HIER_CTRL), long=True) or []
    hier_nodes.sort()
    if cmds.objExists(const.MARKER_ROOT):
        hier_nodes.insert(0, const.MARKER_ROOT)

    # serialize nodes
    for node in hier_nodes:
        node = Node(node)
        data['hier_nodes'][node.name] = _get_marker_node_data(node)
    for node in _iter_marker_nodes():
        data['markers'][node.name] = _get_marker_node_data(node)

    # dump data
    if data:
        if not _validate_export_path('Marker', data_file):
            return
        with open(data_file, 'w+') as f:
            json.dump(data, f, indent=2)
        OpenMaya.MGlobal.displayInfo(
            'Exproted marker data to: {}'.format(data_file))
    else:
        cmds.warning('No markers found.')


@undoable
def import_marker_data(data_file):
    """Reads marker data from a JSON file and applies it to
    existing markers in the scene.

    Args:
        data_file (path): Path to a marker data JSON file.

    Returns:
        None

    Raises:
        ValueError: If the input path is not a JSON file.
    """
    # load data
    if not _validate_import_path('Marker', data_file):
        return
    data = {}
    with open(data_file, 'r') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    if not data:
        return

    # check compatibility
    if math.floor(data['header']['version']) < math.floor(_MS_VERSION):
        raise ValueError('Marker data not compatible.')

    missing_nodes = []
    processed_nodes = set()

    # apply node data
    for node, ndata in data['hier_nodes'].items():
        if not cmds.objExists(node):
            missing_nodes.append(node)
            continue
        _set_marker_node_data(node, ndata)
        processed_nodes.add(node)

    for node, ndata in data['markers'].items():
        if not cmds.objExists(node):
            missing_nodes.append(node)
            continue
        if node in processed_nodes:
            continue
        _set_marker_node_data(node, ndata)

    colored = data['header'].get('colored', False)
    if ms._is_line_colored() != colored:
        ms._toggle_line_colored()

    if missing_nodes:
        cmds.warning(
            'Marker nodes not found: {}'.format(', '.join(missing_nodes)))
    else:
        OpenMaya.MGlobal.displayInfo(
            'Imported marker data from: {}'.format(data_file))


# --- ctrl shape data


def export_ctrl_data(data_file):
    """Serializes ctrls in the scene and save the data
    in the specifed JSON file.

    Args:
        data_file (str): A JSON file path to export ctrl data to.

    Returns:
        None

    Raises:
        ValueError: If data_file is empty or not a JSON file.
    """
    # find the marker root, so that we can exclude all marker nodes.
    marker_root = None
    if cmds.objExists(const.MARKER_ROOT):
        marker_root = Node(const.MARKER_ROOT)

    # gather ctrl data
    data = {}
    for shape in cmds.ls(type='mhyController') or []:
        shape = Node(shape)
        ctrl = shape.get_parent()
        if marker_root:
            if ctrl == marker_root or ctrl.is_child_of(marker_root):
                continue

        data[ctrl.name] = {}
        for attr in shape.list_attr(channelBox=True):
            if not attr.is_compound and not attr.name.startswith('face'):
                val = attr.value
                if val is None:
                    continue
                data[ctrl.name][attr.name] = attr.value

    if data:
        if not _validate_export_path('Ctrl', data_file):
            return
        with open(data_file, 'w+') as f:
            json.dump(data, f, indent=2)
        OpenMaya.MGlobal.displayInfo(
            'Exproted ctrl data to: {}'.format(data_file))
    else:
        cmds.warning('No ctrls found.')


@undoable
def import_ctrl_data(data_file):
    """loads ctrl shape data from the given JSON file.

    Args:
        data_file (str): A JSON file path to import ctrl data from.

    Returns:
        None
    """
    # read data
    if not _validate_import_path('Ctrl', data_file):
        return
    data = {}
    with open(data_file, 'r') as f:
        data = json.load(f)

    missing_ctrls = []
    # apply data to ctrls in the scene
    for ctrl_name, ctrl_data in data.items():
        if not cmds.objExists(ctrl_name):
            missing_ctrls.append(ctrl_name)
            continue

        ctrl = Node(ctrl_name)
        shape = ctrl.get_shapes(type_='mhyController')
        if not shape:
            continue
        shape = shape[0]

        for key, val in ctrl_data.items():
            if shape.has_attr(key):
                try:
                    shape.attr(key).value = val
                except Exception:
                    cmds.warning("Failed to set value for {}".format(shape.attr(key).name))

    if missing_ctrls:
        cmds.warning(
            'Ctrls not found: {}'.format(', '.join(missing_ctrls)))
    else:
        OpenMaya.MGlobal.displayInfo(
            'Improted ctrl data from: {}'.format(data_file))


# --- export set data


def export_set_data(data_file):
    """Serializes export sets in the scene and save the data
    in the specifed JSON file.

    Args:
        data_file (str): A JSON file path to export ctrl data to.

    Returns:
        None

    Raises:
        ValueError: If data_file is empty or not a JSON file.
    """
    data = {'export_sets': {}, 'parent_override': {}}

    for export_set in es.ExportSet.get_export_sets():
        members = []
        for node in export_set.iter_valid_members():
            members.append(str(node))
        if members:
            data['export_sets'][export_set.name] = members

    for node in es.nodes_with_parent_override():
        po = es.get_parent_override(node)
        data['parent_override'][str(node)] = str(po)

    if data['export_sets']:
        if not _validate_export_path('Export Set', data_file):
            return
        with open(data_file, 'w+') as f:
            json.dump(data, f, indent=2)
        OpenMaya.MGlobal.displayInfo(
            'Exproted set data to: {}'.format(data_file))
    else:
        cmds.warning('No export sets found.')


@undoable
def import_set_data(data_file):
    """loads export set data from the given JSON file.

    Args:
        data_file (str): A JSON file path to import export set data from.

    Returns:
        None
    """
    # read data
    if not _validate_import_path('Export Set', data_file):
        return
    data = {}
    with open(data_file, 'r') as f:
        data = json.load(f)

    if not data:
        cmds.warning('Export set file is empty.')
        return

    es.clear_scene()

    missing_nodes = set()
    for export_set, members in data.get('export_sets', {}).items():
        export_set = Node.create('MHYExportSet', name=export_set)
        for each in members:
            if cmds.objExists(each):
                export_set.add_member(each)
            else:
                missing_nodes.add(each)

    missing_parent_ovr = set()
    for node, po in data.get('parent_override', {}).items():
        if cmds.objExists(po):
            if cmds.objExists(node):
                es.set_parent_override(node, po)
        else:
            missing_parent_ovr.add(po)

    if missing_nodes:
        cmds.warning(
            'Export set members not found: {}'.format(', '.join(missing_nodes)))
    if missing_parent_ovr:
        cmds.warning(
            'Parent overrides not found: {}'.format(', '.join(missing_parent_ovr)))
    if not missing_nodes and not missing_parent_ovr:
        OpenMaya.MGlobal.displayInfo(
            'Improted export sets from: {}'.format(data_file))


# --- deformer data


def export_deformer_data(mesh, data_file, uncompressed=False, compressed=True):
    """Exports deformer data to a given file.

    Only supports skinCluster and custer for now.

    Args:
        mesh (str or Node): A mesh to export deformers from.
        data_file (str): Path to a weights file.
        uncompressed (bool): If True, export an uncompressed data file.
        compressed (bool): If True, export an compressed data file.

    Returns:
        bool: True if the export was successful.
    """
    if not compressed and not uncompressed:
        cmds.warning('Need to export something...')
        return False

    if not cmds.objExists(mesh):
        cmds.warning('Mesh not found: {}'.format(mesh))
        return False

    fdir = os.path.dirname(data_file)
    if not os.path.isdir(fdir):
        os.makedirs(fdir)

    data_file, _ = os.path.splitext(data_file)

    # get mesh
    mesh = Node(mesh)
    mesh = mesh.get_shapes()
    if not mesh:
        cmds.warning('No mesh under {}'.format(mesh))
        return False
    mesh = mesh[0]

    # get and validate deformers
    deformers = mesh.get_deformers(type_=['cluster', 'skinCluster'])
    if not deformers:
        return False
    for dfm in deformers:
        if dfm.type_name == 'skinCluster' and \
           not cmds.skinCluster(dfm, query=True, influence=True):
            cmds.warning('SkinCluster has no influence: ' + mesh)
            return False

    if uncompressed:
        p = '{}.{}'.format(data_file, _EXT_DEFORMER_UNCOMP)
        nutil.export_node_data(deformers, p, compress=False)
    if compressed:
        p = '{}.{}'.format(data_file, _EXT_DEFORMER_COMP)
        nutil.export_node_data(deformers, p, compress=True)
    return True


def import_deformer_data(
        data_file, method=SurfaceAssociation.vertex_id, clean_up=True):
    """Loads deformer weights data from a given data file.

    # TODO hook up method kwarg.

    Args:
        data_file (str): Path to a weights file.
        method (SurfaceAssociation): The import surface association method.
        clean_up (bool): If True, clean up the imported deformer.
            Currently ONLY works for clusters.

    Returns:
        Node: The deformer node.
    """
    if not _validate_import_path(
            'Deformer', data_file,
            ext=(_EXT_DEFORMER_COMP, _EXT_DEFORMER_UNCOMP)):
        return
    for node in nutil.import_node_data(data_file, surface_association=method):
        if clean_up and hasattr(node, 'clean_up'):
            node.clean_up()
    OpenMaya.MGlobal.displayInfo(
        'Imported deformers from {}'.format(data_file))


def export_rig_deformer_data(data_path, uncompressed=False, compressed=True):
    """Exports all rig mesh weight files into a data dir.

    Args:
        uncompressed (bool): If True, export an uncompressed data file.
        compressed (bool): If True, export an compressed data file.

    Returns:
        None
    """
    roots = cmds.ls(const.RIGMESH_ROOT) or []
    roots += cmds.ls('*_' + const.WS_NODE) or []

    processed = set()
    for root in roots:
        for each in cmds.listRelatives(
                root, allDescendents=True, type='mesh') or []:
            each = Node(each)
            xform = each.get_parent()
            if xform not in processed:
                data_file = os.path.join(
                    data_path, xform.name + '.' + _EXT_DEFORMER_COMP)
                export_deformer_data(
                    xform, data_file,
                    uncompressed=uncompressed, compressed=compressed)
                processed.add(xform)


@undoable
def import_rig_deformer_data(
        data_path, method=SurfaceAssociation.vertex_id, clean_up=True):
    """Imports rig mesh weight files in a data dir."""
    if not data_path or not os.path.isdir(data_path):
        cmds.warning('Deformer path not valid: {}'.format(data_path))
        return

    processed = set()
    for each in os.listdir(data_path):

        comp = None
        uncomp = None
        if each.endswith(_EXT_DEFORMER_COMP):
            comp = os.path.join(data_path, each)
            head, _ = os.path.splitext(each)
            uncomp = os.path.join(data_path, head + '.' + _EXT_DEFORMER_UNCOMP)
            if not os.path.isfile(uncomp):
                uncomp = None
        elif each.endswith(_EXT_DEFORMER_UNCOMP):
            uncomp = os.path.join(data_path, each)
            head, _ = os.path.splitext(each)
            comp = os.path.join(data_path, head + '.' + _EXT_DEFORMER_COMP)
            if not os.path.isfile(comp):
                comp = None
        if not comp and not uncomp:
            continue

        if comp and uncomp:
            if os.path.getmtime(uncomp) > os.path.getmtime(comp):
                resolved_path = uncomp
            else:
                resolved_path = comp
        elif comp:
            resolved_path = comp
        else:
            resolved_path = uncomp

        if resolved_path not in processed:
            import_deformer_data(resolved_path, method=method, clean_up=clean_up)
            processed.add(resolved_path)


# --- connection data


@undoable
def import_connection_data(data_file, methods=None):
    """Loads connection data from a json file and apply it
    to the scene.

    Args:
        data_file (str): Path to a connection json file.
        methods (None or list): A list of connection methods to include.
            If None, include all methods stored in the json file.

    Returns:
        None
    """
    # read data
    if not _validate_import_path('Connection', data_file):
        return
    data = {}
    with open(data_file) as f:
        data = json.load(f)
    if not methods:
        methods = data.keys()

    # apply data
    for method, connection_data in data.items():
        '''
        if method not in methods:
            continue
        '''
        if  method=='setDrivenKey':

            sdk_data = connection_data
            for data in sdk_data:
                driver = data['driver']
                attr = data['attr']
                driver_attr = Node(driver).attr(attr)
                
                driven_data = data['driven_data']
                drivens = driven_data['nodes']
                dvn_attrs = driven_data['attrs']
                key_pairs = list(zip(data['keys'], driven_data['keys']))
                
                for driven in drivens:
                    for dvn_attr in dvn_attrs:
                        driven_attr = Node(driven).attr(dvn_attr)
                        utils.set_driven_keys(
                            driver_attr, driven_attr,
                            value_pairs=key_pairs,
                            in_tangent_type='linear',
                            out_tangent_type='linear'
                            )
        
        
        elif method=='directConnect':

            conn_data = connection_data
            for data in conn_data:
                driver = data['driver']
                driven = data['driven']
                attrs = data['attrs']
                hide_channels = data['lock_hide']
                
                if isinstance(driver, list):
                    for attr in attrs:
                        driver_attrs=[]
                        driven_attr = '{}.{}'.format(driven, attr)
                        for node in driver:
                            driver_attrs.append('{}.{}'.format(node, attr))
                            
                        node_name = NodeName(driver[0])
                        sum_name = NodeName(
                            driver[0],
                            part = node_name.desc,
                            desc = '{}Sum'.format(attr),
                            num = node_name.num,
                            side = node_name.side,
                            ext = 'pma'
                            )
                        utils.create_sum(
                            input_attrs = driver_attrs,
                            output_attr = driven_attr,
                            dimension = 3,
                            name= sum_name
                            )

                elif isinstance(driver, str):
                    try:
                        utils.xform_connect(driver, driven, attrs=attrs, lock=False)
                        if hide_channels:
                            driven_node = Node(driven)
                        driven_node.lock(attrs='trsv')

                    except BaseException:
                        cmds.warning(
                            '{} cannot be connected to {}'.format(driven, driver))
                            
                else:
                    cmds.warning('{} type incorrect.'.format(driver))
        
        # TODO:  Need specific method for constraint connection
        else:
            for driver, driven in connection_data:
                if method=='parent':
                    try:
                        cmds.parent(driven, driver)
                    except BaseException:
                        cmds.warning(
                            '{} cannot be parented to {}'.format(driven, driver))
                
                elif method == 'parentConstraint':
                    try:
                        cmds.parentConstraint(driver, driven, maintainOffset=True)
                    except BaseException:
                        cmds.warning(
                            '{} cannot be constraint to {}'.format(driven, driver))
                
                elif method == 'pointConstraint':
                    try:
                        cmds.pointConstraint(driver, driven, maintainOffset=True)
                    except BaseException:
                        cmds.warning(
                            '{} cannot be constraint to {}'.format(driven, driver))
                                   
                elif method == 'orientConstraint':
                    try:
                        cmds.orientConstraint(driver, driven, maintainOffset=True)
                    except BaseException:
                        cmds.warning(
                            '{} cannot be constraint to {}'.format(driven, driver))
                
                else: 
                    cmds.warning(
                        ('Connection method {} not available. '
                         'Skipped connecting {} to {}.').format(method, driven, driver))
                    continue
                    
    OpenMaya.MGlobal.displayInfo(
        'Imported ctrl data from: {}'.format(data_file))


# --- pose data

@undoable
def import_pose_data(path, is_anim_rig=False):
    """
    Import pose data to this scene.
    Args:
        path(str): The path to data file
        is_anim_rig(bool): If building anim rig so all the connections will be
        set on FKPOSE node instead of FKCTRL
    Return:
        list: created pose controller nodes
    """
    def update_influence_key(key):
        orig_name = NodeName(key)
        pose_grp_name = orig_name.replace_ext('FKPOSE')
        if orig_name.ext == 'TRACER':
            pose_grp_name = orig_name
        if Node.object_exist(pose_grp_name):
            return pose_grp_name
        return orig_name

    if not os.path.isdir(path):
        OpenMaya.MGlobal.displayWarning('{} is not a valid path to pose data'.format(path))
        return []
    created_controllers = []
    for each in os.listdir(path):
        if each.endswith(_EXT_POSE):
            data_file = os.path.join(path, each)
            if is_anim_rig:
                with open(data_file, 'r') as f:
                    data_file = json.load(f)
                    if isinstance(data_file, dict):
                        data_file = [data_file]
                    for d in data_file:
                        pose_data_dict = d.get('pose')
                        for pose_name, pose_data in pose_data_dict.items():
                            inf_data = pose_data.get('influence', None)
                            if inf_data:
                                pose_data['influence'] = {update_influence_key(k): v
                                                          for k, v in inf_data.items()}
                                                          
            controllers = pc.PoseController.load(data_file)
            
            if controllers:
                created_controllers.extend(controllers)
    return created_controllers

# --- picker data


@undoable
def import_picker_data(path):
    """
    Import picker data to this scene.
    Args:
        path(str): The path to data file
    Return:
        bool: If succeed
    """
    if not os.path.isdir(path):
        OpenMaya.MGlobal.displayWarning('{} is not a valid path to picker data'.format(path))
        return False
    for each in os.listdir(path):
        if each.endswith(_EXT_PICKER):
            data_file = os.path.join(path, each)
            picker_api.load_data_from_file(data_file)
    return True


def export_texture_shader_data(node_name, path=None):
    """
    Export the texture shader data from a node to a path if a file path is given.

    Args:
        node_name(str):
        path(str):

    Returns:
        dict: Data in dictionary format

    """
    def get_workspace_relative_path(workspace_root, path):
        if path.startswith(workspace_root):
            path = path.replace(workspace_root, '', 1)
        return path

    data = {}
    if not Node.object_exist(node_name):
        OpenMaya.MGlobal.displayError('{} doesn not exist'.format(node_name))
        return data
    shader = Node(node_name)
    work_space_root = cmds.workspace(query=True, rootDirectory=True)
    shader_path = shader.shader.value
    shader_path = get_workspace_relative_path(work_space_root, shader_path)

    attributes_to_export = [
        'Diffuse', 'Diffuse01', 'Diffuse02', 'Diffuse03', 'BaseNormal', 'WrinkleNormal01',
        'WrinkleNormal02', 'WrinkleNormal03', 'MicroNormal', 'wm1_msk_01', 'wm1_msk_02',
        'wm1_msk_03', 'wm1_msk_04', 'wm13_msk_03', 'wm2_msk_01', 'wm2_msk_02',
        'wm2_msk_03', 'wm3_msk_01', 'wm3_msk_02', 'Cavity_Map', 'SSAO_Mask', 'Roughness_Mask']

    map_data = {}

    for attr in attributes_to_export:
        attr_inst = shader.attr(attr)
        if not attr_inst:
            continue
        source_node = attr_inst.source_node
        source = ""
        if source_node and source_node.type_name == 'file':
            source = source_node.fileTextureName.value
            source = get_workspace_relative_path(work_space_root, source)
        map_data[attr] = source

    data['shader_file'] = shader_path
    data['map_path'] = map_data
    # dump data
    if path:
        if not _validate_export_path('shader', path):
            return
        with open(path, 'w+') as f:
            json.dump(data, f, indent=2)
        OpenMaya.MGlobal.displayInfo(
            'Exproted shader data to: {}'.format(path))
    else:
        cmds.warning('No markers found.')

    return data


def import_texture_shader_data(shader_node, data):
    """
    Import texture shader data to a given shader node
    Args:
        shader_node(str):
        data(dict or str): Could be dictionary data or file path

    """
    if isinstance(data, six.string_types):
        result = _validate_import_path('Texture Shader', data)
        if not result:
            return
        with open(data, 'r') as f:
            data = json.load(f)

    shader_path = data.get('shader_file')
    if not shader_path:
        return

    shader_node = Node(shader_node)
    shader_node.shader.value = shader_path

    map_path_data = data.get('map_path')
    for attr, val in map_path_data.items():
        attr_inst = shader_node.attr(attr)
        if not attr_inst:
            continue
        file_node = Node.create('file')
        file_node.outColor.connect(attr_inst, force=True)
        file_node.fileTextureName.value = val


def import_shader_data(data_file):
    """
    """
    # read data
    if not _validate_import_path('Shader Data', data_file):
        return
    data = {}
    with open(data_file) as f:
        data = json.load(f)
        
    # apply data
    for shd_grp, shd_data in data.items():
        mesh = shd_data['mesh']
        cmds.sets(mesh, e=True, forceElement=shd_grp)


def import_attrs_data(data_file):
    """
    """
    # read data
    if not _validate_import_path('Attributes', data_file):
        return
    data = {}
    with open(data_file) as f:
        data = json.load(f)
        
    # apply data
    for node, attr_data in data.items():
        for value_data in attr_data:
            attr = value_data['attr']
            value = value_data['value']
            
            node_attr = Node(node).attr(attr)
            node_attr.value = value
            
            try:
                lock = value_data['lock']
                node_attr.locked = lock
            except:
                continue


def import_bs_target_driver_data(data_file):
    """
    """
    # read data
    if not _validate_import_path('Blend Shape Target Driver Data', data_file):
        return
    data = {}
    with open(data_file) as f:
        data = json.load(f)
        
    # apply data
    target_shapes = []
    for bs, data_ls in data.items():
        bs_node = Node(bs)
        for attr_data in data_ls:
            target = attr_data['target']
            if not cmds.nodeType(target)=='mesh':
                target = Node(target).get_shapes()[-1]
                
            driver = attr_data['driver']
            channel = attr_data['channel']
            driver_attr = '{}.{}'.format(driver, channel)
            val01, val02 = attr_data['value']
                
            # add to bs
            bs_attr = bs_node.add_target(target)
            
            # set driver sdk
            if driver:
                driving_data = [
                    (val01, 0.0), (val02, 1.0)
                ]
                utils.set_driven_keys(
                    driver_attr, bs_attr,
                    driving_data,
                    pre_inf='constant',
                    post_inf='constant'
                )
            #
            target_shapes.append(target)
            
    return target_shapes

       

def import_layer_data(data):
    """
    """
    
    pass
    