RIG_ROOT = 'RIG'
MARKER_ROOT = 'MARKER'
WS_NODE = 'WORLDSPACE'
RIG_SKEL_ROOT = 'RIG_SKELETON'
BIND_SKEL_ROOT = 'BIND_SKELETON'
ROOT_JOINT = 'worldOffset_M_RIGJNT'
LIMB_ROOT = 'LIMB'
RIGMESH_ROOT = 'RIG_MESH'
MESH_ROOT = 'MESH'
HEADMESH_ROOT = 'HEAD_MESH'
BODYMESH_ROOT = 'BODY_MESH'
TARGETMESH_ROOT = 'TARGET_MESH'
BLENDMESH_ROOT = 'BLEND_MESH'

MH_ROOT = 'METAHUMAN'
MH_BLEND_FACE_MESH = 'FACE_MH_00_M_MESH'
MH_BLEND_TEETH_MESH = 'TEETH_MH_00_M_MESH'
MH_BLEND_EYE_MESHES = ["EYE_MH_00_L_MESH", "EYE_MH_00_R_MESH"]

POSE_MESH_MSG_ATTR = 'POSE_BASE_MESH'
POSE_DRIVEN_ATTR = 'poseDrivenAttributes'

EXT_BIND_JOINT = 'JNT'
EXT_RIG_JOINT = 'RIGJNT'
ATTR_BIND_JOINT = 'bind_joint'
ATTR_BIND_PARENT = 'bind_parent'

EXT_MARKER_ROOT = 'MROOT'
EXT_MARKER = 'MARKER'
EXT_MARKER_HIER_CTRL = 'HCTRL'
EXT_MARKER_UP_CTRL = 'UPCTRL'

RIG_MM_NAME = 'mhy_rig_marking_menu'
MARKER_MM_NAME = 'mhy_marker_marking_menu'

ROT_ORDERS = ('xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx')

COLOR_L = (0, 0, 1)
COLOR_R = (1, 0, 0)
COLOR_M = (1, 1, 0)




class InputSkelType(object):

    single_joint = 'single_joint'
    single_chain = 'single_chain'
    multi_chain = 'multi_chain'

    @classmethod
    def items(cls):
        return (
            cls.single_joint,
            cls.single_chain,
            cls.multi_chain)


class MarkerConnectMode(object):

    # connect only
    none = 'none'
    # connect + parent follow child
    follow = 'follow'
    # connect + parent aim at child
    aim = 'aim'

    @classmethod
    def items(cls):
        return ('none', 'follow', 'aim')
