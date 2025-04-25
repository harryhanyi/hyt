import maya.cmds
import maya.mel
import maya.OpenMaya as OpenMaya
import json
import gzip
from mhy.maya.nodezoo.node import Node
from mhy.python.core.compatible import gzip_export
import os
from six import string_types


SPACE_MAP = {
    'transform': OpenMaya.MSpace.kTransform,
    'preTransform': OpenMaya.MSpace.kPreTransform,
    'postTransform': OpenMaya.MSpace.kPostTransform,
    # 'object': OpenMaya.MSpace.kObject,
    'object': OpenMaya.MSpace.kTransform,
    'world': OpenMaya.MSpace.kWorld
}


def ls(*args, **kwargs):
    s = maya.cmds.ls(*args, **kwargs)
    return [Node(i) for i in s if '[' not in i]


def delete(nodes):
    maya.cmds.delete([node.name for node in nodes])


def read_data_file(file_path):
    """
    Query the dictionary information from a data file path
    Args:
        file_path(str):

    Returns:
        dict: Data

    """
    if file_path.endswith('.gnzd'):
        with gzip.open(file_path, 'r') as f:
            json_bytes = f.read()
        json_obj = json_bytes.decode('utf-8')
        data = json.loads(json_obj)
    else:
        with open(file_path) as f:
            data = json.load(f)
    return data


def get_space(space):
    """Returns the propery space value in OpenMaya.MSpace"""
    if not isinstance(space, int):
        space = SPACE_MAP.get(space)
        if space is None:
            raise NotImplementedError(
                ('space argument is not valid. '
                    '\nSupported spaces are: "preTransform", '
                    '"postTransform", "transform", "object", "world"'))
    return space


def inspect_data_file(file_path):
    """
    This is a convenient function to read data from a file_path
    Args:
        file_path(str): Path

    Returns:
        dict: data stored in the json file

    """
    file_path = file_path.replace('\\', '/')
    if not os.path.exists(file_path):
        OpenMaya.MGlobal.displayWarning("{} doesnt exist".format(file_path))
        return
    data = read_data_file(file_path)
    return data


def export_node_data_to_multiple_files(nodes, directory, compress=True,
                                       connection_data=True, creation_data=True,
                                       additional_data=True, ui=False, *args, **kwargs):
    """
    Export nodes to multiple disk files
    Args:
        nodes(list): A list of Nodes
        directory(str): A disk directory path the multiple files will be saved under
        compress(bool): If compress data before writing to the disk
        connection_data(bool): If export connection data
        creation_data(bool): If export creation data
        additional_data(bool): If export additional data
        ui(bool): If activate maya progress bar
        *args:
        **kwargs:


    """
    if compress:
        ext = ".nzd"
    else:
        ext = ".gnzd"
    g_main_progress_bar = None
    if ui:
        g_main_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar')
        maya.cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                              status="Exporting nodes ...", maxValue=len(nodes))
    try:
        for i in nodes:
            file_path = os.path.join(directory, i.name + ext)
            export_node_data([i], file_path, compress, connection_data, creation_data,
                             additional_data, ui=False, *args, **kwargs)
            if ui:
                maya.cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                      status="Exporting `{}`...".format(i.name))
    except Exception as e:
        OpenMaya.MGlobal.displayError(str(e))
    finally:
        if ui:
            maya.cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)


def export_node_data(nodes, file_path, compress=True, connection_data=True,
                     creation_data=True, additional_data=True,
                     ui=False, *args, **kwargs):
    """
    Export nodes to single disk files

    Args:
        nodes(list): A list of Nodes
        file_path(str): A disk file path
        compress(bool): If compress data before writing to the disk
        connection_data(bool): If export connection data
        creation_data(bool): If export creation data
        additional_data(bool): If export additional data
        ui(bool): If activate maya progress bar
        *args:
        **kwargs:

    Returns:

    """
    if not nodes:
        return
    if not isinstance(nodes, list):
        nodes = [nodes]

    data_list = []
    g_main_progress_bar = None
    if ui:
        g_main_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar')
        maya.cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                              status="Exporting nodes ...", maxValue=len(nodes) + 1)
    try:
        for i in nodes:
            i = Node(i)
            if g_main_progress_bar:
                maya.cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                      status="Exporting `{}`...".format(i.name))
            data = i.export(connection_data=connection_data, creation_data=creation_data,
                            additional_data=additional_data, *args, **kwargs)
            data_list.append(data)
        data_to_export = {'nodes': data_list}
        if g_main_progress_bar:
            maya.cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                  status="Writing file(s) to disk `{}`...")

        dir_name = os.path.dirname(file_path)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        if compress:
            json_obj = json.dumps(data_to_export)
            gzip_export(json_obj, file_path)
        else:
            json_obj = json.dumps(data_to_export, indent=4)

            with open(file_path, "w") as f:
                f.write(json_obj)
        OpenMaya.MGlobal.displayInfo("Exported data to: '{}'".format(file_path))
    except Exception as e:
        OpenMaya.MGlobal.displayError(str(e))
    finally:
        if ui:
            maya.cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)


def import_node_data(
        files,
        create_node=True,
        make_connections=True,
        name_map=None,
        namespace_map=None,
        ui=False,
        **kwargs):

    node_data_to_import = load_node_data_from_file(files)
    created_nodes = []
    num_nodes = len(node_data_to_import) or 1
    g_main_progress_bar = None
    if ui:
        g_main_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar')
        maya.cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                              status="Importing nodes ...", maxValue=num_nodes)
    try:
        for data in node_data_to_import:
            node_name = data.get('name', "")
            if g_main_progress_bar:
                maya.cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                      status="Importing `{}`...".format(node_name))
            node = Node.load_data(data,
                                  create_node=create_node,
                                  make_connections=make_connections,
                                  name_map=name_map,
                                  namespace_map=namespace_map,
                                  **kwargs)
            if node:
                created_nodes.append(node)
    except RuntimeError as e:
        OpenMaya.MGlobal.displayError(str(e))
    finally:
        if ui:
            maya.cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
    return created_nodes


def load_node_data_from_file(files):
    """
    Get the node data only from file(s).
    Args:
        files(list or str): One or multiple data files

    Returns:
        list: A list of data files

    """
    if isinstance(files, string_types):
        files = [files]
    all_node_datas = []
    for file_path in files:
        file_path = file_path.replace('\\', '/')
        if not os.path.exists(file_path):
            OpenMaya.MGlobal.displayWarning("{} doesnt exist".format(file_path))
            continue
        data = read_data_file(file_path)
        if not data:
            continue
        node_datas = data.get('nodes')
        if node_datas:
            for nodeData in node_datas:
                if not isinstance(nodeData, dict):
                    continue
                all_node_datas.append(nodeData)
    return all_node_datas


