import os
import json
import shutil
from PySide2 import QtWidgets

import subprocess
import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node
from mhy.python.core.utils import increment_name


env_var = "MHY_ANIM_POSE_ROOT"


def resolve_root_paths():
    default_path = os.path.expanduser('~/MHY_anim_poses/default')
    if not os.path.exists(default_path):
        os.makedirs(default_path)
    default_root = os.path.dirname(default_path)
    roots = [default_root]
    anim_root_env = os.environ.get(env_var)
    if anim_root_env:
        root_list = anim_root_env.split(';')
        for path in root_list:
            if os.path.isfile(path):
                # Read the path data from path file
                with open(path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    roots.extend(data)
            if os.path.isdir(path):
                roots.append(path)
    additional_paths = resolve_additional_root_paths()
    if additional_paths:
        roots.extend(additional_paths)
    roots = list(set(roots))
    return roots


def open_path(path):
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not os.path.exists(path):
        return
    path = path.replace('/', '\\')
    subprocess.Popen(r'explorer "{}"'.format(path))


def open_source_file(file_path):
    unsaved_check = cmds.file(q=True, modified=True)
    force = False
    if unsaved_check:
        dialog = QtWidgets.QMessageBox()
        dialog.setWindowTitle("Save Changes")
        cur_path = cmds.file(query=True, sceneName=True)
        dialog.setText('Save changes to {}'.format(cur_path))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel);

        result = dialog.exec_()
        if result == QtWidgets.QMessageBox.Yes:
            cmds.SaveScene()
        elif result == QtWidgets.QMessageBox.No:
            force = True
        elif result == QtWidgets.QMessageBox.Cancel:
            return
    cmds.file(file_path, open=True, force=force)


def real_path(path):
    """
    Return the given path eliminating any symbolic link.
    Args:
        path(str):

    Returns:

    """

    path = os.path.realpath(path)
    path = os.path.expanduser(path)
    return norm_path(path)


def norm_path(path):
    """
    Return a normalized path containing only forward slashes.
    Args:
        path(str):

    Returns:

    """

    # Check and support the UNC path structure
    unc = path.startswith("//") or path.startswith("\\\\")

    path = path.replace("//", "/")
    path = path.replace("\\", "/")

    if path.endswith("/") and not path.endswith(":/"):
        path = path.rstrip("/")

    # Make sure we retain the UNC path structure
    if unc and not path.startswith("//") and path.startswith("/"):
        path = "/" + path

    return path


def get_unique_pose_name(root_path, pose_name):
    """
    This function will check if pose of the given pose name exists under a directory. If so, increment the
    pose name until a unique pose name is found
    Args:
        root_path(str):
        pose_name(str):

    Returns:

    """
    full_path = os.path.join(root_path, pose_name)
    if os.path.exists(full_path):
        new_name = increment_name(pose_name)
        return get_unique_pose_name(root_path, new_name)
    return pose_name


def norm_paths(paths):
    """
    Normalize all the given paths to a consistent format.

    :type paths: list[str]
    :rtype: list[str]
    """
    return [norm_path(path) for path in paths]


def list_leaves(root_dir):
    dirs = []
    files = []
    list_dir = os.listdir(root_dir)
    leave_dir = True
    for i in list_dir:
        full_path = norm_path(os.path.join(root_dir, i))
        if i.endswith('_footage'):
            continue
        elif i.endswith('.apd'):
            leave_dir = False
            files.append(full_path)
        elif os.path.isdir(full_path):
            r_dirs, r_files = list_leaves(full_path)
            if root_dir or r_files:
                leave_dir = False
            dirs.extend(r_dirs)
            files.extend(r_files)
    if leave_dir:
        dirs.append(root_dir)

    return dirs, files


def find_footage_folder(pose_file):
    """
    Return the footage folder associated with a pose file
    Args:
        pose_file(str): A path of pose file

    Returns:
        str: If footage folder for given pose file exists
        None: If no footage folder found

    """
    if not os.path.isfile(pose_file):
        return
    dir_name, base_name, ext = split_path(pose_file)
    footage_folder = norm_path(os.path.join(dir_name, '{}_footage'.format(base_name)))
    if os.path.isdir(footage_folder):
        return footage_folder


def move_pose_file(pose_file, destination):
    if not os.path.isfile(pose_file):
        return
    dir_name, base_name, ext = split_path(pose_file)
    footage_folder = find_footage_folder(pose_file)
    unique_name = get_unique_pose_name(destination, base_name)
    pose_dst = norm_path(os.path.join(destination, unique_name + '.apd'))
    os.rename(pose_file, pose_dst)

    if footage_folder:
        footage_dst = norm_path(os.path.join(destination, unique_name + '_footage'))
        os.rename(footage_folder, footage_dst)
    return pose_dst


def delete_pose_and_footage(pose_file):
    """
    Delete a pose file and the footage images associated with it
    Args:
        pose_file(str): The path of pose file

    """
    footage = find_footage_folder(pose_file)
    if footage:
        shutil.rmtree(footage)
    os.remove(pose_file)


def split_path(path):
    """
    Split the given path into directory, basename and extension.

    Example:
        print splitPath("P:/production/rigs/character/mario.ma

        # (u'P:/production/rigs/character', u'mario', u'.ma')

    :type path: str
    :rtype: list[str]
    """
    path = norm_path(path)
    filename, extension = os.path.splitext(path)
    return os.path.dirname(filename), os.path.basename(filename), extension


def list_all_reference_namespaces():
    """
    List all target namespaces options
    Returns:

    """
    name_spaces = ['']
    for i in cmds.ls(type='reference'):
        ref = Node(i)
        try:
            ns = ref.namespace
            name_spaces.append(ns)
        except RuntimeError:
            continue
    name_spaces.sort()
    return name_spaces


def resolve_additional_root_paths():
    """
    This function is a method user can override to load some
    anim pose roots based on an arbitrary logic
    Returns:
        list:
        None:
    """
    return None
