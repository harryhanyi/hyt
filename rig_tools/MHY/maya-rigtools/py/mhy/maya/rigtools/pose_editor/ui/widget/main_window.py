"""
The main dialog for face expression pose editing.
"""
import os

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds

from PySide2 import QtCore, QtWidgets

import mhy.maya.rigtools.pose_editor.api.pose_controller as p_ctrl
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
import mhy.maya.rigtools.pose_editor.ui.actions as action_lib
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
import mhy.maya.rigtools.pose_editor.ui.widget.pose_tree_widget as ptw
import mhy.maya.rigtools.pose_editor.ui.widget.influence_widget as itw
from mhy.maya.rigtools.pose_editor.ui.widget.controller_widget import ControllerView
import mhy.maya.rigtools.pose_editor.ui.manager as manager
import mhy.maya.rigtools.pose_editor.ui.widget.weight_slider as ws
import mhy.maya.rigtools.pose_editor.ui.widget.corrective_pose_editor as cpe
from mhy.maya.utils import undoable
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.api.utils import progress_lambda_begin, progress_lambda_end

import mhy.qt.core.base_main_window as mw
from mhy.qt.core.utils import get_icon


base_class = mw.get_window_class(app_name='MHY Pose Editor 2022')


class Window(base_class):
    """
    The widget for face expression pose editing.
    """
    maya_callbacks = []
    default_export_path = None

    def __init__(self):
        self.influence_view = None
        self.actions_view = None
        self.pose_tree_widget = None
        self.target_widget = None
        super(Window, self).__init__()
        manager.main_window = self

    def save_settings(self):
        """Updates the app settings and saves it to disk.

        Returns:
            QSettings: The settings object.
        """
        settings = super(Window, self).save_settings()
        settings.beginGroup('io_setting')
        settings.setValue('out_path', Window.default_export_path or "")
        settings.endGroup()
        settings.sync()
        return settings

    def load_settings(self):
        """Loads the app settings.

        Returns:
            QSettings: The settings object.
        """
        settings = super(Window, self).load_settings()

        settings.beginGroup('io_setting')
        Window.default_export_path = settings.value('out_path', '')
        settings.endGroup()
        return settings

    def setup_ui(self):
        """
        The widget for face expression pose editing.
        """
        self.setObjectName('PoseEditor')
        icon = get_icon('chimpamzee')
        self.setWindowIcon(icon)

        central_widget = QtWidgets.QWidget(self)
        main_layout = QtWidgets.QVBoxLayout(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("Pose Editor")

        # =========================================================
        # Actions
        # =========================================================

        export_all_action = QtWidgets.QAction("Export All Data", self)
        export_all_action.setStatusTip("Export pose data from all the pose controllers into a disk file")
        export_all_action.triggered.connect(self.do_export_all_pc)

        export_current_action = QtWidgets.QAction("Export Current", self)
        export_current_action.setStatusTip("Export pose data from the active pose controllers into a disk file")
        export_current_action.triggered.connect(self.do_export_current_pc)

        load_action = QtWidgets.QAction("Load Data", self)
        load_action.setStatusTip("Import pose data to current pose controller(Override original)")
        load_action.triggered.connect(self.do_pose_load)

        import_action = QtWidgets.QAction("Import Data", self)
        import_action.setStatusTip("Import pose data into current pose controller(Merge with original)")
        import_action.triggered.connect(self.do_pose_import)

        mirror_pose_action = QtWidgets.QAction("Mirror Pose", self)
        mirror_pose_action.setStatusTip("Mirror selected pose")
        mirror_pose_action.triggered.connect(self.do_pose_mirror)

        mirror_all_action = QtWidgets.QAction("Mirror All Poses", self)
        mirror_all_action.setStatusTip("Mirror all poses")
        mirror_all_action.triggered.connect(self.do_all_poses_mirror)

        reset_all_action = QtWidgets.QAction("Reset All Poses", self)
        reset_all_action.setStatusTip("Mirror selected pose")
        reset_all_action.triggered.connect(self.do_reset_all_poses)

        delete_key_action = QtWidgets.QAction('Delete Key', self)
        delete_key_action.setStatusTip("Delete selected pose key")
        delete_key_action.triggered.connect(self.do_delete_key)

        reset_target_action = QtWidgets.QAction('Reset Target', self)
        reset_target_action.setStatusTip("Reset target shape")
        reset_target_action.triggered.connect(self.do_target_reset)

        turn_on_targets_action = QtWidgets.QAction('Turn On Targets', self)
        turn_on_targets_action.setStatusTip("Turn on target shape")
        turn_on_targets_action.triggered.connect(self.do_target_turn_on)

        turn_off_targets_action = QtWidgets.QAction('Turn Off Targets', self)
        turn_off_targets_action.setStatusTip("Turn off target shape")
        turn_off_targets_action.triggered.connect(self.do_target_turn_off)

        update_cor_weight_action = QtWidgets.QAction('Update Corrective Weight', self)
        update_cor_weight_action.setStatusTip("Update Corrective weight at current key")
        update_cor_weight_action.setCheckable(True)
        update_cor_weight_action.setChecked(True)
        update_cor_weight_action.toggled.connect(self.update_corrective_weight_from_maya)

        clean_up_blend_shape_action = QtWidgets.QAction('Clean Up Blend Shape', self)
        clean_up_blend_shape_action.setStatusTip("This action will convert blend shape to "
                                                 "state that supports pose workflow")
        clean_up_blend_shape_action.triggered.connect(self.do_clean_up_blend_shape)

        clean_up_neutral_pose_action = QtWidgets.QAction('Clean Up Neutral Pose', self)
        clean_up_neutral_pose_action.setStatusTip("This action will set all the neutral pose to 0")
        clean_up_neutral_pose_action.triggered.connect(self.do_clean_up_neutral_pose)

        remove_parameter_pose_action = QtWidgets.QAction('Switch parameter pose to SDK', self)
        remove_parameter_pose_action.setStatusTip("This action will replace the parameter poses to set driven key setup")
        remove_parameter_pose_action.triggered.connect(self.remove_parameter_pose_cb)

        # =========================================================
        # Menus
        # =========================================================

        menu_bar = self.menuBar()
        file_menu = QtWidgets.QMenu('&File', self)
        menu_bar.addMenu(file_menu)
        file_menu.addAction(export_current_action)
        file_menu.addAction(export_all_action)
        file_menu.addSeparator()
        file_menu.addAction(load_action)
        file_menu.addAction(import_action)

        pose_menu = QtWidgets.QMenu('&Pose', self)
        menu_bar.addMenu(pose_menu)
        pose_menu.addAction(mirror_pose_action)
        pose_menu.addAction(mirror_all_action)
        pose_menu.addAction(reset_all_action)
        pose_menu.addSeparator()
        pose_menu.addAction(delete_key_action)

        inf_menu = QtWidgets.QMenu('&Influence', self)
        menu_bar.addMenu(inf_menu)
        inf_menu.addAction(action_lib.PoseActions.add_influence_action)
        inf_menu.addAction(action_lib.PoseActions.remove_influence_action)
        inf_menu.addAction(action_lib.PoseActions.select_influence_action)

        target_menu = QtWidgets.QMenu('&Target', self)
        menu_bar.addMenu(target_menu)
        target_menu.addAction(action_lib.PoseActions.switch_sculpt_mode_action)
        target_menu.addAction(action_lib.PoseActions.save_sculpt_action)
        target_menu.addAction(action_lib.PoseActions.delete_target_action)
        target_menu.addAction(action_lib.PoseActions.mirror_target_action)
        target_menu.addSeparator()
        target_menu.addAction(reset_target_action)
        target_menu.addAction(action_lib.PoseActions.save_selected_sculpt_action)
        target_menu.addSeparator()
        target_menu.addAction(turn_on_targets_action)
        target_menu.addAction(turn_off_targets_action)

        corrective_menu = QtWidgets.QMenu('&Corrective', self)
        menu_bar.addMenu(corrective_menu)
        corrective_menu.addAction(action_lib.PoseActions.new_corrective_action)
        corrective_menu.addAction(action_lib.PoseActions.del_corrective_action)
        corrective_menu.addSeparator()
        corrective_menu.addAction(update_cor_weight_action)

        clean_up_menu = QtWidgets.QMenu('&CleanUp', self)
        clean_up_menu.addAction(clean_up_blend_shape_action)
        clean_up_menu.addAction(clean_up_neutral_pose_action)
        clean_up_menu.addAction(remove_parameter_pose_action)
        menu_bar.addMenu(clean_up_menu)

        self.controller_view = ControllerView(parent=self)
        self.controller_view.setFixedHeight(64)
        main_layout.addWidget(self.controller_view)

        edit_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addLayout(edit_layout)

        p_ctrl.PoseController.clear_cached_controllers()

        self.root_widget = QtWidgets.QSplitter(QtCore.Qt.Horizontal, parent=self)
        edit_layout.addWidget(self.root_widget)

        lf_panel = QtWidgets.QWidget(self)
        self.root_widget.addWidget(lf_panel)

        lf_panel_layout = QtWidgets.QVBoxLayout(lf_panel)
        lf_panel.setLayout(lf_panel_layout)

        pose_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, parent=self)
        self.pose_tree_widget = ptw.PoseTreeWidget(parent=self)
        self.corrective_editor = cpe.CorrectivePoseEditor(parent=self)
        pose_splitter.addWidget(self.pose_tree_widget)
        pose_splitter.addWidget(self.corrective_editor)
        pose_splitter.setSizes([600, 300])

        self.weight_slider = ws.Slider(self)
        lf_panel_layout.addWidget(pose_splitter)

        self.influence_view = itw.InfluenceWidget(parent=self.root_widget)
        rt_panel = QtWidgets.QWidget(self)
        rt_panel_layout = QtWidgets.QVBoxLayout(self)
        rt_panel.setLayout(rt_panel_layout)

        tab_widget = QtWidgets.QTabWidget(self.root_widget)
        tab_widget.setFixedHeight(100)
        influence_panel = QtWidgets.QWidget(tab_widget)
        influence_actions_bar = QtWidgets.QToolBar("InfluenceBar")
        influence_actions_bar.setIconSize(QtCore.QSize(25, 25))
        influence_panel.setFixedHeight(50)
        influence_actions_bar.addAction(action_lib.PoseActions.add_influence_action)
        influence_actions_bar.addAction(action_lib.PoseActions.remove_influence_action)
        influence_actions_bar.addAction(action_lib.PoseActions.select_influence_action)
        inf_action_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom, influence_panel)
        inf_action_layout.setContentsMargins(0, 0, 0, 0)
        inf_action_layout.addWidget(influence_actions_bar)

        target_panel = QtWidgets.QWidget(tab_widget)
        target_actions_bar = QtWidgets.QToolBar("TargetBar")
        target_actions_bar.setIconSize(QtCore.QSize(25, 25))
        tgt_action_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom, target_panel)
        tgt_action_layout.setContentsMargins(0, 0, 0, 0)
        target_actions_bar.addAction(action_lib.PoseActions.save_sculpt_action)
        target_actions_bar.addAction(action_lib.PoseActions.delete_target_action)
        target_actions_bar.addAction(action_lib.PoseActions.mirror_target_action)
        target_actions_bar.addSeparator()
        target_actions_bar.addAction(action_lib.PoseActions.switch_sculpt_mode_action)
        target_panel.setFixedHeight(50)
        tgt_action_layout.addWidget(target_actions_bar)

        tab_widget.addTab(influence_panel, 'Influence')
        tab_widget.addTab(target_panel, 'Target')
        rt_panel_layout.addWidget(self.influence_view)
        rt_panel_layout.addWidget(self.weight_slider)
        rt_panel_layout.addWidget(tab_widget)
        self.root_widget.addWidget(rt_panel)

        self.setLayout(main_layout)
        controller_name = self.controller_view.current_controller
        self.set_controller(controller_name)

        item = manager.get_active_item()
        if item:
            self.pose_selection_changed_cb(item)

        SignalManager.controller_selection_changed.connect(self.set_controller)
        SignalManager.pose_selection_changed.connect(self.pose_selection_changed_cb)
        SignalManager.update_influence_attribute_signal.connect(self.influence_update_cb)
        self.create_maya_callback()

    def __del__(self):
        self.__delete_maya_callback()

    def create_maya_callback(self):
        """

        Create Maya callback to monitor the scene update.

        """
        if not self.maya_callbacks:
            self.maya_callbacks.append(OpenMaya.MSceneMessage.addCallback(
                OpenMaya.MSceneMessage.kAfterNew, self.__after_open_cb))
            self.maya_callbacks.append(OpenMaya.MSceneMessage.addCallback(
                OpenMaya.MSceneMessage.kAfterOpen, self.__after_open_cb))

    def __delete_maya_callback(self):
        """
        Remove all maya callback once Widgets is either hidden or deleted.
        """
        if not self.maya_callbacks:
            return
        for callback in self.maya_callbacks:
            OpenMaya.MMessage.removeCallback(callback)
        self.maya_callbacks = []

    def __after_open_cb(self, args):
        """
        The callback after user open a scene.
        """
        del args
        self.controller_view.refresh_controllers_deferred()

    def pose_selection_changed_cb(self, item):
        """
        Do the updates when the active pose is changed.

        """
        if item and item.type_str == 'pose':
            self.influence_view.update_ui(item.pose)
            self.weight_slider.update_key_view(item.pose)
            # self.actions_view.update_ui(item.pose)
        else:
            self.influence_view.update_ui(None)
            self.weight_slider.update_key_view(None)

    def influence_update_cb(self, pose):
        self.weight_slider.update_widgets(pose)

    def get_active_pose(self):
        """
        get the active pose of the controller
        """
        active_controller = self.pose_tree_widget.model.controller
        if active_controller:
            return active_controller.active_pose

    def set_controller(self, controller):
        """
        Set the controller with a given name nad update pose tree and corrective widget
        Args:
            controller(str): The name of the target controller

        """
        if controller:
            controller = p_ctrl.PoseController.get_controller(controller)
        else:
            controller = None

        if self.pose_tree_widget:
            self.pose_tree_widget.set_controller(controller)
        if self.corrective_editor:
            self.corrective_editor.controller = controller
        SignalManager.refresh_corrective_view_signal.emit()

    def enterEvent(self, event):
        """
        Override enter event to refresh influence table view if selected objects are not sync with
        slections in the ui
        Args:
            event:

        """
        if not self.influence_view:
            return
        if not manager.pose_controller:
            return
        active_pose = manager.pose_controller.active_pose
        if not active_pose:
            return
        sel = set(cmds.ls(sl=True))
        influences = set(active_pose.influences.keys())
        to_select = set(influences & sel)
        manager.pose_controller.selected_influences = to_select
        SignalManager.influence_update.emit()

    # =========================================================
    # Action callback implementation
    # =========================================================

    def do_export_all_pc(self):
        """
        do export pose action.
        """
        controllers = p_ctrl.list_pose_controllers()
        if not controllers:
            return
        if len(controllers) == 1:
            # If there's only one pose controller in the scene, do
            # regular export current pose controller action
            self.do_export_current_pc()
            return

        file_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Save Pose Files",
            Window.default_export_path or "",
            QtWidgets.QFileDialog.DontUseNativeDialog)
        if file_path:
            if not file_path.endswith('.mhy'):
                file_path = file_path + ".mhy"
            self.pose_tree_widget.view.export_all_data(file_path=file_path)
            dir_path = os.path.dirname(file_path)
            Window.default_export_path = dir_path

    def do_export_current_pc(self):
        """
        do export pose action.
        """
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Pose File",
            Window.default_export_path or "",
            "Mihoyo rig files (*.mhy);; All files (*.*)",
            None,
            QtWidgets.QFileDialog.DontUseNativeDialog)
        if file_path:
            if not file_path.endswith('.mhy'):
                file_path = file_path + ".mhy"
            self.pose_tree_widget.view.export_data(file_path=file_path)
            dir_path = os.path.dirname(file_path)
            Window.default_export_path = dir_path

    @undoable
    def do_pose_import(self):
        """
        Do load pose data to merge the data of active pose controller
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Rig File And Merge With Current Rig.",
            Window.default_export_path or "",
            "Mihoyo rig files (*.mhy);; All files (*.*)",
            None,
            QtWidgets.QFileDialog.DontUseNativeDialog)
        if file_path:
            progress_lambda = progress_lambda_begin(
                title='Importing Poses',
                status='Preparing for import: {}'.format(file_path),
                isInterruptable=False)
            self.pose_tree_widget.model.merge_data(
                file_path,
                progress_lambda=progress_lambda)
            progress_lambda_end()
            SignalManager.refresh_corrective_view_signal.emit()
            dir_path = os.path.dirname(file_path)
            Window.default_export_path = dir_path

    @undoable
    def do_pose_load(self):
        """
        Do load pose data to override the active pose controller

        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Rig File.",
            Window.default_export_path or "",
            "Mihoyo rig files (*.mhy);; All files (*.*)",
            None,
            QtWidgets.QFileDialog.DontUseNativeDialog)
        if file_path:
            progress_lambda = progress_lambda_begin(
                title='Loading Poses',
                status='Preparing for load: {}'.format(file_path),
                isInterruptable=False)
            self.pose_tree_widget.model.load_data(
                file_path,
                progress_lambda=progress_lambda)

            progress_lambda_end()
            SignalManager.refresh_corrective_view_signal.emit()
            dir_path = os.path.dirname(file_path)
            Window.default_export_path = dir_path

    @undoable
    def do_pose_mirror(self):
        """
        do mirror pose action.
        """
        pose = self.get_active_pose()
        if not pose:
            OpenMaya.MGlobal.displayWarning("No pose selected")
            return

        if pose.is_symmetry():
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle('Caution!')
            msg_box.setText("The pose is a middle pose do you want to do Left->Right Mirror on it's self?")
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

            pose.mirror(source=source_pose)
            SignalManager.pose_update.emit([pose.name])
        else:
            mirrored_pose = self.pose_tree_widget.model.get_mirror_pose(pose)
            if mirrored_pose:
                mirrored_pose.mirror_from(pose)
                mirrored_pose.start_cache_job(using_threading=True)
                SignalManager.pose_update.emit([mirrored_pose.name])

    @undoable
    def do_all_poses_mirror(self):
        """
        do mirror pose action.
        """
        controller = self.pose_tree_widget.model.controller
        if not controller:
            return
        controller.refresh_poses()

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle('Caution!')
        msg_box.setText("Please save before mirror. Please choose mirror type?")
        msg_box.addButton('Left To Right', QtWidgets.QMessageBox.ActionRole)
        r_to_l_button = msg_box.addButton('Right To Left', QtWidgets.QMessageBox.ActionRole)
        cancel_button = msg_box.addButton('Cancel', QtWidgets.QMessageBox.ActionRole)
        msg_box.exec_()

        # self left to right mirror.
        dst_pose = Symmetry.LEFT
        if msg_box.clickedButton() == cancel_button:
            return
        elif msg_box.clickedButton() == r_to_l_button:
            dst_pose = Symmetry.RIGHT
        poses = controller.get_poses(
            lambda p: p and p.symmetry == dst_pose)
        progress_lambda = progress_lambda_begin(
            title='Mirroring Poses',
            status='Preparing for mirror',
            isInterruptable=False)
        pose_num = len(poses)
        for idx, pose in enumerate(poses):
            progress_lambda("({0}/{1}){2}.".format(idx, pose_num, pose.name),
                            100.0*float(idx)/float(pose_num))
            mirrored_pose = self.pose_tree_widget.model.get_mirror_pose(pose)
            if mirrored_pose:
                mirrored_pose.mirror_from(pose)
        SignalManager.pose_update.emit(None)
        progress_lambda_end()

    @undoable
    def do_reset_all_poses(self):
        """
        reset all inactive weights to zero.
        """
        self.pose_tree_widget.model.reset_weights()

    @undoable
    def do_delete_key(self):
        """
        delete the pose key.
        """
        pose = self.get_active_pose()
        if not pose:
            OpenMaya.MGlobal.displayWarning("No pose selected")
            return

        if pose:
            confirm_info = cmds.confirmDialog(
                title='Delete the current key!',
                message='Are you sure to delete the current key of the pose:{}?'.format(pose.name),
                button=['Yes', 'No'],
                defaultButton='No',
                cancelButton='No',
                dismissString='No')
            if confirm_info != 'Yes':
                return
            controller = self.pose_tree_widget.model.controller
            controller.delete_key(pose, pose.weight)

        # self.actions_view.update_key_view()

    @undoable
    def do_target_reset(self):
        """
        reset the target mesh.
        """
        pose = self.get_active_pose()
        if not pose:
            OpenMaya.MGlobal.displayWarning("No pose selected")
            return

        weight = pose.weight
        target = pose.get_target(weight=weight)
        if target:
            answer = QtWidgets.QMessageBox.question(
                self,
                "Reset the target!",
                'Are you sure to reset the target at current weight? The action is undoable!')
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                target.reset()
                # self.actions_view.update_key_view()

        else:
            QtWidgets.QMessageBox.information(
                self,
                "No Target Found",
                "Can't find the delta pose at current weight!")

    def do_target_turn_on(self):
        """
        Turn on the blend shape associated with active pose controller

        """
        controller = self.pose_tree_widget.model.controller
        if not controller:
            return
        controller.set_target_status(1.0)
        self.pose_tree_widget.model.update_target_status()

    def do_target_turn_off(self):
        """
        Turn off the blend shape associated with active pose controller

        """
        controller = self.pose_tree_widget.model.controller
        if not controller:
            return
        controller.set_target_status(0.0)
        self.pose_tree_widget.model.update_target_status()

    def update_corrective_weight_from_maya(self, state):
        Settings.live_update_corrective_weight = state
        self.corrective_editor.update_corrective_weight_from_maya()

    def do_clean_up_blend_shape(self):
        """
        To support pose workflow, blend shapes shouldn't have components mask and
        the points data should be stored in vertex index order

        """
        controller = self.pose_tree_widget.model.controller
        if not controller:
            return
        controller.clean_up_sparse_components_data()

    def do_clean_up_neutral_pose(self):
        """
        Clean up neutral pose to 0
        """
        controller = self.pose_tree_widget.model.controller
        if not controller:
            return
        controller.clean_up_neutral_pose()

    def remove_parameter_pose_cb(self):
        controller = self.pose_tree_widget.model.controller
        step, ok = QtWidgets.QInputDialog.getInt(
            self,
            "Number of in-between keys",
            "Enter an integer number larger than 1",
            10,
            2,
            20
        )
        if not ok:
            return
        if step < 2:
            raise ValueError("Invalid number for in-between keys")
        cache = {}
        for pn, pose in controller.poses.items():
            tracer_controls = []
            tracer_control_map = {}
            for inf in pose.get_influences_data().keys():
                if inf.endswith('TRACER'):
                    fol_transform = inf.replace('TRACER','FLCTRANSFORM')
                    if cmds.objExists(fol_transform):
                        tracer_control_map[inf] = fol_transform

            sdk_values = []
            for i in range(step):
                cmds.setAttr(pose.output_attribute_full_name, i*10/(step-1))
                data = {}
                for inf, flc in tracer_control_map.items():
                    values = []
                    for j in 'tr':
                        for z in 'xyz':
                            val = cmds.getAttr(flc + '.' + j + z)
                            values.append(val)
                    data[flc] = values
                sdk_values.append(data)
            cache[pose.output_attribute_full_name] = {
                'sdkData': sdk_values,
                'ctrlMap': tracer_control_map
            }

        for pn, pose in controller.poses.items():
            data = cache.get(pose.output_attribute_full_name)
            if not data:
                continue
            tracer_control_map = data.get('ctrlMap', {})
            # break the connection between fol and parameter control
            for inf, flc in tracer_control_map.items():
                fol = inf.replace('_TRACER', '_FLC')
                if cmds.objExists(inf):
                    cmds.delete(inf)
                if cmds.objExists(fol):
                    cmds.delete(fol)
            # Recreate set driven key between output attribute to fol transform
            sdk_values = data.get('sdkData', {})
            for i in range(step):
                sdk_map = sdk_values[i]
                for flc, offset in sdk_map.items():
                    idx = 0
                    for j in 'tr':
                        for z in 'xyz':
                            val = offset[idx]
                            attr_name = j + z
                            cmds.setDrivenKeyframe(
                                flc + '.' + attr_name,
                                inTangentType="linear",
                                outTangentType="linear",
                                currentDriver=pose.output_attribute_full_name,
                                value=val,
                                driverValue=i*10/(step-1))
                            idx = idx + 1
        self.controller_view.refresh_controllers()
