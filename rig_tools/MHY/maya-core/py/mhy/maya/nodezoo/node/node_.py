"""

This module is the main interface to create a Node object. Node class
is a factory interface that will return an inherited class instance based
on the object passed to Node and create object with it.

"""

# Standard library imports
import re
import six
import traceback
import inspect


# Maya imports
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya


# Package imports
from mhy.python.core.compatible import format_arg_spec
from mhy.maya.nodezoo._manager import _NODE_TYPE_LIB
from mhy.maya.nodezoo.exceptions import NodeClassInitError, MayaObjectError
from mhy.maya.nodezoo._mayaUtils import get_api_object, is_valid_m_object_handle
from mhy.maya.nodezoo.constant import kMObjectHandleStr, kMFnNodeStr, nodezoo_tag_attr

NODE_TYPE_ATTR = '__NODETYPE__'
CUSTOM_TYPE_ATTR = '__CUSTOMTYPE__'


class _NodeMeta(type):
    """
    Metaclass that register node types to a cached dictionary
    """
    def __new__(mcs, class_name, bases, attrs):
        cls_obj = type.__new__(mcs, class_name, bases, attrs)
        if class_name != 'Node':
            prop = attrs.get(CUSTOM_TYPE_ATTR)
            if prop:
                node_type = prop
            else:
                node_type = attrs.get(NODE_TYPE_ATTR)
            if node_type is None:
                raise NotImplementedError(
                    ('Every node class must define one of the 2 type attrs: '
                     '{} or {}. {} defined neither').format(
                         NODE_TYPE_ATTR, CUSTOM_TYPE_ATTR, class_name))

            _NODE_TYPE_LIB[node_type] = cls_obj
        return cls_obj

    def __repr__(cls):
        return cls.__name__


class Node(six.with_metaclass(_NodeMeta)):
    __internal_data = {}
    __FNCLS__ = None

    def __new__(cls, *args, **kwargs):
        """
          Example Usage:

          >>> import mhy.maya.nodezoo.node as node_api
          >>> import maya.cmds as cmds
          >>> joint = cmds.joint()
          >>> joint_instance = node_api.Node(joint)

        Args:
            *args:
            **kwargs:
        """

        def _get_mobject_and_internal_data(node):
            data = {}
            if isinstance(node, OpenMaya.MDagPath):
                data['MDagPath'] = node
                node = node.node()
                data['MObjectHandle'] = OpenMaya.MObjectHandle(node)

            elif isinstance(node, OpenMaya.MObjectHandle):
                data['MObjectHandle'] = node
                node = node.object()
                if node.hasFn(OpenMaya.MFn.kDagNode):
                    dag_path = OpenMaya.MDagPath()
                    OpenMaya.MDagPath.getAPathTo(node, dag_path)
                    data['MDagPath'] = dag_path

            elif isinstance(node, OpenMaya.MObject):
                data['MObjectHandle'] = OpenMaya.MObjectHandle(node)
                if node.hasFn(OpenMaya.MFn.kDagNode):
                    dag_path = OpenMaya.MDagPath()
                    OpenMaya.MDagPath.getAPathTo(node, dag_path)
                    data['MDagPath'] = dag_path
            else:
                raise NodeClassInitError('{} is not supported object.'
                                         'supported objects are MDagPath'
                                         'and MObject'.format(node))
            return node, data

        assert args, 'Required one argument, got None'
        assert len(args) == 1, 'Required one argument, got {}'.format(len(args))
        arg_obj = args[0]

        obj = None
        # We support Node instance duplication
        if isinstance(arg_obj, Node):
            if 'MObjectHandle' in arg_obj.__internal_data:
                obj = arg_obj.__internal_data['MObjectHandle']
            if 'MDagPath' in arg_obj.__internal_data:
                obj = arg_obj.__internal_data['MDagPath']

        elif hasattr(arg_obj, '__module__') and arg_obj.__module__.startswith('maya.OpenMaya'):
            obj = arg_obj
        elif isinstance(arg_obj, six.string_types):
            obj = get_api_object(arg_obj)
        else:
            raise NodeClassInitError('{} is not either a Node object or string'.format(arg_obj))
        obj, internal_data = _get_mobject_and_internal_data(obj)
        node_cls = Node._get_cls_from_object(obj)
        target_cls = object.__new__(node_cls)
        target_cls.__internal_data = internal_data
        return target_cls

    # ------------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------------

    @classmethod
    def _pre_creation_callback(cls, *args, **kwargs):
        return args, kwargs

    @classmethod
    def _post_creation_callback(cls, *args, **kwargs):
        return args, kwargs

    @classmethod
    def import_create(cls, *args, **kwargs):
        """
        This function is called while importing creation data. User can register call back
        before or after the creation.
        Args:
            *args:
            **kwargs:

        Returns:

        """
        args, kwargs = cls._pre_creation_callback(*args, **kwargs)
        node = cls.create(*args, **kwargs)
        cls._post_creation_callback(*args, **kwargs)
        return node

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Calls the create() method in the specified node class.
        Args:
            *args:
            **kwargs:

        Returns:

        """
        args = list(args)
        if not args:
            raise ValueError('Must specify a node type.')
        typ = args.pop(0)

        try:
            if typ and inspect.isclass(typ) and issubclass(typ, Node):
                return typ.create(*args, **kwargs)
            node_class = _NODE_TYPE_LIB.get(typ)
            if node_class:
                return node_class.create(*args, **kwargs)
            else:
                return Node(cmds.createNode(typ, *args, **kwargs))
        except BaseException as e:
            traceback.print_exc()
            raise RuntimeError(str(e))

    @classmethod
    def load_data(cls, data, create_node=True, make_connections=True,
                  name_map=None, namespace_map=None, recreate=False,
                  **kwargs):
        """
        This method load data into the current maya scene. It will check
        the existence of the object named as the data. If it's there, node
        data will be loaded to the existing object. Otherwise, there's option
        to create a new node or just abort execution
        Args:
            data(dict): Dictionary format node data.
            create_node(bool): If create a new node if there's no existing object
            named the same
            make_connections(bool): If make connections to attributes
            name_map(dict):
            namespace_map(tuple):
            recreate(bool)
        Returns:
            (nodezoo.Node) Node instance

        """
        cls_type = data.get('type')
        if not cls_type:
            return
        cls_obj = _NODE_TYPE_LIB.get(cls_type)
        if not cls_obj:
            cls_obj = _NODE_TYPE_LIB.get('dependencyNode')
        name = data.get('name')
        if not name:
            OpenMaya.MGlobal.displayWarning("Got invalid data. No name information found")
            return

        Node.get_new_name_from_map(name, name_map, namespace_map)
        name = Node.get_new_name_from_map(name, name_map, namespace_map)
        data['name'] = name
        node = None
        if Node.object_exist(name):
            if recreate:
                Node(name).delete()
                create_node = True
            else:
                node = Node(name)
                create_node = False
        if create_node:
            creation_data = data.get('creation', {})
            if not creation_data:
                OpenMaya.MGlobal.displayError("Data to import has no 'creation' data. Please make sure "
                                              "creation data exported")
                return
            args = creation_data.get('_args', [])
            creation_kwargs = {str(key): creation_data[key] for key in creation_data if key != '_args'}
            create_name = kwargs.get('name')
            if create_name:
                kwargs['name'] = Node.get_new_name_from_map(create_name,
                                                            name_map,
                                                            namespace_map)
            node = cls_obj.import_create(*args, **creation_kwargs)

        if node:
            node.load(data, make_connections=make_connections, **kwargs)

        return node

    @classmethod
    def object_exist(cls, obj):
        """
        Check if the object exists in the scene
        Args:
            obj:

        Returns:
            bool: If object is valid and exists
        """
        if isinstance(obj, six.string_types):
            return cmds.objExists(obj)
        elif isinstance(obj, OpenMaya.MObject):
            handle = OpenMaya.MObjectHandle(obj)
            return handle.isValid() and handle.isValid()
        elif isinstance(obj, OpenMaya.MObjectHandle):
            return obj.isAlive() and obj.isValid()
        elif isinstance(obj, OpenMaya.MDagPath):
            if not obj.isValid():
                return False
            m_obj = obj.node()
            handle = OpenMaya.MObjectHandle(m_obj)
            return handle.isValid() and handle.isValid()
        return False

    @classmethod
    def make_custom_node(cls, node):
        """
        Makes a given node as a custom node of this type by creating
        a nodezoo custom tag attribute.

        Args:
            node(str): Name of the node

        Returns:
            Node: Node instance applied the tag attribute to
        """

        typ = getattr(cls, CUSTOM_TYPE_ATTR)
        if typ:
            cmds.addAttr(node, longName=nodezoo_tag_attr, dataType='string')
            attr = '{}.{}'.format(node, nodezoo_tag_attr)
            cmds.setAttr(attr, typ, type='string')
            cmds.setAttr(attr, lock=True)
            return cls(node)
        else:
            raise RuntimeError('{} is not a custom node type.'.format(cls))

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------

    @property
    def custom_type_name(self):
        """Returns the nodezoo custom type name."""
        return getattr(self, CUSTOM_TYPE_ATTR)

    @property
    def maya_handle(self):
        """
        Get the cached maya handle object
        Returns:
            MObjectHandle:
        """
        return self.internal_data.get(kMObjectHandleStr)

    @property
    def is_valid(self):
        """
        Check the internal mobject associated with this instance is still valid
        Returns:
            bool: If valid
        """
        handle = self.maya_handle
        if handle:
            return handle.isValid()
        return False

    @property
    def internal_data(self):
        return self.__internal_data

    @property
    def fn_node(self):
        """
        Query the fn node object representation of this node
        Returns:
            MFnDependencyNode: If this node has no dag information
            MFnDagNode: If this node has dag information
        """
        m_obj = self.api_repr()
        result = None
        if self.internal_data.get(kMFnNodeStr):
            # Check if the MObject still valid
            return self.__internal_data[kMFnNodeStr]

        try:
            if not self.__FNCLS__:
                raise RuntimeError
            result = self.__FNCLS__(m_obj)
            self.internal_data[kMFnNodeStr] = result
        except RuntimeError:
            if isinstance(m_obj, OpenMaya.MObject):
                result = OpenMaya.MFnDependencyNode(m_obj)

            elif isinstance(m_obj, OpenMaya.MDagPath):
                result = OpenMaya.MFnDagNode(m_obj)
        self.internal_data[kMFnNodeStr] = result
        return result

    # ------------------------------------------------------------------------
    # Instance Methods
    # ------------------------------------------------------------------------

    def api_repr(self):
        return self.object()

    def object(self):
        handle = self.maya_handle
        if is_valid_m_object_handle(handle):
            return handle.object()
        raise MayaObjectError("Failed to get valid MObjectHandle for node, \n"
                              " It's probably not set, deleted or not in the scene")

    def delete(self, **kwargs):
        """Deletes this node."""
        cmds.delete(self, **kwargs)

    def help(self, verbose=False):
        """
        Print out the help message related to this node
        Args:
            verbose(bool): If help message include detailed doc
        """
        def format_doc(doc_str):
            doc_str = '\t' + doc_str.lstrip().rstrip() + '\n'
            return doc_str
        msg = '\n>> {}\n'.format(repr(self))

        for m in inspect.getmembers(self, predicate=inspect.ismethod):
            if m[0].startswith('_'):
                continue
            msg = msg + '+ ' + m[0] + format_arg_spec(m[1]) + '\n'
            if verbose:
                doc = m[1].__doc__
                if doc:
                    msg = msg + format_doc(doc) + '\n'
        OpenMaya.MGlobal.displayInfo(msg)

    # ------------------------------------------------------------------------
    # Static Methods
    # ------------------------------------------------------------------------
    @staticmethod
    def _get_cls_from_object(obj):
        """
        Query the class object based on the type of object passed in.

        Following the rules below:

        1. If found specific class for this type, return it from cached data.
        2. If not, we try to match the most specific class in the order of
        "transform", "geometryFilter", "locator", "dagNode", "dependencyNode"

        Args:
            obj(OpenMaya.MObject): An MObject instance

        Returns:
            (_NodeMeta): get a sub-class object of Node

        """
        assert isinstance(obj, OpenMaya.MObject)
        cls = None
        if obj.hasFn(OpenMaya.MFn.kDependencyNode):
            dep_node = OpenMaya.MFnDependencyNode(obj)
            type_name = None
            if dep_node.hasAttribute(nodezoo_tag_attr):
                plug = dep_node.findPlug(nodezoo_tag_attr)
                if not plug.isNull():
                    type_name = plug.asString()
                    if not type_name or type_name not in _NODE_TYPE_LIB:
                        type_name = None
            if not type_name:
                type_name = dep_node.typeName()
            if type_name in _NODE_TYPE_LIB:
                return _NODE_TYPE_LIB[type_name]
            if obj.hasFn(OpenMaya.MFn.kTransform):
                cls = _NODE_TYPE_LIB['transform']
            elif obj.hasFn(OpenMaya.MFn.kWeightGeometryFilt) or obj.hasFn(OpenMaya.MFn.kGeometryFilt):
                cls = _NODE_TYPE_LIB['geometryFilter']
            elif obj.hasFn(OpenMaya.MFn.kDagNode):
                cls = _NODE_TYPE_LIB['dagNode']
            elif obj.hasFn(OpenMaya.MFn.kDependencyNode):
                cls = _NODE_TYPE_LIB['dependencyNode']
        else:
            raise RuntimeError(
                "Could not determine type for object of type {}".format(obj.apiTypeStr)
            )
        return cls

    @staticmethod
    def get_new_name_from_map(name, name_map=None, namespace_map=None):
        """
        Generate a new name based on the name map and namespace map dictionary
        Args:
            name(str):
            name_map(dict or None): If given, map the name by replacing key to value in the map
            namespace_map(tuple or None): If given, map the name space by replacing first item in tuple with second.
            If second item is empty string, remove namespace

        Returns:
            str: A new name
        """
        name_space = ""
        real_name = name
        if namespace_map:
            namespace_map_from, namespace_map_to = namespace_map
            if ':' not in name:
                name_space = ""
                real_name = name
            else:
                name_space, real_name = name.split(':', 1)

            if name_space == namespace_map_from:
                name_space = namespace_map_to

        if name_map:
            for k, v in name_map.items():
                if k in real_name:
                    real_name = real_name.replace(k, v)
        if name_space:
            return name_space + ":" + real_name
        return real_name
