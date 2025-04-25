"""
Typed attribute class
"""

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.attribute.attribute_ import Attribute, MayaAttributeError


class TypedAttribute(Attribute):
    ArrayDataTypeMap = {
        OpenMaya.MFnData.kDoubleArray: 'doubleArray',
        OpenMaya.MFnData.kIntArray: 'Int32Array',
        OpenMaya.MFnData.kPointArray: 'pointArray',
        OpenMaya.MFnData.kVectorArray: 'vectorArray',
        OpenMaya.MFnData.kStringArray: 'stringArray',
        OpenMaya.MFnData.kComponentList: 'componentList'
    }
    OtherDataTypeMap = {
        OpenMaya.MFnData.kMatrix: 'matrix',
        OpenMaya.MFnData.kString: 'string'
    }

    @property
    def attr_type(self):
        """
        Get the attribute type
        Returns:
            OpenMaya.MFnData
        """
        attr = self.__plug__.attribute()
        fn_attr = OpenMaya.MFnTypedAttribute(attr)
        return fn_attr.attrType()

    def _plug_value(self, time=None, timeUnit=OpenMaya.MTime.uiUnit()):
        plug = self.__plug__
        if time:
            time_obj = OpenMaya.MTime(time, timeUnit)
            context = OpenMaya.MDGContext(time_obj)
        else:
            context = OpenMaya.MDGContext()

        attr_type = self.attr_type

        if attr_type == OpenMaya.MFnData.kMatrix:
            try:
                matrix_obj = plug.asMObject(context)
            except RuntimeError as e:
                # In case run into a maya bug that failed to query matrix plug
                return get_val_from_cmd(self.long_name, time)
            matrix_data = OpenMaya.MFnMatrixData(matrix_obj)
            matrix = matrix_data.matrix()
            matrix_list = []
            for i in range(4):
                for j in range(4):
                    matrix_list.append(matrix(i, j))
            return tuple(matrix_list)
        elif attr_type == OpenMaya.MFnData.kString:
            return plug.asString(context)

        elif attr_type == OpenMaya.MFnData.kDoubleArray:
            try:
                obj = plug.asMObject(context)
            except RuntimeError:
                return get_val_from_cmd(self.long_name, time)
            double_array_data = OpenMaya.MFnDoubleArrayData(obj)
            return list(double_array_data.array())

        elif attr_type == OpenMaya.MFnData.kIntArray:
            try:
                obj = plug.asMObject(context)
            except RuntimeError:
                return get_val_from_cmd(self.long_name, time)
            double_array_data = OpenMaya.MFnIntArrayData(obj)
            return list(double_array_data.array())

        elif attr_type == OpenMaya.MFnData.kVectorArray:
            try:
                obj = plug.asMObject(context)
            except RuntimeError:
                return get_val_from_cmd(self.long_name, time)
            vector_array_data = OpenMaya.MFnVectorArrayData(obj)
            vector_array = vector_array_data.array()
            vectors = []
            for i in range(vector_array.length()):
                vectors.append((vector_array[i].x, vector_array[i].y, vector_array[i].z))
            return vectors

        elif attr_type == OpenMaya.MFnData.kPointArray:
            try:
                obj = plug.asMObject(context)
            except RuntimeError:
                return get_val_from_cmd(self.long_name, time)
            point_array_data = OpenMaya.MFnPointArrayData(obj)
            point_array = point_array_data.array()
            points = []
            for i in range(point_array.length()):
                points.append((point_array[i].x, point_array[i].y, point_array[i].z, 1.0))
            return points

        elif attr_type == OpenMaya.MFnData.kStringArray:
            try:
                obj = plug.asMObject(context)
            except RuntimeError:
                return get_val_from_cmd(self.long_name, time)
            string_array_data = OpenMaya.MFnStringArrayData(obj)
            return list(string_array_data.array())

        elif attr_type == OpenMaya.MFnData.kComponentList:
            data = get_val_from_cmd(self.long_name, time)
            if data:
                data = [str(i) for i in data]
            return data

        elif attr_type == OpenMaya.MFnData.kAny:
            return get_val_from_cmd(self.long_name, time)

        else:
            OpenMaya.MGlobal.displayWarning(
                'No implementation for data type {} on '
                'attribute {}'.format(attr_type, self.short_name))

    @property
    def value(self):
        """

        Returns:

        """
        return self._plug_value()

    @value.setter
    def value(self, val):
        """
        Value setter for typed attribute. This method will check attr_type
        first using MFnAttribute api and then call maya.cmds.setAttr with correct type arguments.
        Args:
            val:

        """
        if not self.is_free_to_change:
            if self.sourceWithConversion:
                raise MayaAttributeError(
                    '{} has input connection and cannot be changed'.format(
                        self.short_name))
            if self.locked:
                raise MayaAttributeError(
                    '{} is locked and cannot be changed'.format(
                        self.short_name))

        if val is None or not self.is_writable:
            return

        attr_type = self.attr_type
        if attr_type in TypedAttribute.ArrayDataTypeMap:
            cmds.setAttr(self.long_name, len(val), *val, type=TypedAttribute.ArrayDataTypeMap[self.attr_type])
        elif attr_type in TypedAttribute.OtherDataTypeMap:
            cmds.setAttr(self.long_name, val, type=TypedAttribute.OtherDataTypeMap[self.attr_type])
        elif attr_type == OpenMaya.MFnData.kAny:
            cmds.setAttr(self.long_name, val)
        else:
            cmds.error(
                'set value for {} is not supported'.format(self.short_name))


def get_val_from_cmd(attr_name, time=None):
    """
    Get value with maya.cmds.getAttr with time context or without
    Args:
        attr_name(str): The name of attribute
        time(float): time

    Returns:

    """
    if time:
        return cmds.getAttr(attr_name, time=time)
    else:
        return cmds.getAttr(attr_name)
