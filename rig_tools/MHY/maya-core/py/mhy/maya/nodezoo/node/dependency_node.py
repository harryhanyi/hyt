import re
from six import string_types
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.attribute import Attribute
from mhy.maya.nodezoo.constant import DataFormat
from mhy.maya.nodezoo.node import Node
import mhy.maya.nodezoo.constant as const

from mhy.python.core.compatible import classproperty

SEP_ATTR_PREFIX = 'mhy_separator_attr'


class DependencyNode(Node):
    """
    Dependency node class.

    """

    __NODETYPE__ = 'dependencyNode'
    __CUSTOMTYPE__ = None
    __FNCLS__ = OpenMaya.MFnDependencyNode

    attribute_to_export_override = None
    attribute_to_ignore_override = None

    def __repr__(self):
        return "<Nodezoo.Node {0}: '{1}' at <{2}>>".format(
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, DependencyNode):
            return False
        return self.maya_handle == other.maya_handle

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.long_name)

    def __getattr__(self, attr_name):
        try:
            return self.attr(attr_name)
        except Exception:
            raise AttributeError("'{0}' has no attribute or method named '{1}'".format(repr(self), attr_name))

    @classproperty
    def api_type_str(cls):
        """
        This method allows user to query the node type name from the
        class without an instance.
        If this class is a custom override type, return the custom type
        string instead maya api node type
        Returns:
            str: The node type associated with this class
        """
        return cls.__CUSTOMTYPE__ or cls.__NODETYPE__

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            node = cmds.createNode(cls.__NODETYPE__, *args, **kwargs)
        except RuntimeError as e:
            raise RuntimeError(str(e))
        if node:
            return Node(node)

    # --- basic properties

    @property
    def type_name(self):
        """Returns the node type name."""
        return str(self.fn_node.typeName())

    @property
    def inherited_types(self):
        """Returns a list of type names this node inherits"""
        return cmds.nodeType(self.name, inherited=True)

    @property
    def name(self):
        """Returns the short name of this node."""
        if not self.is_valid:
            return ''
        fn_node = self.fn_node
        if fn_node:
            return str(fn_node.name())
        return ''

    @name.setter
    def name(self, new_name):
        """
        Sets the short name of this node.

        Args:
            new_name(str): The new name to set

        """

        assert isinstance(new_name, string_types), \
            'New name {} is not a string type data'.format(new_name)
        cmds.rename(self.long_name, new_name)

    def get_name_space(self):
        """
        Get the namespace of this node
        Returns:
            str: The namespace
        """
        if ':' in self.name:
            return self.name.split(':')[0]

    @property
    def long_name(self):
        """
        Returns the long name of this node.

        Returns:
            str: The long name
        """

        return self.name

    @property
    def is_deformable(self):
        """
        Returns the deformable state.
        Returns:
            bool: If deformable
        """
        return False

    @property
    def is_referenced(self):
        """
        Returns True if this node is referenced, otherwise False.
        Returns:
            bool
        """
        return cmds.referenceQuery(self, isNodeReferenced=True)

    # --- attribute methods

    def attr(self, attr_name):
        """Returns an attribute object.

        Args:
            attr_name (str): An attribute name to work with.

        Returns:
            Attribute: the attribute object.
        """
        return Attribute(self, attr_name)

    def list_attr(self, **kwargs):
        """Wraps cmds.listAttr()"""
        return [Attribute(self, attr) for attr in
                cmds.listAttr(self.name, **kwargs) or []]

    def top_level_attrs(self, **kwargs):
        """Returns a list of attributes on this node which is not a child attr.
        Returns:
            list: List or Attributes
        """
        attrs = []
        num_attrs = self.fn_node.attributeCount()
        for i in range(num_attrs):
            attr_obj = self.fn_node.attribute(i)
            plug = OpenMaya.MPlug(self.object(), attr_obj)
            if plug.isChild():
                # Make sure we only need top level plugs
                continue

            attr = Attribute(plug)
            # Added some filter features. e.g. kwargs: keyable = True
            # Filter key should be the member of Attribute instance
            for key, val in kwargs.items():
                if hasattr(attr, key) and not getattr(attr, key) == val:
                    break
            else:
                attrs.append(attr)

        return attrs

    def add_attr(self, typ, name='attr', **kwargs):
        """Adds an attribute on this node.

        also accept following args in cmds.setAttr():
            + lock
            + channelBox
        (only has effecit when keyable is False)

        Args:
            typ (str): The attribute type.
            name (str): The attribute name.
            kwargs: Keyword arguments accepted by cmds.addAttr().

        Returns:
            Attribute: The new attribute object.

        Raises:
            ValueError: If attribute already exists.
        """
        if self.fn_node.hasAttribute(name):
            raise ValueError(
                'Attribute already exists: {}.{}'.format(self.name, name))

        # remove default name and type kwargs
        for key in ('ln', 'at', 'dt', 'attributeType', 'dataType'):
            if key in kwargs:
                kwargs.pop(key)

        # set name and type kwargs
        kwargs['longName'] = name
        val = None
        if typ.endswith('Array') or typ.endswith('RGB') or typ[-1].isdigit() or \
           typ in ('string', 'matrix', 'nurbsCurve', 'nurbsSurface', 'lattice'):
            kwargs['dataType'] = typ
            for key in ('defaultValue', 'dv'):
                if key in kwargs:
                    val = kwargs.pop(key)
        else:
            kwargs['attributeType'] = typ

        # allow specificing enum default with an enum name string
        if typ == 'enum':
            # consolidate default value kwarg
            if 'dv' in kwargs:
                kwargs['defaultValue'] = kwargs.pop('dv')
            default = kwargs.get('defaultValue')

            if default is not None and not isinstance(default, int):
                enums = kwargs.get('enumName', kwargs.get('en'))
                if enums:
                    enums = enums.split(':')
                    if default in enums:
                        kwargs['defaultValue'] = enums.index(default)
                    else:
                        raise AttributeError(
                            'Enum name not found: {}'.format(default))

        # for non-keyable attrs, set channel box and locked state
        keyable = False
        for key in ('k', 'keyable'):
            if key in kwargs:
                keyable = kwargs[key]
                break

        channelBox = True
        lock = False
        if not keyable:
            for key in ('ch', 'channelBox'):
                if key in kwargs:
                    channelBox = kwargs.pop(key)
                    break
            for key in ('l', 'lock'):
                if key in kwargs:
                    lock = kwargs.pop(key)
                    break

        # create the attr
        cmds.addAttr(self.long_name, **kwargs)
        attr = Attribute(self, name)

        # set value if needed
        if val is not None:
            attr.value = val

        if not keyable:
            attr.channelBox = channelBox
            attr.locked = lock

        return attr

    def add_color_attr(self, name='color', defaultValue=None):
        """Adds a color attribute on this node.

        Args:
            name (str): The attribute name.
            defaultValue (tuple): The default color.

        Returns:
            Attribute: The color attribute object.

        Raises:
            ValueError: If attribute already exists.
        """
        if self.fn_node.hasAttribute(name):
            raise ValueError(
                'Attribute already exists: {}.{}'.format(self.name, name))

        cmds.addAttr(
            self.name, longName=name, attributeType='float3', usedAsColor=True)
        for ch in 'RGB':
            cmds.addAttr(longName=name + ch, attributeType='float', parent=name)
        attr = Attribute(self, name)
        if defaultValue:
            attr.value = defaultValue
        return attr

    def add_separator_attr(self, name='sep'):
        """Adds an enum separator attr on this node.

        Args:
            name (str): The separator attribute name.

        Returns:
            Attribute: The added attribute object.

        Raises:
            ValueError: If attribute already exists.
        """
        attr_name = '{}_{}'.format(SEP_ATTR_PREFIX, name)

        if self.fn_node.hasAttribute(attr_name):
            raise ValueError(
                'Separater attribute already exists: {}.{}'.format(
                    self.name, attr_name))

        attr = self.add_attr(
            'enum', name=attr_name, keyable=False, enumName=name + ':')
        attr.add_category(SEP_ATTR_PREFIX)
        alias = '_' * (len(self.get_separator_attrs()) + 1)
        cmds.aliasAttr(alias, attr.long_name)
        attr.channelBox = True
        attr.locked = True
        return attr

    def has_separator_attr(self, name):
        """Checks if a separator attr exists."""
        return self.has_attr('{}_{}'.format(SEP_ATTR_PREFIX, name))

    def get_separator_attrs(self):
        """Returns a list of separator attributes on this node."""
        attrs = []
        for attr in self.list_attr(userDefined=True):
            if attr.has_category(SEP_ATTR_PREFIX):
                attrs.append(attr)
        return attrs

    def get_attr(self, attr_name):
        """Returns the value of a given attribute."""
        try:
            return self.attr(attr_name).value
        except BaseException:
            val = cmds.getAttr('{}.{}'.format(self.long_name, attr_name))
            if isinstance(val, list) and len(val) == 1:
                return val[0]
            return val

    def set_attr(self, attr_name, value):
        """Sets an attribute value and/or properties.

        Args:
            attr_name (str): Name of the attribute.
            value: The value to set.

        Returns:
            None
        """
        self.attr(attr_name).value = value

    def has_attr(self, attr_name):
        """Checks if an attribute exists on this node."""
        return self.fn_node.hasAttribute(attr_name)

    def delete_attr(self, attr_name):
        """Deletes an attribute on this node."""
        attr = '{}.{}'.format(self.long_name, attr_name)
        cmds.setAttr(attr, lock=False)
        cmds.deleteAttr(attr)

    def add_tag(self, tag, value=None, force=False):
        """Adds a tag on this node with a message attribute.

        Args:
            tag (str): Name of the tag. This will be the attribute name.
            value (str): A value to set the tag attribute to.
                If value is an existing node, use message tag attr.
                Otherwise use string tag attr.
            force (bool): If True and the tag already exists, rebuld it.
                Otherwise raise error.

        Returns: None

        Raises:
            RuntimeError: If tag already exists and force is False.
        """
        tag = str(tag)
        attr = '{}.{}'.format(self.long_name, tag)

        # remove existing tag if any
        if self.has_attr(tag):
            if force:
                self.delete_attr(tag)
            else:
                raise RuntimeError('Tag already exists: {}'.format(attr))

        # create the tag attr and lock it.
        if value and cmds.objExists(value):
            self.add_attr('message', name=tag)
            cmds.connectAttr(
                '{}.message'.format(value), '{}.{}'.format(self, tag))
        else:
            val = str(value) if value else ''
            self.add_attr('string', name=tag, defaultValue=val)
        cmds.setAttr(attr, lock=True)

    def get_tag(self, tag):
        """Searchs for a given tag and return its value.

        Args:
            tag (str): A tag name to search for.

        Returns:
            str: The tag attribute value.
            Node: The tagged node object if the tag is a message attr.
            None: If no tag is found.
        """
        attr = '{}.{}'.format(self.long_name, tag)
        if cmds.objExists(attr):
            if cmds.getAttr(attr, type=True) == 'message':
                cnn = cmds.listConnections(
                    attr, source=True, destination=False,
                    plugs=False, shapes=True)
                if cnn:
                    return Node(cnn[0])
            else:
                return cmds.getAttr(attr)

    def add_marking_menu(self, menu_name, mod=None, replace=False):
        """Associates this node with a marking menu.

        Args:
            menu_name (str): Name of the marking menu to
                associate with this node.
            mod (str): The modifier key. Supprots "shift" and "ctrl".
            replace (bool): If True, replaces existing marking menus.

        Returns:
            None

        Raises:
            ValueError: If mod is invalid.
        """
        if replace:
            menus = [menu_name]
        else:
            menus = self.get_marking_menu(mod=mod)
            if menu_name not in menus:
                menus.append(menu_name)
            else:
                return

        attr = const.nodezoo_mm_attr
        if mod:
            if mod in ('shift', 'ctrl'):
                attr += '_' + mod
            else:
                raise ValueError('Invalid mod "{}".'.format(mod))

        if not self.has_attr(attr):
            self.add_attr('string', name=attr)
        attr = self.attr(attr)
        attr.locked = False
        attr.value = ';'.join(menus)
        attr.locked = True

    def get_marking_menu(self, mod=None):
        """Returns a list of marking menu names associated with this node.

        Args:
            mod (str): The modifier key. Supprots "shift" and "ctrl".

        Returns:
            list: Marking menu names.

        Raises:
            ValueError: If mod is invalid.
        """
        attr = const.nodezoo_mm_attr
        if mod:
            if mod in ('shift', 'ctrl'):
                attr += '_' + mod
            else:
                raise ValueError('Invalid mod "{}".'.format(mod))

        if self.has_attr(attr):
            return self.attr(attr).value.split(';')
        return []

    # --- misc

    def duplicate(self, **kwargs):
        """Duplicates this node.

        Args:
            kwargs: Keyword argument accepted by cmds.duplicate().

        Defaults:
            name: self.name + 'Dup'
            inputConnections: False

        Returns:
            list: The duplicated nodes.
        """
        for keys, default in (
                (('name', 'n'), self.name + 'Dup'),
                (('parentOnly', 'po'), False),
                (('renameChildren', 'rc'), True),
                (('inputConnections', 'ic'), False)):
            if keys[1] in kwargs:
                kwargs[keys[0]] = kwargs.pop(keys[1])
            elif keys[0] not in kwargs:
                kwargs[keys[0]] = default
        nodes = [Node(n) for n in cmds.duplicate(self.long_name, **kwargs)]
        return nodes

    # --- connection methods

    def search_node(self, pattern=None, upstream=True, type_filter=OpenMaya.MFn.kTransform):
        """Search the dependency graph from this node for another node ends with
        a given regex pattern.

        Args:
            pattern (str): A regex pattern used for matching node names.
            upstream (bool): If True, search upstream, otherwise downstream.
            type_filter (OpenMaya.MFn.Type): 	Object type filter

        Returns:
            DependencyNode: The node found.
            None: If no node was found.
        """
        sel_list = OpenMaya.MSelectionList()
        sel_list.add(self.long_name)
        base_object = OpenMaya.MObject()
        sel_list.getDependNode(0, base_object)

        if upstream:
            it_dg = OpenMaya.MItDependencyGraph(
                base_object,
                type_filter,
                OpenMaya.MItDependencyGraph.kUpstream,
                OpenMaya.MItDependencyGraph.kNodeLevel)
        else:
            it_dg = OpenMaya.MItDependencyGraph(
                base_object,
                type_filter,
                OpenMaya.MItDependencyGraph.kDownstream,
                OpenMaya.MItDependencyGraph.kNodeLevel)

        fn_node = OpenMaya.MFnDependencyNode()
        while not it_dg.isDone():
            cur_item = it_dg.currentItem()
            fn_node.setObject(cur_item)
            if pattern is not None:
                if re.match(pattern, fn_node.name()):
                    return Node(cur_item)
            else:
                return Node(cur_item)
            it_dg.next()

    def list_connections(self, attr=None, *args, **kwargs):
        """Wrapper around cmds.listConnections(). """
        nodes = []
        if attr:
            src = self.attr(attr).long_name
        else:
            src = self.name
        for each in cmds.listConnections(src, *args, **kwargs) or []:
            if each.rfind('.') == -1:
                nodes.append(Node(each))
            else:
                nodes.append(Attribute(each))
        return nodes

    def move_connections(
            self, target_node,
            source=True, destination=True,
            connected_nodes=None):
        """
        Moves connections from this node to a target node.

        Args:
            target_node (str or Node): A node to move the connections to.
            source (bool): If True, move source connections.
            destination (bool): If True, move destination connections.
            connected_nodes (list): A only move connections if the node
                on the other end is in this list.
                If None, move all connections.

        Returns:
            None
        """
        target_node = Node(target_node)
        if connected_nodes:
            connected_nodes = [Node(x) for x in connected_nodes]

        # move destination connections:
        if destination:
            connections = cmds.listConnections(
                self, source=False, destination=True,
                connections=True, skipConversionNodes=True, plugs=True) or []

            for i in range(0, len(connections), 2):
                src = connections[i]
                dst = connections[i + 1]

                node, attr = dst.split('.', 1)
                if not connected_nodes and Node(node) not in connected_nodes:
                    continue

                cmds.setAttr(dst, lock=False)
                cmds.disconnectAttr(src, dst)
                node, attr = src.split('.', 1)
                if target_node.has_attr(attr):
                    src = '{}.{}'.format(target_node, attr)
                    cmds.connectAttr(src, dst)

        # move source connections:
        if source:
            connections = cmds.listConnections(
                self, source=True, destination=False,
                connections=True, skipConversionNodes=True, plugs=True) or []
            for i in range(0, len(connections), 2):
                src = connections[i + 1]
                dst = connections[i]

                node, attr = src.split('.', 1)
                if not connected_nodes and Node(node) not in connected_nodes:
                    continue

                cmds.setAttr(dst, lock=False)
                cmds.disconnectAttr(src, dst)
                node, attr = dst.split('.', 1)
                if target_node.has_attr(attr):
                    dst = '{}.{}'.format(target_node, attr)
                    cmds.setAttr(dst, lock=False)
                    cmds.connectAttr(src, dst)

    # --- data methods

    def load(self, data, make_connections=True, rename=False, *args, **kwargs):
        """
        Load data to this node.
        Args:
            data:
            make_connections:
            rename:
            *args:
            **kwargs:

        Returns:

        """
        new_name = data.get('name')
        if new_name and rename:
            self.name = new_name

        attribute_data = data.get('attributes', [])

        self._load_attrs(
            attribute_data,
            make_connections=make_connections)

    def _load_attrs(self, data, make_connections=True):
        self._pre_load_callback()
        for attrData in data:
            attr_name = attrData.get('name')
            if attr_name:
                attr_name = attr_name.split('.')[-1]
                if not self.has_attr(attr_name):
                    continue
                attribute = self.attr(attr_name)
                if attribute:
                    attribute.load(attrData, makeConnections=make_connections)
                else:
                    OpenMaya.MGlobal.displayWarning("{} has not attribute named {}."
                                                    " Skipped".format(self.name, attr_name))
        self._post_load_callback()

    def _pre_load_callback(self):
        pass

    def _post_load_callback(self):
        pass

    @property
    def attributes_to_export(self):
        """
        Implement this in child class to specific attributes need to be exported
        Returns:
            list or None: Need to be implemented in child class that override with specific
            attributes to export
        """
        if self.attribute_to_export_override is not None:
            return self.attribute_to_export_override
        return []

    def set_export_attr(self, val):
        self.attribute_to_export_override = val

    @property
    def attributes_to_ignore(self):
        if self.attribute_to_ignore_override is not None:
            return self.attribute_to_ignore_override
        return []

    def set_ignored_attr(self, val):
        self.attribute_to_ignore_override = val

    def export(self, connection_data=True, creation_data=True,
               additional_data=True, data_format=DataFormat.kJson):
        """
        This is the entry point when exporting data of a dependency node and its child classes.

        Args:
            connection_data(bool):  If export connection data when calling
            creation_data(bool): If export creation data when calling
            additional_data(bool): If export additional data when calling
            data_format(bool): For now only json data format is supported

        Returns:
            (dict)

        """
        data = None
        if data_format == DataFormat.kJson:
            data = {'name': self.name, 'type': self.type_name}
            attr_data = self._export_attrs(with_connection=connection_data)
            if attr_data:
                data['attributes'] = attr_data
            if creation_data:
                c_data = self.export_creation_data()
                if c_data:
                    data['creation'] = c_data
                    data['creation']['name'] = self.name
            if additional_data:
                a_data = self.export_additional_data()
                if a_data:
                    data['additional'] = a_data
        return data

    def _export_attrs(self, with_connection=True, attrs=None):
        if attrs is None:
            if self.attributes_to_export is not None:
                attrs = self.attributes_to_export
            else:
                attrs = self.top_level_attrs()

        ignore_attrs = (
            'binMembership',
            'boundary',
            'caching',
            'containerType',
            'creationDate',
            'creator',
            'currentDisplayLayer',
            'currentRenderLayer',
            'customTreatment',
            'doubleSided',
            'face',
            'ghostFrames',
            'nodeState',
            'outStippleThreshold',
            'overrideEnabled',
            'overridePlayback',
            'playFromCache',
            'rmbCommand',
            'rotateQuaternion',
            'rotateQuaternionW',
            'rotateQuaternionX',
            'rotateQuaternionY',
            'rotateQuaternionZ',
            'springDamping',
            'springRestLength',
            'springStiffness',
            'templateName',
            'templatePath',
            'useComponentPivot',
            'viewName'
        )
        data = []
        for attr in attrs:
            if not isinstance(attr, Attribute):
                if attr in self.attributes_to_ignore \
                        or attr in ignore_attrs:
                    continue
                if not self.has_attr(attr):
                    continue
                attr = Attribute(self, attr)
            if self.attributes_to_ignore and \
                    not all(iga not in attr.name for iga in self.attributes_to_ignore):
                continue
            attr_data = attr.export(
                withConnection=with_connection,
                isNested=True,
                ignore=self.attributes_to_ignore)
            if attr_data:
                data.append(attr_data)
        return data

    def export_creation_data(self):
        """
        This is a virtual method that will be overridden in child class
        if creation data is required to export. The creation data is used if
        we need to create the instance when loading the data into the scene.

        Returns:
            dict: creation data

        """
        return {"name": self.name}

    def export_additional_data(self):
        """
        This is a virtual method that will be overridden in child class
        if additional data is required to export. The additional data is not
        required to re-create the instance but necessary for some special cases.

        Returns:
            dict: creation data

        """
        return {}

    def _pre_export_callback(self, *args, **kwargs):
        return args, kwargs

    def _post_export_callback(self, *args, **kwargs):
        return args, kwargs
