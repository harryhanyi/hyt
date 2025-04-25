from six import string_types
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class MatrixAttribute(Attribute):

    def _plug_value(self, time=None, timeUnit=OpenMaya.MTime.uiUnit()):
        plug = self.__plug__
        if time:
            timeObj = OpenMaya.MTime(time, timeUnit)
            context = OpenMaya.MDGContext(timeObj)
        else:
            context = OpenMaya.MDGContext()
        matrixObj = self.__plug__.asMObject(context)
        matrixData = OpenMaya.MFnMatrixData(matrixObj)
        matrix = matrixData.matrix()
        matrixList = []
        for i in range(4):
            for j in range(4):
                matrixList.append(matrix[i][j])
        return matrixList

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
        if not self.is_writable:
            return
        if isinstance(val, int):
            cmds.setAttr(self.long_name, val)
        elif isinstance(val, string_types):
            raise NotImplementedError('Not implemented yet')
