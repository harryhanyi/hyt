import os
import maya.mel as mel
import mhy.python.core.logger as logger


CHAR_DIR_LIST = (
    'assets',
    'autosave',
    'camera',
    'data',
    'movies',
    'scenes',
    'scripts',
    'sourceimages',
    'FBX')


ASSET_DIR_DICT = {
    'body': (
        'anim',
        'attrs',
        'connections',
        'ctrl',
        'deformer',
        'layers',
        'picker',
        'rigmesh',
        'shaders',
        'skeleton'),
    'face': (
        'anim',
        'attrs',
        'connections',
        'ctrls',
        'deformer',
        'layers',
        'metahuman',
        'picker',
        'pose',
        'rigmesh',
        'targets',
        'shaders',
        'skeleton',
        'textureDriver',
        'wtsDeformer')
}


def _clean_join(*args):
    #return os.path.join(*args).replace('\\', ' /').replace(' ', '')
    return os.path.join(*args).replace('\\', '/')


def create_workarea(root, project, char, rig_type='body'):
    """Creates maya project folders for a given character.

    Args:
        root (str): The workarea root path.
        project (str): The project name.
        char (str): The character name.
        rig_type (str): The rig type. "body" or "face".

    Returns:
        None
    """
    c_path = char_path(root, project, char)
    a_path = asset_path(root, project, char, rig_type=rig_type)

    for sub_dir in CHAR_DIR_LIST:
        sub_dir = _clean_join(c_path, sub_dir)
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

    for rt, sub_dirs in ASSET_DIR_DICT.items():
        if rt != rig_type:
            logger.debug('NOT {}, {}'.format(rig_type, rig_type))
            continue
        for sub_dir in sub_dirs:
            sub_dir = _clean_join(a_path, sub_dir)
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir)

    mel.eval('setProject \"' + c_path + '\"')


def char_path(root, project, char):
    """Returns a character path."""
    project_path = _clean_join(root, project)
    return _clean_join(project_path, char)


def asset_path(root, project, char, rig_type='body'):
    """Returns an asset path."""
    project_path = _clean_join(root, project)
    char_path = _clean_join(project_path, char)
    return _clean_join(char_path, 'assets', rig_type + 'RigAssets')


def marker_data_file(root, project, char, rig_type='body'):
    """Returns the marker data file path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'marker.json')


def ctrl_data_file(root, project, char, rig_type='body'):
    """Returns the ctrl data file path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'ctrl.json')
    
    
def connection_data_file(root, project, char, rig_type='body'):
    """Returns the ctrl data file path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'connections/connections.json')
    
    
def pr_connection_data_file(root, project, char, rig_type='body'):
    """Returns the ctrl data file path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'connections/pr_connections.json')


def set_data_file(root, project, char, rig_type='body'):
    """Returns the export set data file path for a given character."""
    return _clean_join(
        asset_path(root, project, char, rig_type), 'export_set.json')


def attribute_data_file(root, project, char, rig_type='face'):
    """Returns the attribute setting data file path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'attrs/attrs.json')


def skeleton_path(root, project, char, rig_type='body'):
    """Returns the skeleton directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'skeleton')


def rigmesh_path(root, project, char, rig_type='body'):
    """Returns the mesh directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'rigmesh')


def target_path(root, project, char, rig_type='face'):
    """Returns the mesh directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'targets')


def connection_path(root, project, char, rig_type='body'):
    """Returns the connection directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'connections')


def deformer_path(root, project, char, rig_type='body'):
    """Returns the deformer directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'deformer')
    
    
def blend_shape_path(root, project, char, rig_type='face'):
    """Returns the deformer directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'deformer/blend_shape')
    
    
def skin_cluster_path(root, project, char, rig_type='face'):
    """Returns the deformer directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'deformer/skin_cluster')


def wts_deformer_path(root, project, char, rig_type='body'):
    """Returns the wts deformer directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'wtsDeformer')


def pose_path(root, project, char, rig_type='face'):
    """Returns the pose directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'pose')


def picker_path(root, project, char, rig_type='body'):
    """Returns the picker directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'picker')


def metahuman_path(root, project, char, rig_type='face'):
    """Returns the metahuman directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'metahuman')


def shader_path(root, project, char, rig_type='face'):
    """Returns the shaders directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'shaders')


def attr_path(root, project, char, rig_type='face'):
    """Returns the attributes directory path for a given character."""
    return _clean_join(asset_path(root, project, char, rig_type), 'attrs')
    

def texture_driver_path(root, project, char, rig_type='body'):
    """Returns the texture driver node data path in json format."""
    return _clean_join(asset_path(root, project, char, rig_type), 'textureDriver', 'shader.json')


def rig_file(root, project, char, rig_type='body'):
    """Returns the output rig file path."""
    file_name = '{}.ma'.format(char)
    if rig_type == 'face':
        file_name = '{}_face.ma'.format(char)
    return _clean_join(char_path(root, project, char), 'scenes', file_name)
