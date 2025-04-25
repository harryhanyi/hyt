from maya import cmds, OpenMaya

import mhy.maya.maya_math as math
from mhy.maya.nodezoo.node import Node, DagNode


class NurbsSurface(DagNode):
    """
    Nurbs surface node class.
    """

    __NODETYPE__ = 'nurbsSurface'
    __FNCLS__ = OpenMaya.MFnNurbsSurface

    @classmethod
    def create(cls, *args, **kwargs):
        """Wrapper create function."""
        return cls._create_from_edges(*args, **kwargs)

    @classmethod
    def _create_from_edges(
            cls, edgeA, edgeB, name='surface', keep_history=True):
        """Creates a surface from 2 edges on a mesh.

        Args:
            edgeA (str): The first edge.
            edgeB (str): The second edge.
            name (str): Name of the surface transform node.
            keep_history (bool): If True, keep the loft node.

        Returns:
            NurbsSurface: The surface shape node.
        """
        result = cmds.loft(
            edgeA, edgeB, constructionHistory=keep_history, name=name,
            uniform=True, autoReverse=True,
            degree=1, sectionSpans=1, range=0, polygon=0,
            reverseSurfaceNormals=False)
        xform = Node(result[0])
        return xform.get_shapes()[0]

    @property
    def is_deformable(self):
        return True

    @property
    def max_u(self):
        """ Returns the max u param. """
        return self.get_attr('minMaxRangeU')[1]

    @property
    def max_v(self):
        """ Returns the max v param. """
        return self.get_attr('minMaxRangeV')[1]

    def point_at_param(self, param_u, param_v, is_normalized=False, as_tuple=True):
        """Returns the world position at the input uv parameters.

        Args:
            param_u (float): The parameter U value.
            param_v (float): The parameter V value.
            is_normalized (bool): If True, treat params as normalized params.
            as_tuple: (bool): If return data in tuple format. Otherwise, MPoint

        Returns:
            MPoint: point at the given param.
            tuple: point at the given param in tuple form.
        """
        point = OpenMaya.MPoint()
        if is_normalized:
            param_u *= self.max_u
            param_v *= self.max_v
        self.fn_node.getPointAtParam(
            param_u, param_v, point, OpenMaya.MSpace.kWorld)
        if as_tuple:
            return point[0], point[1], point[2]
        return point

    def closest_param(self, point):
        """
        Returns the closest uv parameters to the input position.

        Args:
            point (MPoint, MVector, tuple): A point to work with.

        Return:
            (double, double)
        """
        util_u = OpenMaya.MScriptUtil()
        util_u.createFromDouble(0)
        ptr_u = util_u.asDoublePtr()

        util_v = OpenMaya.MScriptUtil()
        util_v.createFromDouble(0)
        ptr_v = util_v.asDoublePtr()

        point = OpenMaya.MPoint(math.get_position(point))
        self.fn_node.closestPoint(point, ptr_u, ptr_v, False, 0.0001, OpenMaya.MSpace.kWorld)
        return util_u.getDouble(ptr_u), util_v.getDouble(ptr_v)

    def closest_point(self, point, as_tuple=True):
        """Returns the closest point on this surface to a given point.

        Args:
            point (MPoint, MVector, tuple): A point to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MPoint.

        Returns:
            MPoint: the closest point.
            tuple: the closest point in tuple form.
        """
        u, v = self.closest_param(point)
        return self.point_at_param(u, v, as_tuple=as_tuple)

    def closest_normal(self, point, as_tuple=True):
        """Returns the closest normal to a given position.

        Args:
            point (MPoint, MVector, tuple, or Transform): A point to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MVector

        Returns:
            MVector: closest normal
            tuple: closest normal in tuple form.
        """
        u, v = self.closest_param(point)
        normal = self.fn_node.normal(u, v, OpenMaya.MSpace.kWorld)
        if as_tuple:
            return normal[0], normal[1], normal[2]
        return normal

    def closest_tangent(self, point, as_tuple=True):
        """Returns the closest tangents to a given position.

        Args:
            point (MPoint, MVector, tuple, or Transform): A point to work with.
            as_tuple (bool): If True, return a tuple,
                otherwise return a MVector.

        Returns:
            (MVector, MVector): closest tangents.
            (tuple, tuple): closest tangents in tuple form.
        """
        tu = OpenMaya.MVector()
        tv = OpenMaya.MVector()
        u, v = self.closest_param(point)
        self.fn_node.getTangents(u, v, tu, tv, OpenMaya.MSpace.kWorld)
        if as_tuple:
            tu = tu[0], tu[1], tu[2]
            tv = tv[0], tv[1], tv[2]
        return tu, tv
