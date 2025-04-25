import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.exceptions import MayaAttributeError
from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class UnitAttribute(Attribute):
    @property
    def unit_type(self):
        attr = self.__plug__.attribute()
        fn_attr = OpenMaya.MFnUnitAttribute(attr)
        return fn_attr.unitType()

    def _plug_value(self, time=None, timeUnit=OpenMaya.MTime.uiUnit()):
        plug = self.__plug__
        if time:
            time_obj = OpenMaya.MTime(time, timeUnit)
            context = OpenMaya.MDGContext(time_obj)
        else:
            context = OpenMaya.MDGContext()
        unit_type = self.unit_type
        if unit_type == OpenMaya.MFnUnitAttribute.kDistance:
            return plug.asMDistance(context).value()
        elif unit_type == OpenMaya.MFnUnitAttribute.kAngle:
            angle = plug.asMAngle(context)
            return angle.asDegrees()
        elif unit_type == OpenMaya.MFnUnitAttribute.kTime:
            time = plug.asMTime(context)
            return time.value()
        else:
            raise NotImplementedError(
                "Not implementation has been made for given data type"
            )

    @property
    def value(self):
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
            cmds.setAttr(self.long_name, val)
