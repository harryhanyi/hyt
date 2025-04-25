"""
NurbsCurve node class
"""
from maya import cmds, OpenMaya

import mhy.maya.maya_math as math
from mhy.maya.nodezoo.node import Node, DagNode
import mhy.maya.nodezoo.utils as utils


def _get_open_knots(point_num, degree):
    """
    Returns a open curve knot list.
    Args:
        point_num(int):  Point numbers
        degree(int): Degree of the curve

    Returns:
        list: Get a list of index integers

    """

    knots = []
    n_knot_max = point_num - degree
    for i in range(degree - 1):
        knots.append(0)
    for i in range(n_knot_max + 1):
        knots.append(i)
    for i in range(degree - 1):
        knots.append(n_knot_max)
    return knots


def _get_closed_knots(point_num, degree):
    """
    Get closed knots
    Args:
        point_num(int):  Point numbers
        degree(int): Degree of the curve

    Returns:
        list: Get a list of index integers

    """
    knots = []
    for i in range(degree - 1):
        knots.append(-degree + 1 + i)
    for i in range(point_num + 1):
        knots.append(i)
    for i in range(degree - 1):
        knots.append(point_num + 1 + i)
    return knots


class NurbsCurve(DagNode):
    """
    Nurbs curve class.

    """

    __NODETYPE__ = 'nurbsCurve'
    __FNCLS__ = OpenMaya.MFnNurbsCurve

    @classmethod
    def create(cls, *args, **kwargs):
        """Wrapper create function."""
        if len(args) == 1:
            return cls._create_from_points(*args, **kwargs)
        else:
            return cls._create_from_surface(*args, **kwargs)

    @classmethod
    def _create_from_points(
            cls, points, name='curve',
            degree=1, spans=None,
            periodic=False, uniform=True,
            knot=None, rebuild=False,
            returnShape=False):
        """Creates a curve from a list of points.

        Args:
            points (list or MPointArray): A list of transform nodes
                or point positions.
            name (str): Name of the curve transform node.
            degree (int): Degree of the curve.
            periodic (bool): Use periodic form?
            uniform (bool): Rebuild the result curve to make it uniform?
            knot (list or MDoubleArray): Curve knots.
                If None, use a default knot list.

        Returns:
            NurbsCurve: The curve shape node.
        """
        # get cv positions as a list of lists
        if not isinstance(points, (list, tuple)):
            points = [(points[i][0], points[i][1], points[i][2])
                      for i in points.length()]
        else:
            pgen = [math.get_position(p) for p in points]
            points = [(p.x, p.y, p.z) for p in pgen]

        # create curve shape
        length = len(points)
        if not knot:
            if periodic:
                length = length - degree
                knot = _get_closed_knots(length, degree)
            else:
                knot = _get_open_knots(length, degree)

        xform = Node(cmds.curve(
            degree=degree, point=points, knot=knot, periodic=periodic))
        xform.name = name

        # uniform rebuild
        if not spans:
            spans = length-1
        if rebuild:
            cmds.rebuildCurve(
                xform, constructionHistory=False, replaceOriginal=True,
                rebuildType=0, endKnots=1, keepEndPoints=True, keepRange=0,
                keepControlPoints=False, keepTangents=True,
                spans=spans, degree=3)

        if returnShape:
            return xform.get_shapes()[0]
        else:
            return xform

    @classmethod
    def _create_from_surface(
            cls, surface, uv_list, is_normalized=False, underworld=False,
            name='curve', degree=3, periodic=False, uniform=False, knot=None):
        """Creates a curve from a set of uvs on a surface.

        Args:
            surface (str): A surface to create the curve from.
            uv_list (list): A list of uvs to create the curve from.
            is_normalized (bool): If True, treat uvs as normalized uvs.
            underworld (bool): If True, build the curve in the underworld
                via cmds.curveOnSurface().
            name (str): Name of the curve transform node.
            degree (int): Degree of the curve.
            periodic (bool): Use periodic form?
            uniform (bool): Rebuild the result curve to make it uniform?
            knot (list or MDoubleArray): Curve knots.
                If None, use a default knot list.
            rebuild (bool): post rebuild the created curve on surface
            rebuildDegree (int): the degree of the rebuild curve.

        Return:
            NurbsCurve: The curve shape node.
        """
        # get surface shape
        shape = Node(surface)
        shape = shape.get_shapes(type_='nurbsSurface')
        if shape:
            shape = shape[0]
        else:
            raise ValueError('Invalid surface: {}'.formrat(surface))

        # create curve based on surface point in world space
        if not underworld:
            points = [shape.point_at_param(x, y, is_normalized=is_normalized)
                      for x, y in uv_list]
            length = len(points)
            return cls._create_from_points(
                points, name=name, degree=degree, periodic=periodic,
                uniform=uniform, knot=knot)

        else:
            length = len(uv_list)
            if not knot:
                if periodic:
                    length = length - degree
                    knot = _get_closed_knots(length, degree)
                else:
                    knot = _get_open_knots(length, degree)

            xform = cmds.curveOnSurface(
                shape,
                name=name,
                degree=degree,
                knot=knot,
                periodic=periodic,
                positionUV=tuple(uv_list))

            # uniform rebuild
            if uniform and degree > 1:
                cmds.rebuildCurve(
                    xform, constructionHistory=False, replaceOriginal=True,
                    rebuildType=0, endKnots=1, keepEndPoints=True, keepRange=0,
                    keepControlPoints=False, keepTangents=True,
                    spans=length-1, degree=degree)

            return Node(xform).get_shapes()[0]

    def rebuild(self, *args, **kwargs):
        """Rebuilds this curve.

        This function wrap cmds.rebuildCurve().

        Returns:
            [NurbsCurve]: This curve. (If replaceOriginal is True)
            [NurbsCurve]: The new curve. (if constructionHistory is False)
            [NurbsCurve, rebuildCurve]: The new curve and the rebuildCurve node.
                (if constructionHistory is True)
        """
        nodes = [Node(n) for n in cmds.rebuildCurve(self.name, *args, **kwargs)]
        for i, node in enumerate(nodes):
            if node.type_name == 'transform':
                node.sync_shape_name()
                nodes[i] = node.get_shapes()[0]
        return nodes

    def duplicate_curve(self, *args, **kwargs):
        """Duplicates this curve.

        This function wrap cmds.duplicateCurve().

        Returns:
            NurbsCurve: The duplicated curve object.
            [NurbsCurve, duplicateCurve]: The duplicateCurve curve and the
                duplicateCurve node. (if constructionHistory is True)
        """
        nodes = [Node(n) for n in
                 cmds.duplicateCurve(self.get_parent(), *args, **kwargs)]
        for i, node in enumerate(nodes):
            if node.type_name == 'transform':
                node.sync_shape_name()
                nodes[i] = node.get_shapes()[0]
        return nodes

    @property
    def is_deformable(self):
        return True

    @property
    def max_param(self):
        """ Returns the max param. """
        return self.maxValue.value

    def get_points(self, space='world', as_list=True):
        """Returns the CV points.

        Args:
            space (str): transform space in which to get the points.
            as_list (bool): If return points as a list
        Returns:
            MPointArray: If as_list is False
            list: If as_list is True
        """
        points = OpenMaya.MPointArray()
        self.fn_node.getCVs(points, utils.get_space(space))
        if not as_list:
            return points
        num_points = points.length()
        result = []
        for i in range(num_points):
            pnt = [points[i].x, points[i].y, points[i].z]
            result.append(pnt)
        return result

    def set_points(self, points, space='world'):
        """Sets the CV points
        TODO support undo

        Args:
            points (list or MPointArray): The points to set.
            space (str): transform space in which to set the points.

        Returns:
            None
        """
        if isinstance(points, (list, tuple)):
            point_array = OpenMaya.MPointArray()
            for each in points:
                point_array.append(OpenMaya.MPoint(*each))
        else:
            point_array = points
        self.fn_node.setCVs(point_array, utils.get_space(space))

    def closest_point(self, point, as_tuple=True):
        """Returns the closest point from a given point to this curve.

        Args:
            point (str, Node, list, MVector): A node or a vector to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MPoint.

        Returns:
            MPoint: the closest point.
            tuple: the closest point in tuple form.
        """
        point = OpenMaya.MPoint(math.get_position(point))
        point = self.fn_node.closestPoint(
            point, None, 0.0001, OpenMaya.MSpace.kWorld)
        if as_tuple:
            return point[0], point[1], point[2]
        return point

    def closest_param(self, point):
        """Returns the closest parameter from a given point to this curve.

        Args:
            point (str, Node, list, MVector): A node or a vector to work with.

        Returns:
            folat: the parameter.
        """
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(0.0)
        ptr = util.asDoublePtr()
        point = OpenMaya.MPoint(math.get_position(point))
        self.fn_node.closestPoint(point, ptr, 0.0001, OpenMaya.MSpace.kWorld)
        return util.getDouble(ptr)

    def closest_normal(self, point, as_tuple=True):
        """Returns the closest normal to a given position.

        Args:
            point (MPoint, MVector, tuple, or Transform): A point to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MVector

        Returns:
            MVector: closest normal
            tuple: closest normal in tuple form.
        """
        normal = self.fn_node.normal(
            self.closest_param(point), OpenMaya.MSpace.kWorld)
        if as_tuple:
            return normal[0], normal[1], normal[2]
        return normal

    def closest_tangent(self, point, as_tuple=True):
        """Returns the closest tangent to a given position.

        Args:
            point (MPoint, MVector, tuple, or Transform): A point to work with.
            as_tuple (bool): If True, return a tuple,
                otherwise return a MVector.

        Returns:
            MVector: closest tangent
            tuple: closest tangent in tuple form.
        """
        tangent = self.fn_node.tangent(
            self.closest_param(point), OpenMaya.MSpace.kWorld)
        if as_tuple:
            return tangent[0], tangent[1], tangent[2]
        return tangent

    def point_at_param(self, param, is_normalized=False, as_tuple=True):
        """Returns the world position at a input parameter.

        Args:
            param (float): The parameter value.
            is_normalized (bool): If True, treat params as normalized params.

        Returns:
            MPoint: point at the given param.
            tuple: point at the given param in tuple form.
        """
        point = OpenMaya.MPoint()
        if is_normalized:
            param *= self.max_param
        self.fn_node.getPointAtParam(param, point, OpenMaya.MSpace.kWorld)
        if as_tuple:
            return (point[0], point[1], point[2])
        return point
