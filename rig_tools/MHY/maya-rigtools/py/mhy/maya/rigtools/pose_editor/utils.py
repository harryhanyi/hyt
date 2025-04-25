"""

This modules will contains some convenient functions
import gzip
"""
from mhy.maya.rigtools.pose_editor.api.pose_controller import list_pose_controllers
import mhy.maya.rigtools.pose_editor.ui.model.pose_tree_model as ptm
from mhy.python.core.compatible import gzip_export
from six import string_types
import json


def export_pose_data(pose_controllers=None, file_path=None, compress=False):
    """
    This function will export pose data for each given pose controller. If
    a file path provided, a json format file will be exported to disk
    Args:
        pose_controllers:
        file_path:
        compress(bool): if compress data before writing to disk

    Returns:

    """
    if isinstance(pose_controllers, string_types):
        pose_controllers = [pose_controllers]

    if pose_controllers is None:
        pose_controllers = list_pose_controllers()

    if not pose_controllers:
        return
    data_to_export = {'pose_controls': list()}

    ptm.PoseTreeModel.clear_cached_models()
    for cp in pose_controllers:
        model = ptm.PoseTreeModel.get_model(cp, silent=True)
        data = model.export_data()
        data_to_export['pose_controls'].append(data)

    if file_path:
        data_str = json.dumps(data_to_export,
                              sort_keys=True,
                              indent=4,
                              separators=(',', ': '))
        if compress:
            gzip_export(data_str, file_path)
        else:
            with open(file_path, 'w') as output_file:
                output_file.write(data_str)

    return data_to_export
