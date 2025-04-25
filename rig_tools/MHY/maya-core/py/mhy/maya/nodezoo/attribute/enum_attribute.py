from six import string_types

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.exceptions import MayaAttributeError
from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class EnumAttribute(Attribute):
    def _plug_value(self, time=None, timeUnit=OpenMaya.MTime.uiUnit()):
        if time:
            time_obj = OpenMaya.MTime(time, timeUnit)
            context = OpenMaya.MDGContext(time_obj)
        else:
            context = OpenMaya.MDGContext()
        return self.__plug__.asInt(context)

    @property
    def value(self):
        return self._plug_value()

    @property
    def enum_value(self):
        return self.enum_names[self.value]

    @property
    def enum_names(self):
        """Returns the enum name list."""
        enum = cmds.attributeQuery(self.name, node=self.node, listEnum=True)
        return enum[0].split(':')

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

        if not self.is_writable:
            return
        elif isinstance(val, string_types):
            val = str(val)
            enums = self.enum_names
            if val in enums:
                cmds.setAttr(self.long_name, enums.index(val))
            else:
                raise MayaAttributeError(
                    '{} does not contain enum name {}'.format(self.name, val))
        else:
            cmds.setAttr(self.long_name, int(val))
