import maya.OpenMaya as OpenMaya
from six import string_types

from mhy.maya.nodezoo.exceptions import ObjectNotFoundError


def get_api_object(name):
    """
    Get the MObject from a name

    Args:
        name(str):

    Returns:
        OpenMaya.MObject

    """
    assert isinstance(name, string_types)
    if not name:
        raise ObjectNotFoundError('Got empty object name')
    if '.' in name:
        # If it's an attribute name, cast it to the node object
        name = name.split('.')[0]

    sel = OpenMaya.MSelectionList()
    if '->' not in name and '-' in name:
        try:
            m_uuid = OpenMaya.MUuid(name)
            sel.add(m_uuid)
        except RuntimeError:
            raise ObjectNotFoundError('No object found from uuid {}'.format(name))
    else:
        try:
            sel.add(name)
        except RuntimeError:
            raise ObjectNotFoundError('No object named {}'.format(name))

    if sel.length() > 1:
        raise ObjectNotFoundError('More than one object matches {}'.format(name))

    if sel.length() == 0:
        raise ObjectNotFoundError('No object matches {}'.format(name))

    try:
        # Try to get dag node first because it keeps the hierarchy information
        dag = OpenMaya.MDagPath()
        sel.getDagPath(0, dag)
        dag_node = dag.node()
        if not dag_node or not dag_node.hasFn(OpenMaya.MFn.kDagNode):
            raise RuntimeError
        return dag
    except RuntimeError:
        obj = OpenMaya.MObject()
        sel.getDependNode(0, obj)
        return obj


def is_valid_m_object_handle(obj):
    """
        Check if obj is a valid MObjectHandle
    """
    return isinstance(obj, OpenMaya.MObjectHandle) and obj.isValid() and obj.isAlive


def is_valid_m_object(obj):
    """
    Check if obj is a valid MObject
    """
    return isinstance(obj, OpenMaya.MObject) and not obj.isNull()
