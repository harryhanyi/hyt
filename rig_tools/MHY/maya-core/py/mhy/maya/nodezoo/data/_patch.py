import sys

from maya import OpenMaya

import gorilla as gorilla

from . import _matrix


@gorilla.patch(OpenMaya.MVector, name='__setitem__')
@gorilla.patch(OpenMaya.MFloatVector, name='__setitem__')
@gorilla.patch(OpenMaya.MPoint, name='__setitem__')
@gorilla.patch(OpenMaya.MFloatPoint, name='__setitem__')
def setitemxyz(self, i, val):
    """ Sets item by index. """
    if i == 0:
        self.x = val
    elif i == 1:
        self.y = val
    elif i == 2:
        self.z = val
    else:
        raise ValueError('Invalid index {}'.format(i))


@gorilla.patch(OpenMaya.MColor, name='__setitem__')
def setitemrgb(self, i, val):
    """ Sets item by index. """
    if i == 0:
        self.r = val
    elif i == 1:
        self.g = val
    elif i == 2:
        self.b = val
    else:
        raise ValueError('Invalid index {}'.format(i))


@gorilla.patch(OpenMaya.MVector, name='__radd__')
@gorilla.patch(OpenMaya.MFloatVector, name='__radd__')
@gorilla.patch(OpenMaya.MPoint, name='__radd__')
@gorilla.patch(OpenMaya.MFloatPoint, name='__radd__')
@gorilla.patch(OpenMaya.MColor, name='__radd__')
def radd(self, other):
    """ Enables reverse add. """
    if isinstance(other, int) and other == 0:
        return self
    else:
        return self.__add__(other)


@gorilla.patch(OpenMaya.MVector, name='as_tuple')
@gorilla.patch(OpenMaya.MFloatVector, name='as_tuple')
def as_tuple_3(self):
    """Converts to tuple."""
    out_list = []
    for i in range(3):
        out_list.append(self[i])
    return tuple(out_list)


@gorilla.patch(OpenMaya.MPoint, name='as_tuple')
@gorilla.patch(OpenMaya.MFloatPoint, name='as_tuple')
@gorilla.patch(OpenMaya.MColor, name='as_tuple')
def as_tuple_4(self):
    """Converts to tuple."""
    out_list = []
    for i in range(4):
        out_list.append(self[i])
    return tuple(out_list)


# apply patches
patches = gorilla.find_patches([sys.modules[__name__], _matrix])
for patch in patches:
    gorilla.apply(patch)
