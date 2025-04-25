kMObjectStr = 'MObject'
kMObjectHandleStr = 'MObjectHandle'
kMDagPathStr = 'MDagPath'
kMFnNodeStr = 'MFn'

nodezoo_tag_attr = 'nodezoo_custom_type'
nodezoo_mm_attr = 'nodezoo_marking_menu'


class DataFormat(object):
    # Will register more data format here
    kJson = 'json'


class SurfaceAssociation(object):

    vertex_id = 'vertexId'
    closest_point = 'closestPoint'
    ray_cast = 'rayCast'
    closest_component = 'closestComponent'
    uv = 'uv_space'

    @classmethod
    def items(cls):
        return (
            cls.vertex_id,
            cls.closest_point,
            cls.ray_cast,
            cls.closest_component,
            cls.uv
        )
