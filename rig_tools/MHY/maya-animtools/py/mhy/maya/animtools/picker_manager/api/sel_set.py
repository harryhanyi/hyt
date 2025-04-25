"""
This module is the api functions for creating selection sets

"""
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from mhy.maya.nodezoo.node import Node

root_set_name = "MHY_Picker_SELSET"

def simplfy_set_name(sel_set):
    if sel_set.endswith('_SELSET'):
        sel_set = sel_set.rstrip('_SELSET')
    return sel_set

def find_root_set(namespace=None):
    """
    Find the root set of selection sets under a given namespace.
    This function could be also used to query the set for a specific
    rig reference
    Args:
        namespace:

    Returns:
        Set:
    """
    full_name = root_set_name
    if namespace:
        full_name = '{}:{}'.format(namespace, full_name)
    if Node.object_exist(full_name):
        return Node(full_name)


def get_root_set():
    """
    Get the root set of selection sets of picker system,
    if not exists, create one.
    Returns:
        Set: An object set nodezoo instance named as root set name
    """
    root = find_root_set()
    if root:
        return root
    cmds.select(cl=True)
    set_obj = Node.create('objectSet', name=root_set_name, empty=True)
    return set_obj


def create_selection_set(name, objects=None):
    """
    Create
    Args:
        name(str):
        objects(list): A list of objects added to the new set

    Returns:

    """
    if objects is None:
        objects = cmds.ls(sl=True)
    if not name.endswith('_SELSET'):
        name = name + '_SELSET'

    if Node.object_exist(name):
        OpenMaya.MGlobal.displayWarning("Object named {} already exists".format(name))
        return
    root_set = get_root_set()
    new_set = Node.create('objectSet', *objects, name=name)
    root_set.add_member(new_set)
    return new_set


def remove_selection_set(name, root_set):
    for i in list_picker_sets(root_set):
        if i.name == name:
            i.delete()


def list_picker_sets(root_set):
    """
    List all the picker sets
    Args:
        root_set:

    Returns:

    """
    root_set = Node(root_set)
    picker_sets = list()
    for s in root_set.members:
        s = Node(s)
        if s.type_name == "objectSet":
            picker_sets.append(s)
    return picker_sets


def list_picker_sets_with_namespace(namespace=None):
    """
    Convenient method to list all the picker sets under the
    root set of a given namespace
    Args:
        namespace:

    Returns:
        list:

    """
    root_set = find_root_set(namespace=namespace)
    if root_set:
        return list_picker_sets(root_set)
    return list()


def find_related_selection_set(obj, name_space=None):
    """

    Args:
        obj:
        name_space:

    Returns:

    """
    if name_space is None:
        if ':' in obj:
            ns = obj.split(':')[0]
        else:
            ns = None
    else:
        ns = name_space
    result = list()
    for picker_set in list_picker_sets_with_namespace(namespace=ns):
        obj_node = Node(obj)
        if picker_set.is_member(obj_node):
            result.append(picker_set)
    return result


def select_set(sel_set):
    sel_set = Node(sel_set)
    sel_set.select()


def export_sel_set_data():
    data = {}
    root = find_root_set()
    if not root:
        return
    for member_set in root.members:
        member_set = Node(member_set)
        child_member_data = member_set.export()
        data[member_set.name] = child_member_data
    return data


def load_sel_set_data(data):
    root_set = get_root_set()
    # Clear the members of root sel set before loading data
    for member in root_set.members:
        cmds.delete(member)

    for name, set_data in data.items():
        members = set_data.get('members')
        if not members:
            continue
        members = [member for member in members if cmds.objExists(member)]
        create_selection_set(name=name, objects=members)
