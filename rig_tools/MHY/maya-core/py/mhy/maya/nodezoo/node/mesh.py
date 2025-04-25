"""
This modules contains Mesh class and its api methods
"""
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.node import DagNode
import mhy.maya.nodezoo.utils as utils
import mhy.maya.maya_math as math


class Mesh(DagNode):
    __NODETYPE__ = 'mesh'
    __FNCLS__ = OpenMaya.MFnMesh

    class ComponentType(object):
        kVertex = 11
        kEdge = 12
        kFace = 13

    @classmethod
    def create(cls, vertex_positions, polygon_vertices, parent=None, name=None,
               uvs=None, assigned_uvs=None):
        mesh = OpenMaya.MFnMesh()
        num_vertices = len(vertex_positions)
        num_polygons = len(polygon_vertices)

        polygon_counts = OpenMaya.MIntArray()
        polygon_connects = OpenMaya.MIntArray()
        for i in polygon_vertices:
            polygon_counts.append(len(i))
            for j in i:
                polygon_connects.append(j)

        vertex_array = OpenMaya.MFloatPointArray()
        for p in vertex_positions:
            point = OpenMaya.MFloatPoint(p[0], p[1], p[2])
            vertex_array.append(point)

        if parent and cmds.objExists(parent):
            parent = DagNode(parent)

            obj = mesh.create(num_vertices, num_polygons,
                              vertex_array, polygon_counts,
                              polygon_connects, parent.object())
        else:
            obj = mesh.create(num_vertices, num_polygons,
                              vertex_array, polygon_counts,
                              polygon_connects)
        mesh = Mesh(obj)

        if mesh.type_name == 'transform':
            # mesh.create will return transform node if parent
            # object is not provided
            mesh = mesh.get_shapes(exact_type='mesh')
            if not mesh:
                OpenMaya.MGlobal.displayError("Failed to create mesh object")
                return
            mesh = mesh[0]
        if name:
            mesh.name = name

        if uvs and assigned_uvs:
            mesh.clear_uvs()
            mesh.set_uvs(*uvs)
            mesh.assign_uvs(*assigned_uvs)

        return mesh

    @property
    def vtx(self):
        """
        Get vertex component
        Returns:
            VertexComponent: Vertex Component instance
        """
        return VertexComponent(self)

    @property
    def e(self):
        """
        Get edge component
        Returns:
            EdgeComponent: Edge Component instance
        """
        return EdgeComponent(self)

    @property
    def f(self):
        """
        Get face component
        Returns:
            FaceComponent: Face Component instance
        """
        return FaceComponent(self)

    def destruct(self):
        """
        Delete the mesh shape node. If parent transform has no other children
        node, delete the parent transform as well

        """
        parent = self.get_parent()
        self.delete()
        if parent and not parent.get_children():
            parent.delete()

    def get_intermediate_sibling(self):
        """
        Get the intermediate object associated with this mesh node if exists
        Returns:
            Mesh: Intermediate mesh under the same parent transform node
            None: There's no intermediate sibling
        """
        transform = self.get_parent()
        if transform:
            for child in transform.get_children():
                if child.is_intermediate:
                    return child

    def get_current_uv_set(self):
        """
        Get the current uv set
        Returns:
            str: The name of current uv set
        """
        current = cmds.polyUVSet(self.name, currentUVSet=True, q=True)
        if current:
            return current[0]

    @property
    def is_deformable(self):
        return True

    def get_barycentric_coords(self, point):
        """
        Get the barycentric coordinates on this mesh from a world space point
        Args:
            point(MPoint):

        Returns:
            tuple: A tuple of vtx index and weight
        """
        mesh_intersector = OpenMaya.MMeshIntersector()
        point_info = OpenMaya.MPointOnMesh()
        mesh_intersector.create(self.object(), self.dag_path.exclusiveMatrix())
        u_util = OpenMaya.MScriptUtil(0.0)
        u_ptr = u_util.asFloatPtr()
        v_util = OpenMaya.MScriptUtil(0.0)
        v_ptr = v_util.asFloatPtr()
        dummy = OpenMaya.MScriptUtil()
        dummy_int_ptr = dummy.asIntPtr()
        mesh_intersector.getClosestPoint(point, point_info)
        point_info.getBarycentricCoords(u_ptr, v_ptr)
        u = u_util.getFloat(u_ptr)
        v = v_util.getFloat(v_ptr)
        w = 1 - u - v
        face_id = point_info.faceIndex()
        tri_id = point_info.triangleIndex()

        current_face = OpenMaya.MItMeshPolygon(self.dag_path)
        point_array = OpenMaya.MPointArray()
        vert_id_list = OpenMaya.MIntArray()
        current_face.setIndex(face_id, dummy_int_ptr)
        current_face.getTriangle(tri_id, point_array, vert_id_list, OpenMaya.MSpace.kWorld)
        return (vert_id_list[0], u), (vert_id_list[1], v), (vert_id_list[2], w)

    @property
    def num_polygons(self):
        """
        Returns the number of polygons for this mesh.

        Returns:
            int
        """
        return self.fn_node.numPolygons()

    @property
    def num_vertices(self):
        """
        Returns the number of vertices in the vertex list for this mesh.

        Returns:
            int
        """
        return self.fn_node.numVertices()

    @property
    def num_edges(self):
        """
        Returns the number of edges for this mesh.

        Returns:
            int
        """
        return self.fn_node.numEdges()

    @property
    def num_face_vertices(self):
        """
        Returns the number of face-vertices for this mesh.

        Returns:
            int
        """
        return self.fn_node.numFaceVertices()

    @property
    def polygon_vertices(self):
        """
        Query vertices indexes for all polygons in a list
        Returns:
        """
        num_polygon = self.num_polygons
        vtx_index_array = OpenMaya.MIntArray()
        polygon_vertices_list = []
        for i in range(num_polygon):
            self.fn_node.getPolygonVertices(i, vtx_index_array)
            index_list = []
            for j in range(vtx_index_array.length()):
                idx = vtx_index_array[j]
                index_list.append(idx)
            polygon_vertices_list.append(index_list)
        return polygon_vertices_list

    def get_points(self, space='world', as_list=True):
        """Returns the vertex points.

        Args:
            space (str): transform space in which to get the points.
            as_list (bool): If return points in a list

        Returns:
            MPointArray
        """
        points = OpenMaya.MPointArray()
        self.fn_node.getPoints(points, utils.get_space(space))
        if not as_list:
            return points
        num_points = points.length()
        result = []
        for i in range(num_points):
            pnt = [points[i].x, points[i].y, points[i].z]
            result.append(pnt)
        return result

    def set_points(self, points, space='world'):
        """Sets the vertex points
        TODO support undo

        Args:
            points (MPointArray): The points to set.
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
        self.fn_node.setPoints(point_array, utils.get_space(space))

    def get_vertex_normals(self, angle_weighted=False, space='world'):
        """Returns the averaged, vertex normal vectors.

        Args:
            angle_weighted (bool): If true, normals are computed by an average
                of surrounding face normals weighted by the angle subtended by
                the face at the vertex. (significantly slower)
                Otherwise, use a simple average of surround face normals.
            space (str): transform space in which to get the points.

        Returns:
            MFloatVectorArray
        """
        normals = OpenMaya.MFloatVectorArray()
        self.fn_node.getVertexNormals(
            angle_weighted, normals, utils.get_space(space))
        return normals

    def get_polygon_vertices(self, face_id):
        """Returns the vertex id lists associated with a given face.

        Args:
            face_id (int): A face index to work with.

        Returns:
            list: A list of vertex indices.
        """
        vert_ids = OpenMaya.MIntArray()
        self.fn_node.getPolygonVertices(face_id, vert_ids)
        return [vert_ids[i] for i in range(vert_ids.length())]

    # ------------------------------------------------------------------------
    # UV methods
    # ------------------------------------------------------------------------

    def get_uvs(self, uv_set=None):
        """

        Args:
            uv_set:

        Returns:

        """
        if uv_set is None:
            uv_set = self.get_current_uv_set()
            if not uv_set:
                return
        u_array = OpenMaya.MFloatArray()
        v_array = OpenMaya.MFloatArray()
        self.fn_node.getUVs(u_array, v_array, uv_set)
        u_list = []
        v_list = []
        for i in range(u_array.length()):
            u_list.append(u_array[i])
        for i in range(v_array.length()):
            v_list.append(v_array[i])
        return u_list, v_list

    def get_assigned_uvs(self, uv_set=None):
        """

        Args:
            uv_set:

        Returns:

        """
        if uv_set is None:
            uv_set = self.get_current_uv_set()
            if not uv_set:
                return
        uv_counts_array = OpenMaya.MIntArray()
        uv_ids_array = OpenMaya.MIntArray()
        self.fn_node.getAssignedUVs(uv_counts_array, uv_ids_array, uv_set)
        uv_counts_list = []
        uv_ids_list = []
        for i in range(uv_counts_array.length()):
            uv_counts_list.append(uv_counts_array[i])
        for i in range(uv_ids_array.length()):
            uv_ids_list.append(uv_ids_array[i])
        return uv_counts_list, uv_ids_list

    def clear_uvs(self, uv_set=None):
        """
        Clear the a specific uv_set if given; otherwise current uv_set will be deleted
        Args:
            uv_set(str): The name of uv set

        """
        if uv_set is None:
            uv_set = self.get_current_uv_set()
            if not uv_set:
                return
        self.fn_node.clearUVs(uv_set)

    def set_uvs(self, u_list, v_list, uv_set=None):
        """
        This method is used to create the texture coordinate table for the mesh.
        After the table is created, this assign_uvs is used to map those values to each polygon
        on a per-vertex basis. This method should be called before the assign_uvs method.
        Args:
            u_list:
            v_list:
            uv_set:

        Returns:

        """
        if uv_set is None:
            uv_set = self.get_current_uv_set()
            if not uv_set:
                return
        u_array = OpenMaya.MFloatArray()
        for u in u_list:
            u_array.append(u)
        v_array = OpenMaya.MFloatArray()
        for v in v_list:
            v_array.append(v)
        self.fn_node.setUVs(u_array, v_array, uv_set)

    def assign_uvs(self, uv_counts_list, uv_ids_list, uv_set=None):
        """
        The set_uvs method is used to create the texture coordinate table for the mesh.
        After the table is created, this method is used to map those values to each polygon
        on a per-vertex basis. The set_uvs method should be called before the this method.

        Args:
            uv_counts_list:
            uv_ids_list:
            uv_set:

        Returns:

        """
        if uv_set is None:
            uv_set = self.get_current_uv_set()
            if not uv_set:
                return
        uv_counts_array = OpenMaya.MIntArray()
        for u in uv_counts_list:
            uv_counts_array.append(u)
        uv_ids_array = OpenMaya.MIntArray()
        for v in uv_ids_list:
            uv_ids_array.append(v)
        self.fn_node.assignUVs(uv_counts_array, uv_ids_array, uv_set)

    def export_creation_data(self):
        data = {}
        vtx_array = OpenMaya.MFloatPointArray()
        self.fn_node.getPoints(vtx_array, OpenMaya.MSpace.kObject)
        vertex_positions = []
        for i in range(vtx_array.length()):
            vertex_positions.append([vtx_array[i].x, vtx_array[i].y, vtx_array[i].z])
        polygon_vertices = self.polygon_vertices

        parent = self.get_parent()
        data['vertex_positions'] = vertex_positions
        data['polygon_vertices'] = polygon_vertices
        current_uvs = self.get_uvs()
        assigned_uvs = self.get_assigned_uvs()
        if current_uvs:
            data['uvs'] = current_uvs
        if assigned_uvs:
            data['assigned_uvs'] = assigned_uvs
        if parent:
            data['parent'] = parent.name
        return data

    def get_vtx_association_with_distance(self, other_mesh):
        """

        This method get the vertex from this mesh association with another mesh
        by querying point position and barycentric coordinates.

        Args:
            other_mesh(Mesh):

        Returns:
            dict: A dictionary of association relations: key is the index of source
            vertex and value is a tuple of three vertex indexes and each respective
            weight


        """
        mesh_iter = OpenMaya.MItMeshVertex(self.dag_path)
        mesh_iter.reset()
        vertex_association = {}
        while not mesh_iter.isDone():
            pos = mesh_iter.position(OpenMaya.MSpace.kWorld)
            point = OpenMaya.MPoint(pos.x, pos.y, pos.z)
            (index_1, u), (index_2, v), (index_3, w) = other_mesh.get_barycentric_coords(point)
            vertex_association[mesh_iter.index()] = ((index_1, u), (index_2, v), (index_3, w))
            mesh_iter.next()
        return vertex_association

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
        # TODO
        raise NotImplementedError('point_at_param() is not implemented.')

    def closest_param(self, point, uv_set=None):
        """
        Returns the closest uv parameters to the input position.

        Args:
            point (MPoint, MVector, tuple): A point to work with.
            uv_set (str): The uv set to use. If None, use current uv set.

        Return:
            (double, double)
        """
        if not uv_set:
            uv_set = self.uvSet
        if not uv_set:
            return

        point = OpenMaya.MPoint(math.get_position(point))

        util_u = OpenMaya.MScriptUtil()
        util_u.createFromList([0.0, 0.0], 2)
        ptr = util_u.asFloat2Ptr()
        self.fn_node.getUVAtPoint(point, ptr, OpenMaya.MSpace.kWorld, uv_set)
        return (util_u.getFloat2ArrayItem(ptr, 0, 0),
                util_u.getFloat2ArrayItem(ptr, 0, 1))

    def closest_point(self, point, as_tuple=True):
        """Returns the closest point on this mesh to a given point.

        Args:
            point (MPoint, MVector, tuple): A point to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MPoint.

        Returns:
            MPoint: the closest point.
            tuple: the closest point in tuple form.
        """
        cpnt = OpenMaya.MPoint()
        point = OpenMaya.MPoint(math.get_position(point))
        self.fn_node.getClosestPoint(point, cpnt, OpenMaya.MSpace.kWorld)
        if as_tuple:
            return cpnt[0], cpnt[1], cpnt[2]
        return cpnt

    def closest_normal(self, point, as_tuple=True):
        """Returns the closest normal to a given position.

        Args:
            point (MPoint, MVector, tuple, or Transform): A point to work with.
            as_tuple (bool): If True, return a tuple, otherwise return MVector

        Returns:
            MVector: closest normal
            tuple: closest normal in tuple form.
        """
        normal = OpenMaya.MVector()
        cpnt = OpenMaya.MPoint()
        point = OpenMaya.MPoint(math.get_position(point))
        self.fn_node.getClosestPointAndNormal(
            point, cpnt, normal, OpenMaya.MSpace.kWorld)
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
        # TODO
        raise NotImplementedError('closest_tangent() is not implemented.')


class MeshComponent(object):
    short_name = ""

    def __init__(self, parent, _slice=None):
        self.parent = parent

        self.full_indices = range(self.parent.num_vertices)
        if _slice is not None:
            if isinstance(_slice, int):
                self.indices = [_slice]
            else:
                self.indices = self.full_indices[_slice]
        else:
            self.indices = self.full_indices[:]

    def __getitem__(self, key):
        return self.__class__(
            self.parent,
            _slice=key)

    def __repr__(self):
        if not self.indices:
            return '[]'
        first = self.indices[0]
        end = self.indices[-1]
        if first == end:
            slice_str = first
        else:
            slice_str = "{}:{}".format(first, end)
        return "{}.{}[{}]".format(self.parent.name, self.short_name, slice_str)

    def __len__(self):
        return len(self.indices)

    def get_position(self, space='object'):
        if not self.indices:
            return
        if space == "world":
            ws = True
        else:
            ws = False
        pos = cmds.xform("{}.{}[{}]".format(
            self.parent.name,
            self.short_name,
            self.indices[0]),
            query=True,
            translation=True,
            worldSpace=ws
        )
        return pos

    @property
    def name(self):
        return repr(self)


class VertexComponent(MeshComponent):
    short_name = 'vtx'


class EdgeComponent(MeshComponent):
    short_name = 'e'


class FaceComponent(MeshComponent):
    short_name = 'f'
