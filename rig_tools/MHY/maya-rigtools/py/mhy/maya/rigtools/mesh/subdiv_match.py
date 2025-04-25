from maya.api import OpenMaya
from maya import cmds
import mhy.python.core.logger as logger


def has_intersect(list_0, list_1):
    """
    Check two lists contain the common element.
    """
    for item in list_0:
        if item in list_1:
            return True
    return False


def _get_diagonal_vertex(vertex_it, pre_index, current_index):
    """
    Get vertex index doesn't share any faces with pre_index.
    both pre_index and diagonal_index connect to current_index
    """
    vertex_it.setIndex(pre_index)
    exclude_faces = vertex_it.getConnectedFaces()
    vertex_it.setIndex(current_index)
    neighor_indices = vertex_it.getConnectedVertices()
    for diagonal_index in neighor_indices:
        if pre_index == diagonal_index:
            continue
        vertex_it.setIndex(diagonal_index)
        connected_faces = vertex_it.getConnectedFaces()
        if not has_intersect(connected_faces, exclude_faces):
            return diagonal_index
    return None


def _get_edge_vertices_along(vertex_it, src_index, dir_index, edge_num):
    """
    Get the vertices on the edges along the direction from src_index to dir_index.
    """
    edge_vertices = [src_index, dir_index]
    vertex_it.setIndex(src_index)
    neighor_indices = vertex_it.getConnectedVertices()
    vertex_it.setIndex(dir_index)
    for i in range(edge_num-1):
        if dir_index is None:
            return None
        next_index = _get_diagonal_vertex(vertex_it, src_index, dir_index)
        src_index = dir_index
        dir_index = next_index
        edge_vertices.append(next_index)
    return edge_vertices


def _get_edge_vertices_between(vertex_it, src_index, dir_index, edge_num=4):
    """
    Get the vertices on the edges between src_index and dir_index.
    """
    vertex_it.setIndex(src_index)
    neighor_indices = vertex_it.getConnectedVertices()
    for vertex_index in neighor_indices:
        edge_vertices = _get_edge_vertices_along(
            vertex_it, src_index, vertex_index, edge_num)
        if edge_vertices and edge_vertices[-1] == dir_index:
            return edge_vertices
    return None


def _get_subdiv_face_vertices(vertex_it, vertices, subdiv_level):
    """
    Get the high level subdiv vertices corresponding to a low level polygon face.
    vertices store the four corner of the low level polygon.
    """
    edge_num = 1 << subdiv_level
    left_edge = _get_edge_vertices_between(vertex_it, vertices[0], vertices[3])
    right_edge = _get_edge_vertices_between(
        vertex_it, vertices[1], vertices[2])
    row_number = len(left_edge)
    if row_number != len(right_edge):
        return None
    patch_indices = []
    for row_id in range(row_number):
        row = _get_edge_vertices_between(
            vertex_it, left_edge[row_id], right_edge[row_id], edge_num)
        patch_indices.append(row)
    return patch_indices


def _get_dag(name):
    """
    convenient function to get dagPath from name.
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(name)
    return selection_list.getDagPath(0)


def get_subdiv_level(hi, lo):
    """
    compute the subdiv level from the high and low mesh's polygon number.
    """
    if hi <= lo:
        logger.error("get_subdiv_level failed. low-res mesh has same or higher subdiv level than low-res mesh.")
    level = 0
    value = hi
    while value > lo:
        value = value >> 1
        level += 1
    if (lo << level) == hi:
        return level/2
    return -1


def _get_subdiv_topology_map(base_mesh, hi_mesh):
    """
    Get the each low level polygon faces' corresponding face vertices.
    """
    component = OpenMaya.MObject()
    base_face_it = OpenMaya.MItMeshPolygon(base_mesh, component)
    hi_face_it = OpenMaya.MItMeshPolygon(hi_mesh, component)
    subdiv_level = get_subdiv_level(hi_face_it.count(), base_face_it.count())
    hi_vertex_it = OpenMaya.MItMeshVertex(hi_mesh, component)
    it_num = 0
    subdiv_map = []
    sud_vertices_num = (1<<subdiv_level)+1
    while not base_face_it.isDone():
        it_num += 1
        vertices = base_face_it.getVertices()
        sub_vertices = _get_subdiv_face_vertices(
            hi_vertex_it, vertices, subdiv_level=subdiv_level)
        subdiv_map.append(sub_vertices)
        if len(sub_vertices) != sud_vertices_num:
            logger.error('reverse subdiv failed, expect {} vertices on one edge, get {} vertices!'.format(sud_vertices_num, len(sub_vertices)))
            return None
        base_face_it.next()
    return subdiv_map


def create_match_mesh(base_mesh, hi_mesh, out_mesh=None, subdiv_type=2):
    """
    Create a subdiv mesh from the low level mesh and copy vertices position from high level mesh.
    Args:
            base_mesh (str): The name of low resolution mesh.
            hi_mesh (str): The name of high resolution mesh.
            out_mesh (str): The name for new created mesh.
            subdiv_type (int): The subdivision type is used in polySmooth. Default to 2(OpenSubdiv).
                subdiv_type is pass to cmds.polySommoth.
                MAYA document about subdivisionType is completely wrong.
                The truth is
                0: Maya Catmull-Clark
                1: ?, Something completely different subdivision topology.
                2: OpenSubdiv Catmull-Clark
    """
    base_dag = _get_dag(base_mesh)
    base_mesh_fn = OpenMaya.MFnMesh(base_dag)
    hi_dag = _get_dag(hi_mesh)
    hi_mesh_fn = OpenMaya.MFnMesh(hi_dag)
    hi_points = hi_mesh_fn.getPoints()
    base_face_num = base_mesh_fn.numPolygons
    hi_face_num = hi_mesh_fn.numPolygons
    subdiv_level = get_subdiv_level(hi_face_num, base_face_num)
    if subdiv_level <= 0:
        logger.error("The high-res mesh shoud be the the catmull subdiv of low-res mesh!")
        return False
    subdiv_mesh = out_mesh
    if out_mesh is None:
        subdiv_mesh = cmds.duplicate(base_mesh)[0]
    else:
        subdiv_mesh = cmds.duplicate(base_mesh, name=out_mesh)[0]
    cmds.polySmooth(subdiv_mesh, subdivisionType=subdiv_type,
                    divisions=subdiv_level)
    subdiv_dag = _get_dag(subdiv_mesh)
    subdiv_mesh_fn = OpenMaya.MFnMesh(subdiv_dag)
    subdiv_points = subdiv_mesh_fn.getPoints()
    base_hi_map = _get_subdiv_topology_map(base_dag, hi_dag)
    base_sub_map = _get_subdiv_topology_map(base_dag, subdiv_dag)
    if base_sub_map is None or base_hi_map is None:
        return False
    vertices_number_per_polygon = (1 << subdiv_level)+1
    for face_id in range(base_face_num):
        base_sub_face = base_sub_map[face_id]
        base_hi_face = base_hi_map[face_id]
        for row in range(vertices_number_per_polygon):
            base_sub_row = base_sub_face[row]
            base_hi_row = base_hi_face[row]
            for col in range(vertices_number_per_polygon):
                subdiv_points[base_sub_row[col]] = hi_points[base_hi_row[col]]
    subdiv_mesh_fn.setPoints(subdiv_points)
    return True
