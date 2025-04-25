from mhy.maya.rigtools.pose_editor.ui.model.influence_table_model import InfluenceTableModel
from mhy.maya.rigtools.pose_editor.ui.model.pose_tree_model import PoseTreeModel

main_window = None

pose_controller = None

# Init var with model instance helps ide inspect instance
Pose_View = None
action_view = None
corrective_pose_view = None
Pose_Model = PoseTreeModel()
Influence_Model = InfluenceTableModel()

# ========================================
# Target functions
# ========================================

Current_Targets = set()


def select_active_pose_influences():
    """
    select all the influences of the active pose.
    :return:
    """
    if not pose_controller:
        return
    pose = pose_controller.active_pose
    if not pose:
        return
    pose.select_all_influences()
    pose_controller.selected_influences = set(pose.influences.keys())


def influences_select_changed(select, deselect):
    """
    Update the selected influences
    """
    if not pose_controller:
        return
    pose_controller.selected_influences = pose_controller.selected_influences.union(
        set(select)).difference(set(deselect))
    select_influences()


def select_influences():
    """
    Select the influences transforms in Maya.
    """
    if not pose_controller:
        return
    if pose_controller.active_pose:
        pose_controller.active_pose.select_influences(pose_controller.selected_influences)


def get_active_item():
    if not pose_controller:
        return
    active_pose = pose_controller.active_pose
    if active_pose and Pose_Model:
        index = Pose_Model.get_index_by_pose_name(active_pose.name)
        if index and index.isValid():
            return Pose_Model.item_from_index(index)
