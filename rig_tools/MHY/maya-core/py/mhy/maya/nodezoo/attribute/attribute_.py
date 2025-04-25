from six import string_types
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.exceptions import MayaAttributeError


class Attribute(object):
    __internal_data = {}

    def __new__(cls, *args, **kwargs):
        import mhy.maya.nodezoo.node as node_api
        from mhy.maya.nodezoo.attribute import ArrayAttribute, CompoundAttribute,\
            MultiNumericAttribute, NumericAttribute, MatrixAttribute, \
            LightDataAttribute, EnumAttribute, UnitAttribute,\
            GenericAttribute, TypedAttribute, MessageAttribute

        assert args and len(args) < 3, "Supported arguments are 1. Attribute instance 2.Node and attribute name"
        arg_obj = args[0]

        if isinstance(arg_obj, OpenMaya.MPlug):
            plug = OpenMaya.MPlug(arg_obj)

        elif isinstance(arg_obj, CompoundAttribute):
            if len(args) == 1:
                return arg_obj
            attr_name = args[1]
            assert isinstance(attr_name, string_types), "Attribute name argument is not a string. " \
                                                        "It's {}".format(type(args[1]))
            attr = arg_obj.find_child(attr_name)
            return attr

        elif isinstance(arg_obj, Attribute):
            # The order of compoundAttribute and Attribute can't switch
            # Copy
            return arg_obj
        elif isinstance(arg_obj, node_api.Node):
            # We need attr name to query attribute on a node
            assert len(args) > 1, "Need the second argument as attribute name"
            attr_name = args[1]
            assert isinstance(attr_name, string_types), "Attribute name is invalid type {}. " \
                                                        "Need a string".format(type(attr_name))
            sel = OpenMaya.MSelectionList()
            # Now we need to get the plug object
            if '.' in attr_name or '[' in attr_name:
                plug = get_plug_from_object_and_attr_name(arg_obj, attr_name)
            else:
                try:
                    # Try to directly find plug from the dependencyNode
                    plug = arg_obj.fn_node.findPlug(attr_name, True)
                    if '[-1]' in plug.name():
                        # There's possible maya bug if find the plug incorrectly
                        # If so we roll back to find plug using full attr name
                        raise RuntimeError
                except RuntimeError:
                    plug = get_plug_from_object_and_attr_name(arg_obj, attr_name)

        elif isinstance(arg_obj, string_types):
            assert '.' in arg_obj, "{} is not a valid attribute full path".format(arg_obj)
            sel = OpenMaya.MSelectionList()
            plug = OpenMaya.MPlug()
            try:
                sel.add(arg_obj)
                sel.getPlug(0, plug)
            except RuntimeError:
                OpenMaya.MGlobal.displayWarning("Failed to find plug: {}".format(arg_obj))
                return None

        else:
            raise ValueError("The first argument '{}' is not supported".format(arg_obj))

        assert plug, "Unable to generate valid plug from provided arguments"

        data = {'MPlug': plug}

        attribute = plug.attribute()
        if plug.isArray():
            new_cls = ArrayAttribute
        elif plug.isCompound():
            if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
                new_cls = MultiNumericAttribute
            else:
                new_cls = CompoundAttribute
        elif attribute.hasFn(OpenMaya.MFn.kEnumAttribute):
            new_cls = EnumAttribute
        elif attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
            new_cls = NumericAttribute
        elif attribute.hasFn(OpenMaya.MFn.kGenericAttribute):
            new_cls = GenericAttribute
        elif attribute.hasFn(OpenMaya.MFn.kMatrixAttribute):
            new_cls = MatrixAttribute
        elif attribute.hasFn(OpenMaya.MFn.kLightDataAttribute):
            new_cls = LightDataAttribute
        elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
            new_cls = UnitAttribute
        elif attribute.hasFn(OpenMaya.MFn.kTypedAttribute):
            new_cls = TypedAttribute
        elif attribute.hasFn(OpenMaya.MFn.kMessageAttribute):
            new_cls = MessageAttribute
        else:
            raise MayaAttributeError('Unable to create class based on type')

        target_class = object.__new__(new_cls)
        target_class.__internal_data = data

        return target_class

    def __repr__(self):
        return "<Nodezoo.Attribute:{0}: '{1}' at <{2}>>".format(
            self.__class__.__name__,
            self.short_name,
            hex(id(self)))

    def __str__(self):
        return self.short_name

    def __eq__(self, other):
        if isinstance(other, OpenMaya.MPlug):
            return self.__plug__.partialName(True, False, False, False, False, True) ==\
                   other.partialName(True, False, False, False, False, True)
        elif isinstance(other, Attribute):
            return self.long_name == other.long_name
        raise MayaAttributeError(
            'Can\'t compare Attribute object with {}'.format(type(other)))

    def __hash__(self):
        return hash(self.long_name)

    @property
    def name(self):
        return str(self.__plug__.partialName(False, False, False, False, False, True))

    @property
    def alias(self):
        return str(self.__plug__.partialName(False, False, False, True, False))

    @alias.setter
    def alias(self, alias):
        if not alias:
            cmds.aliasAttr(self.long_name, remove=True)
        else:
            cmds.aliasAttr(alias, self.long_name)

    @property
    def node(self):
        from mhy.maya.nodezoo.node import Node
        return Node(self.__plug__.node())

    @property
    def value(self):
        """
        This property has to be implemented in sub classes
        """
        return None

    @value.setter
    def value(self, val):
        """
        This property.setter has to be implemented in sub classes
        """

    @property
    def short_name(self):
        return '{}.{}'.format(self.node.name, self.name)

    @property
    def long_name(self):
        return '{}.{}'.format(self.node.long_name, self.name)

    @property
    def parent(self):
        """Returns the parent attribute, if any."""
        try:
            parent = self.__plug__.parent()
            return Attribute(parent.name())
        except BaseException:
            return

    @property
    def is_compound(self):
        """Checks if this is a compound attr."""
        return self.__plug__.isCompound()

    @property
    def __plug__(self):
        return self.__internal_data.get('MPlug')

    @property
    def is_element(self):
        return self.__plug__.isElement()

    @property
    def index(self):
        assert self.is_element, "Only element plug has index"
        return self.__plug__.logicalIndex()

    @property
    def locked(self):
        """Returns the locked state."""
        return self.__plug__.isLocked()

    @locked.setter
    def locked(self, state):
        """Sets the locked state."""
        self.__plug__.setLocked(bool(state))

    @property
    def keyable(self):
        """Returns the keyable state."""
        return self.__plug__.isKeyable()

    @keyable.setter
    def keyable(self, state):
        """Sets the keyable state."""
        self.__plug__.setKeyable(bool(state))

    @property
    def channelBox(self):
        """Returns the channelbox state."""
        return self.__plug__.isChannelBoxFlagSet()

    @channelBox.setter
    def channelBox(self, state):
        """Sets the channelbox state."""
        self.__plug__.setChannelBox(bool(state))

    @property
    def dynamic(self):
        """Returns the dynamic state."""
        return self.__plug__.isDynamic()

    @property
    def num_children(self):
        """Returns the number of children."""
        return self.__plug__.numChildren()

    @property
    def num_elements(self):
        """Returns the number of elements if this is a array plug."""
        if self.is_array:
            return self.__plug__.numElements()
        return 0

    @property
    def default(self):
        """The default attr value, if any."""
        try:
            return cmds.attributeQuery(
                self.name, node=self.node, listDefault=True)[0]
        except BaseException:
            return

    @property
    def is_child(self):
        """Checks if this attribute is a child attribute."""
        return self.__plug__.isChild()

    def child(self, i):
        """Returns the child plug."""
        return Attribute(self.__plug__.child(i))

    # -----------------------------------------------------------------
    # Connections
    # -----------------------------------------------------------------

    @property
    def source(self):
        plug = self.__plug__.source()
        if plug.isNull():
            return
        return Attribute(plug)

    @property
    def sourceWithConversion(self):
        plug = self.__plug__.sourceWithConversion()

        if plug.isNull():
            return
        return Attribute(plug)

    @property
    def source_node(self):
        """
        Get the node connected to this attribute as source
        Returns:
            Node: The connected source node
            None: This attribute is not connected as destination
        """
        plug = self.__plug__.source()
        if plug.isNull():
            return
        return Attribute(plug).node

    @property
    def destinations(self):
        plugArray = OpenMaya.MPlugArray()
        self.__plug__.destinations(plugArray)
        dests = []
        if plugArray.length():
            for i in range(plugArray.length()):
                attr = Attribute(plugArray[i])
                dests.append(attr)
        return dests

    @property
    def destinationsWithConversions(self):
        plugArray = OpenMaya.MPlugArray()
        self.__plug__.destinationsWithConversions(plugArray)
        dests = []
        if plugArray.length():
            for i in range(plugArray.length()):
                attr = Attribute(plugArray[i])
                dests.append(attr)
        return dests

    @property
    def isConnected(self):
        return self.__plug__.isConnected()

    def connectedTo(self, asDst=True, asSrc=True):
        plugArray = OpenMaya.MPlugArray()
        self.__plug__.connectedTo(plugArray, asDst, asSrc)
        attrs = []
        for i in range(plugArray.length()):
            plug = plugArray[i]
            attr = Attribute(plug)
            attrs.append(attr)

        return attrs

    def is_connected_to(self, other):
        """
        Check if this attribute is connected to another attribute
        Args:
            other(Attribute or MPlug or str): Another attribute

        Returns:
            bool: If this attribute is connected to another
        """
        if isinstance(other, (OpenMaya.MPlug, string_types)):
            other = Attribute(other)
        assert isinstance(other, Attribute), "{} is not a valid attribute".format(other)
        for i in self.connectedTo():
            if other == i:
                return True
        return False

    def connect(self, other, force=False, lock=False):
        if isinstance(other, OpenMaya.MPlug):
            other = Attribute(other)
        assert isinstance(other, Attribute), "{} is not a valid attribute".format(other)
        if not cmds.isConnected(self.long_name, other.long_name):
            cmds.connectAttr(self.long_name, other.long_name, force=force, lock=lock)

    def disconnect(self, other):
        if isinstance(other, OpenMaya.MPlug):
            other = Attribute(other)
        assert isinstance(other, Attribute), "{} is not a valid attribute".format(other)
        if cmds.isConnected(self.long_name, other.long_name):
            cmds.disconnectAttr(self.long_name, other.long_name)

    def __rshift__(self, other):
        self.connect(other, force=True)

    def __floordiv__(self, other):
        self.disconnect(other)

    @property
    def is_writable(self):
        fn_attr = OpenMaya.MFnAttribute(self.__plug__.attribute())
        return fn_attr.isWritable()

    @property
    def is_free_to_change(self):
        return self.__plug__.isFreeToChange() is OpenMaya.MPlug.kFreeToChange

    @property
    def is_array(self):
        return self.__plug__.isArray()

    def remove(self, break_connections=True):
        """
        Remove element from array attribute.
        Args:
            break_connections(bool): If the argument is true, all connections to the attribute will be
            broken before the element is removed. If false, then the command will fail if the element is connected.

        """
        if not self.is_element:
            OpenMaya.MGlobal.displayError("Can't remove none element attribute")
            return
        cmds.removeMultiInstance(self.long_name, b=break_connections)

    @property
    def categories(self):
        return cmds.attributeQuery(
            self.name, node=self.node, categories=True) or []

    def has_category(self, category):
        fn_attr = OpenMaya.MFnAttribute(self.__plug__.attribute())
        return fn_attr.hasCategory(category)

    def add_category(self, category):
        if not self.has_category(category):
            cmds.addAttr(self.long_name, edit=True, category=category)

    # -----------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------
    def export(self, withConnection=True, isNested=False, ignore=None, filter=None):
        data = {}
        if self.is_writable:
            try:
                value = self.value
                if value is not None:
                    # Skip message attribute
                    data['value'] = value
            except NotImplementedError as e:
                # Some attributes should not be exported
                # By pass those attributes but continue fetching
                # connection information
                pass

        if withConnection:
            source = self.source
            if source:
                data['src'] = source.short_name
                source_with_conversion = self.sourceWithConversion
                if source_with_conversion.short_name != source.short_name:
                    unit_conversion = source_with_conversion.node
                    if unit_conversion.type_name == 'unitConversion':
                        try:
                            conversion_factor = unit_conversion.conversionFactor.value
                            data['unit_conversion'] = conversion_factor
                        except RuntimeError:
                            pass
            destinations = self.destinations
            if destinations:
                data['destinations'] = []
                destinations_with_conversion = self.destinationsWithConversions
                for dest, destConversion in zip(destinations, destinations_with_conversion):
                    dest_data = dict()
                    dest_data['dst'] = dest.short_name
                    if dest.short_name != destConversion.short_name:
                        unit_conversion = destConversion.node
                        if unit_conversion.type_name == 'unitConversion':
                            try:
                                conversion_factor = unit_conversion.conversionFactor.value
                                dest_data['unit_conversion'] = [conversion_factor]
                            except RuntimeError:
                                pass
                    data['destinations'].append(dest_data)

        # Only if the data is not empty we need to export it as an item
        if data:
            if self.is_element:
                data['index'] = self.index
            elif isNested:
                data['name'] = self.name.split('.')[-1]
            else:
                data['name'] = self.name

        return data

    # -----------------------------------------------------------------
    # Load
    # -----------------------------------------------------------------
    def load(self, data, makeConnections=True):
        value = data.get('value')
        if value is not None and self.is_writable\
                and not self.isConnected and self.is_free_to_change:
            self.value = value
        if makeConnections:
            source = data.get('src')
            if source and cmds.objExists(source) and not self.is_connected_to(source):
                source = Attribute(source)
                if source:
                    try:
                        source.connect(self, force=True)
                        unit_conversion = data.get('unit_conversion')
                        if unit_conversion is not None:
                            self.update_unit_conversion(unit_conversion)
                    except RuntimeError:
                        pass

            destinations = data.get('destinations')
            if destinations:
                for dest_data in destinations:
                    attr = dest_data.get('dst')
                    if attr and cmds.objExists(attr) and not self.is_connected_to(attr):
                        dest = Attribute(attr)
                        if dest:
                            try:
                                self.connect(dest, force=True)
                                unit_conversion = dest_data.get('unit_conversion')
                                if unit_conversion is not None:
                                    dest.update_unit_conversion(unit_conversion)
                            except RuntimeError:
                                pass

    def update_unit_conversion(self, factor):
        """

        Args:
            factor(float): Set the unit conversion factor attribute value

        """
        source = self.sourceWithConversion
        if source:
            source_node = source.node
            if source_node.type_name == "unitConversion":
                source_node.conversionFactor.value = factor


def get_plug_from_object_and_attr_name(obj, attr_name):
    """
    Get the MPlug instance of the attribute under an maya object
    Args:
        obj(DagNode or DependencyNode):
        attr_name(str): Attribute name

    Returns:
        MPlug

    """
    sel = OpenMaya.MSelectionList()

    plug = OpenMaya.MPlug()
    full_attr_name = obj.name + '.' + attr_name
    try:
        sel.add(full_attr_name)
        sel.getPlug(0, plug)
        if obj.object() != plug.node():
            raise MayaAttributeError(
                ('Attribute {} found on the shape node '
                 'instead of {}').format(attr_name, obj.name))
    except RuntimeError:
        raise MayaAttributeError(
            'Attribute {} not found.'.format(full_attr_name))
    return plug
