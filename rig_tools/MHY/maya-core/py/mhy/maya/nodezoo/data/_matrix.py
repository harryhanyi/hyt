import gorilla as gorilla

import maya.OpenMaya as OpenMaya

import mhy.python.core.utils as pyutil


@gorilla.patches(OpenMaya.MMatrix)
class MMatrix(object):

    @gorilla.filter(True)
    @gorilla.settings(allow_hit=True)
    def __init__(self, *args, **kwargs):
        """Override to allow initializing from a 1D python list."""
        org_init = gorilla.get_original_attribute(OpenMaya.MMatrix, '__init__')

        if args:
            values = pyutil.flatten_list(args)
            if len(values) == 16:
                util = OpenMaya.MScriptUtil()
                util.createFromList(values, 16)
                org_init(self, util.asFloat4Ptr())
                return

        org_init(self, *args, **kwargs)

    def as_tuple(self):
        """Converts to tuple."""
        flat_list = []
        for i in range(4):
            for j in range(4):
                flat_list.append(self(i, j))
        return tuple(flat_list)


@gorilla.patches(OpenMaya.MTransformationMatrix)
class MTransformationMatrix(object):

    @gorilla.filter(True)
    @gorilla.settings(allow_hit=True)
    def __init__(self, *args, **kwargs):
        """Override to allow initializing from a 1D python list."""
        org_init = gorilla.get_original_attribute(
            OpenMaya.MTransformationMatrix, '__init__')

        if args:
            values = pyutil.flatten_list(args)
            if len(values) == 16:
                util = OpenMaya.MScriptUtil()
                util.createFromList(values, 16)
                org_init(self, util.asFloat4Ptr())
                return

        org_init(self, *args, **kwargs)

    def as_tuple(self):
        """Converts to tuple."""
        flat_list = []
        mat = self.asMatrix()
        for i in range(4):
            for j in range(4):
                flat_list.append(mat(i, j))
        return tuple(flat_list)
