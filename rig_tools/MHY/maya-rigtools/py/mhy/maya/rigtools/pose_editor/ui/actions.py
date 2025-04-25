import mhy.maya.rigtools.pose_editor.ui.manager as manager
from mhy.maya.rigtools.pose_editor.api.influence import get_influence_names
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from PySide2 import QtWidgets, QtGui
import maya.OpenMaya as OpenMaya
from mhy.qt.core.utils import get_icon
import maya.cmds as cmds
from mhy.maya.utils import undoable
from mhy.maya.nodezoo.node import Node
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.rigtools.pose_editor.ui.widget.create_corrective_pose_dialog import CreateCorrectivePoseDialog


def get_active_pose():
    controller = manager.pose_controller
    if not controller:
        OpenMaya.MGlobal.displayWarning("No active pose controller")
        return
    active_pose = controller.active_pose
    if not active_pose:
        OpenMaya.MGlobal.displayWarning("No active pose")
        return
    return active_pose


def do_influences_add():
    """
    do add target action.
    """
    active_pose = get_active_pose()
    if not active_pose:
        return
    influence_names = get_influence_names() or []
    added_influences = active_pose.add_influences(influence_names)
    active_pose.refresh_cache(False)

    active_pose.select_influences(added_influences)

    # UI updates
    manager.pose_controller.selected_influences = set(added_influences)
    if manager.Influence_Model:
        manager.Influence_Model.populate(active_pose.influences.values())

    SignalManager.update_influence_attribute_signal.emit(active_pose)
    SignalManager.pose_changed_signal.emit(active_pose, active_pose.weight)
    manager.Pose_Model.refresh_pose(active_pose)


@undoable
def do_influences_remove():
    """
    Call back method to remove selected influences from active pose
    """

    active_pose = get_active_pose()
    if not active_pose:
        return
    answer = QtWidgets.QMessageBox.question(
        manager.main_window,
        "Delete selected influences?",
        'Are you sure to delete the selected influences?')
    if answer != QtWidgets.QMessageBox.StandardButton.Yes:
        return

    highlight_influences = manager.pose_controller.selected_influences
    active_pose.delete_influences(highlight_influences)
    active_pose.refresh_cache(False)
    SignalManager.update_influence_attribute_signal.emit(active_pose)
    manager.Pose_Model.refresh_pose(active_pose)
    SignalManager.pose_changed_signal.emit(active_pose, active_pose.weight)
    cmds.select(clear=True)


def do_influences_select_all():
    """
    select all influences.
    """
    active_pose = get_active_pose()
    if not active_pose:
        return
    manager.select_active_pose_influences()
    manager.pose_controller.selected_influences = set(active_pose.influences.keys())
    SignalManager.influence_update.emit()


def switch_sculpt_mode():
    """
    Switch between sculpt geo and bind geo mode
    """
    controller = manager.pose_controller
    if not controller:
        return
    if controller.is_sculpting:
        controller.remove_sculpt_mesh()

    else:
        sculpt_geo = controller.create_sculpt_mesh()
        if sculpt_geo:
            cmds.select(sculpt_geo.name)
            OpenMaya.MGlobal.displayInfo("Created sculpt geo")

    if controller.is_sculpting:
        PoseActions.switch_sculpt_mode_action.setIcon(PoseActions.leave_sculpt_mode_icon)
        PoseActions.switch_sculpt_mode_action.setToolTip('Currently in Sculpture mode(Click to Leave)')
    else:
        PoseActions.switch_sculpt_mode_action.setIcon(PoseActions.enter_sculpt_mode_icon)
        PoseActions.switch_sculpt_mode_action.setToolTip('Currently in non-sculpture mode(Click to Enter)')


def do_save_sculpt():
    controller = manager.pose_controller
    if not controller:
        return
    active_pose = controller.active_pose
    if not active_pose:
        OpenMaya.MGlobal.displayWarning("No active pose")
        return
    active_sculpt_mesh = controller.active_sculpt_mesh
    if not active_sculpt_mesh:
        OpenMaya.MGlobal.displayError("No Sculpting is active")
        return

    sculpt_mesh = active_sculpt_mesh[0]
    sculpt_mesh = Node(sculpt_mesh)
    if sculpt_mesh.type_name == 'transform':  # If get transform node as sculpt mesh, look for mesh
        shapes = sculpt_mesh.get_shapes()
        if shapes:
            sculpt_mesh = shapes[0]

    manager.pose_controller.save_sculpt_to_target(sculpt_mesh)
    # Remove points tweak from sculpt mesh
    for i in sculpt_mesh.pnts:
        i.remove()
    active_pose.refresh_cache(False)
    SignalManager.pose_changed_signal.emit(active_pose, active_pose.weight)


def do_save_selected_sculpt():
    controller = manager.pose_controller
    if not controller:
        return
    active_pose = controller.active_pose
    if not active_pose:
        OpenMaya.MGlobal.displayWarning("No active pose")
        return

    sel = cmds.ls(sl=True)
    if not sel:
        return
    sculpt_mesh = sel[0]
    sculpt_mesh = Node(sculpt_mesh)
    if sculpt_mesh.type_name == 'transform':  # If get transform node as sculpt mesh, look for mesh
        shapes = sculpt_mesh.get_shapes()
        if shapes:
            sculpt_mesh = shapes[0]

    manager.pose_controller.save_sculpt_to_target(sculpt_mesh)
    # Remove points tweak from sculpt mesh
    active_pose.refresh_cache(False)
    SignalManager.pose_changed_signal.emit(active_pose, active_pose.weight)


def do_target_mirror():
    """
    Mirror the target model.
    """
    pose = get_active_pose()
    if not pose:
        return
    weight = pose.weight

    target = pose.get_target(weight=weight/10.0)

    if target:
        msg_box = QtWidgets.QMessageBox(manager.main_window)
        msg_box.setWindowTitle('Mirror the target!')
        msg_box.setText('Are you sure to mirror the target vertex position? '
                        'Half side of geometry changing will lost!')
        msg_box.addButton('Left To Right', QtWidgets.QMessageBox.ActionRole)
        r_to_l_button = msg_box.addButton('Right To Left', QtWidgets.QMessageBox.ActionRole)
        cancel_button = msg_box.addButton('Cancel', QtWidgets.QMessageBox.ActionRole)
        msg_box.exec_()
        source_pose = Symmetry.LEFT
        # self left to right mirror.
        if msg_box.clickedButton() == cancel_button:
            return
        elif msg_box.clickedButton() == r_to_l_button:
            source_pose = Symmetry.RIGHT

        target.mirror(source=source_pose)
        pose.refresh_cache(False)
    else:
        QtWidgets.QMessageBox.critical(manager.main_window,
                                       "No Delta",
                                       "Can't find the target data at current weight")


def do_target_delete():
    """
    Action callback to remove the target at the active pose.
    """
    pose = get_active_pose()
    if not pose:
        return
    weight = pose.weight
    if pose.get_target(weight=weight/10.0):
        answer = QtWidgets.QMessageBox.question(
            manager.main_window,
            "Remove the target!",
            'Are you sure to remove the target '
            'at current weight? The action is undoable!')
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            manager.pose_controller.delete_target(pose, weight)
            SignalManager.pose_changed_signal.emit(pose, pose.weight)
    else:
        QtWidgets.QMessageBox.warning(
            manager.main_window,
            'Warning',
            "Can't find the delta pose at current weight!"
        )


def do_create_corrective_pose():
    """
    Add corrective pose for current shape.
    """
    active_pose = get_active_pose()
    if not active_pose:
        return
    if active_pose.is_corrective:
        QtWidgets.QMessageBox.critical(
            manager.main_window,
            'Error!',
            "You can't use a corrective pose({0}) as the drive pose.".format(active_pose.name))
        return
    poses = manager.pose_controller.get_poses(
        lambda pose: pose and pose.weight != 0.0 and not pose.is_corrective and pose != active_pose)
    poses.append(active_pose)
    create_dialog = CreateCorrectivePoseDialog(
        controller=manager.pose_controller,
        poses=poses,
        parent=manager.main_window)
    create_dialog.show()


def do_delete_corrective_pose():
    controller = manager.pose_controller

    if controller and manager.corrective_pose_view:
        corrective_pose, _ = manager.corrective_pose_view.get_selected_corrective_and_drive()
        if manager.Pose_Model:
            item = manager.Pose_Model.get_pose_item_by_pose_name(corrective_pose.name)
            manager.Pose_Model.delete_item(item)
        SignalManager.refresh_corrective_view_signal.emit()


def update_actions(pose, weight):
    current_value_is_target = pose.has_target(weight/10.0)
    if current_value_is_target:
        PoseActions.mirror_target_action.setEnabled(True)
        PoseActions.delete_target_action.setEnabled(True)
    else:
        PoseActions.mirror_target_action.setEnabled(False)
        PoseActions.delete_target_action.setEnabled(False)


class PoseActions(object):
    """
    This class is a namespace container for all the actions used for pose ui
    """

    # =========================================================
    # Influence Actions
    # =========================================================

    add_icon = get_icon('add.png', QtGui.QColor(255, 255, 255))
    add_influence_action = QtWidgets.QAction(add_icon, "Add Influences", None)
    add_influence_action.setToolTip("Add selected influences to active pose")
    add_influence_action.triggered.connect(do_influences_add)

    delete_inf_icon = get_icon('delete.png', QtGui.QColor(255, 255, 255))
    remove_influence_action = QtWidgets.QAction(delete_inf_icon, "Remove Influences", None)
    remove_influence_action.setToolTip("Remove selected influences from active pose")
    remove_influence_action.triggered.connect(do_influences_remove)

    select_icon = get_icon('arrowhead_right.png', QtGui.QColor(255, 255, 255))
    select_influence_action = QtWidgets.QAction(select_icon, "Select Influences", None)
    select_influence_action.setToolTip("Select all influences associated with active pose")
    select_influence_action.triggered.connect(do_influences_select_all)

    # =========================================================
    # Target Actions
    # =========================================================
    enter_sculpt_mode_icon = get_icon('hammer.png', QtGui.QColor(171, 107, 81))
    leave_sculpt_mode_icon = get_icon('hammer.png', QtGui.QColor(87, 193, 255))
    switch_sculpt_mode_action = QtWidgets.QAction(enter_sculpt_mode_icon, "Switch Sculpt Mode", None)
    switch_sculpt_mode_action.setToolTip('Currently in non-sculpture mode(Click to Enter)')
    switch_sculpt_mode_action.triggered.connect(switch_sculpt_mode)

    save_sculpt_icon = get_icon('insourcing.png', QtGui.QColor(179, 226, 131))
    save_sculpt_action = QtWidgets.QAction(save_sculpt_icon, "Save Sculpt", None)
    save_sculpt_action.setToolTip("Save sculpt geo to active pose at current weight")
    save_sculpt_action.triggered.connect(do_save_sculpt)

    mirror_target_icon = get_icon('reflect.png', QtGui.QColor(148, 164, 235))
    mirror_target_action = QtWidgets.QAction(mirror_target_icon, "Mirror Target", None)
    mirror_target_action.setEnabled(False)
    mirror_target_action.setToolTip("Mirror target for active pose at current weight")
    mirror_target_action.triggered.connect(do_target_mirror)

    delete_target_icon = get_icon('delete.png', QtGui.QColor(233, 148, 151))
    disabled_delete_target_icon = get_icon('delete.png', QtGui.QColor(150, 150, 150, 90))
    delete_target_action = QtWidgets.QAction(delete_target_icon, "Delete Target", None)
    delete_target_action.setEnabled(False)
    delete_target_action.setToolTip("Delete the target from active pose at current weight")
    delete_target_action.triggered.connect(do_target_delete)

    save_selected_sculpt_action = QtWidgets.QAction("Save Target With Selection", None)
    save_selected_sculpt_action.setToolTip("Save selected geo as target to active pose at current weight")
    save_selected_sculpt_action.triggered.connect(do_save_selected_sculpt)



    # select_influence_action = QtWidgets.QAction(select_icon, "Select Influences")
    # select_influence_action.setToolTip("Select all influences associated with active pose")
    # select_influence_action.triggered.connect(do_influences_select_all)

    # =========================================================
    # Corrective Actions
    # =========================================================
    new_corrective_icon = get_icon('add.png', QtGui.QColor(255, 255, 255))
    new_corrective_action = QtWidgets.QAction(new_corrective_icon, 'New Corrective', None)
    new_corrective_action.setToolTip("Create a new corrective pose with selected pose and active poses")
    new_corrective_action.triggered.connect(do_create_corrective_pose)

    del_corrective_icon = get_icon('delete.png', QtGui.QColor(255, 255, 255))
    del_corrective_action = QtWidgets.QAction(del_corrective_icon, 'Delete Corrective', None)
    del_corrective_action.setToolTip("Delete selected corrective pose in the view")
    del_corrective_action.triggered.connect(do_delete_corrective_pose)

    SignalManager.pose_changed_signal.connect(update_actions)


