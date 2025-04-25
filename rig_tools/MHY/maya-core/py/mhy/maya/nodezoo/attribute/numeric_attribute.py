import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.exceptions import MayaAttributeError
from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class NumericAttribute(Attribute):

    MultiDataTypeMap = {
        OpenMaya.MFnNumericData.k2Short: 'short2',
        OpenMaya.MFnNumericData.k3Short: 'short3',
        OpenMaya.MFnNumericData.k2Int: 'long2',
        OpenMaya.MFnNumericData.k2Long: 'long2',
        OpenMaya.MFnNumericData.k3Int: 'long3',
        OpenMaya.MFnNumericData.k3Long: 'long3',
        OpenMaya.MFnNumericData.k2Double: 'double2',
        OpenMaya.MFnNumericData.k3Double: 'double3',
        OpenMaya.MFnNumericData.k4Double: 'double3',
        OpenMaya.MFnNumericData.k2Float: 'float2',
        OpenMaya.MFnNumericData.k3Float: 'float3'}

    @property
    def numeric_type(self):
        attr = self.__plug__.attribute()
        fn_attr = OpenMaya.MFnNumericAttribute(attr)
        return fn_attr.unitType()

    def _plug_value(self, time=None, timeUnit=OpenMaya.MTime.uiUnit()):
        plug = self.__plug__
        if time:
            time_obj = OpenMaya.MTime(time, timeUnit)
            context = OpenMaya.MDGContext(time_obj)
        else:
            context = OpenMaya.MDGContext()

        unit_type = self.numeric_type
        if unit_type == OpenMaya.MFnNumericData.kBoolean:
            return plug.asBool(context)
        elif unit_type == OpenMaya.MFnNumericData.kByte:
            return plug.asInt(context)
        elif unit_type == OpenMaya.MFnNumericData.kChar:
            return plug.asChar(context)
        elif unit_type == OpenMaya.MFnNumericData.kShort:
            return plug.asShort(context)
        elif unit_type in (
                OpenMaya.MFnNumericData.kInt,
                OpenMaya.MFnNumericData.kLong):
            return plug.asInt(context)
        elif unit_type == OpenMaya.MFnNumericData.kDouble:
            return plug.asDouble(context)
        elif unit_type == OpenMaya.MFnNumericData.kFloat:
            return plug.asFloat(context)
        elif unit_type in self.MultiDataTypeMap:
            val = []
            for i in range(self.num_children):
                val.append(self.child(i).value)
            return tuple(val)
        else:
            raise NotImplementedError(
                'No implementation for data type {}'.format(unit_type))

    @property
    def value(self):
        """
        Get the value of this plug
        Returns:

        """
        return self._plug_value()

    @value.setter
    def value(self, val):
        if not self.is_free_to_change:
            if self.sourceWithConversion:
                raise MayaAttributeError(
                    '{} has input connection and cannot be changed'.format(
                        self.short_name))
            if self.locked:
                raise MayaAttributeError(
                    '{} is locked and cannot be changed'.format(
                        self.short_name))

        if self.is_writable:
            multi_type = self.MultiDataTypeMap.get(self.numeric_type)
            if multi_type is None:
                cmds.setAttr(self.long_name, val)
            else:
                cmds.setAttr(self.long_name, *val, type=multi_type)

    @property
    def has_maximum_value(self):
        """
        Returns:
            bool: If this attribute has maximum value
        """
        node_name = self.node.name
        attr_name = self.name
        return cmds.attributeQuery(attr_name, node=node_name, maxExists=True)

    @property
    def maximum_value(self):
        """
        Get the maximum value if exists. otherwise None is returned
        Returns:
            int: Maximum value in integer
            float: Maximum value in float
            None: This attribute has no maximum value
        """
        node_name = self.node.name
        attr_name = self.name
        if cmds.attributeQuery(attr_name, node=node_name, maxExists=True):
            return cmds.attributeQuery(attr_name, node=node_name, maximum=True)[0]

    @property
    def has_minimum_value(self):
        """
        Returns:
            bool: If this attribute has minimum value
        """
        node_name = self.node.name
        attr_name = self.name
        return cmds.attributeQuery(attr_name, node=node_name, minExists=True)

    @property
    def minimum_value(self):
        """
        Get the minimum value if exists. otherwise None is returned
        Returns:
            int: Minimum value in integer
            float: Minimum value in float
            None: This attribute has no minimum value
        """
        node_name = self.node.name
        attr_name = self.name
        if cmds.attributeQuery(attr_name, node=node_name, minExists=True):
            return cmds.attributeQuery(attr_name, node=node_name, minimum=True)[0]

    @property
    def has_soft_maximum_value(self):
        """
        Returns:
            bool: If this attribute has soft maximum value
        """
        node_name = self.node.name
        attr_name = self.name
        return cmds.attributeQuery(attr_name, node=node_name, softMaxExists=True)

    @property
    def soft_maximum_value(self):
        """
        Get the soft maximum value if exists. otherwise None is returned
        Returns:
            int: Soft maximum value in integer
            float: Soft maximum value in float
            None: This attribute has no soft maximum value
        """
        node_name = self.node.name
        attr_name = self.name
        if cmds.attributeQuery(attr_name, node=node_name, softMaxExists=True):
            return cmds.attributeQuery(attr_name, node=node_name, softMaximum=True)[0]

    @property
    def has_soft_minimum_value(self):
        """
        Returns:
            bool: If this attribute has soft minimum value
        """
        node_name = self.node.name
        attr_name = self.name
        return cmds.attributeQuery(attr_name, node=node_name, softMinExists=True)

    @property
    def soft_minimum_value(self):
        """
        Get the minimum value if exists. otherwise None is returned
        Returns:
            int: soft minimum value in integer
            float: soft minimum value in float
            None: This attribute has no soft minimum value
        """
        node_name = self.node.name
        attr_name = self.name
        if cmds.attributeQuery(attr_name, node=node_name, softMinExists=True):
            return cmds.attributeQuery(attr_name, node=node_name, softMin=True)[0]
