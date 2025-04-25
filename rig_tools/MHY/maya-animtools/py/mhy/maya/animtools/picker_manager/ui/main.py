"""

This module is the mhy picker manager main dialog

"""
import os
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from PySide2 import QtWidgets, QtCore, QtGui

from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.constant import nodezoo_mm_attr
from mhy.maya.startup.marking_menu import MMENU_DATA
import mhy.maya.animtools.picker_manager.ui.picker_view as pv
import mhy.maya.animtools.picker_manager.node.viewport_picker as vp
from mhy.maya.rig.marking_menu import _select_rig_ctrls
import mhy.maya.animtools.picker_manager.api.pickers as picker_api
import mhy.qt.core.base_main_window as mw
from mhy.maya.animtools.picker_manager.ui.picker_property_widget import PickerPropertyWidget
from mhy.maya.animtools.picker_manager.ui.container_property_widget import ContainerPropertyWidget
from mhy.maya.animtools.picker_manager.ui.sel_set_widget import SelSetWidget
from mhy.qt.icon_lib.api import get_icon
import mhy.maya.animtools.picker_manager.ui.manager as manager


base_class = mw.get_window_class(app_name='MHY Picker Manager')


class Window(base_class):

    picker_file_filter = "MHY Picker files (*.lpk)"

    default_export_path = None

    def __init__(self):
        manager.edit_mode = True
        self.__edit_widgets = []
        self.__edit_actions = []
        self.current_name_space = None
        self.current_container = None
        self.edit_tab = None
        self.maya_callbacks = []
        self.create_maya_callback()
        super(Window, self).__init__()

    def save_settings(self):
        """Updates the app settings and saves it to disk.

        Returns:
            QSettings: The settings object.
        """
        settings = super(Window, self).save_settings()
        settings.beginGroup('io_setting')
        settings.setValue('out_path', Window.default_export_path or "")
        settings.endGroup()

        settings.beginGroup('ui_setting')
        settings.setValue('edit_mode', manager.edit_mode)
        settings.setValue('show_hidden_picker', manager.show_hidden_pickers)
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

        settings.beginGroup('ui_setting')
        manager.edit_mode = (settings.value('edit_mode', 'true') == 'true')

        manager.show_hidden_pickers = (settings.value('show_hidden_picker', 'true') == 'true')
        settings.endGroup()
        self.update_widgets()

        return settings

    def closeEvent(self, event):
        for callback in self.maya_callbacks:
            OpenMaya.MMessage.removeCallback(callback)
        self.maya_callbacks = []
        super(Window, self).closeEvent(event)

    def enterEvent(self, event):
        """
        Override enter event to refresh container drop down
        Args:
            event:

        """
        containers = vp.ViewportPicker.list_containers()
        self.current_container = self.get_active_container()
        for container in containers:
            if container.v.value:
                self.set_active_container(container.name)
                break
        self.refresh_active_selection()

    def keyReleaseEvent(self, event):
        super(Window, self).keyReleaseEvent(event)
        if event.key() == QtCore.Qt.Key_Z:
            self.refresh_active_selection()

    def refresh_active_selection(self):
        sel = cmds.ls(sl=True)
        to_sel = list()
        selected_ctrls = list()
        self.picker_scene.blockSignals(True)

        for k, v in self.picker_scene.nodes.items():
            if not Node.object_exist(k):
                continue
            picker_shape = Node(k)
            v.is_hidden = picker_shape.is_hidden()
            parent = picker_shape.get_parent()
            if parent:
                state = parent.name in sel
                v.setSelected(state)
                if state:
                    selected_ctrls.append(parent)
                    to_sel.append(v)
        self.picker_scene.blockSignals(False)
        self.update_action_widget()
        self.refresh_sel_set_widget(selected_ctrls)

        for item in to_sel:
            item.refresh_state()
        self.picker_scene.update_active_selection_text(to_sel)
        self.picker_property.set_items(to_sel)

    def create_maya_callback(self):
        """

        Create Maya callback to monitor the scene update.

        """
        if not self.maya_callbacks:
            self.maya_callbacks.append(OpenMaya.MSceneMessage.addCallback(
                OpenMaya.MSceneMessage.kAfterNew, self.__after_open_cb))
            self.maya_callbacks.append(
                OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterImport, self.__after_open_cb))
            self.maya_callbacks.append(OpenMaya.MSceneMessage.addCallback(
                OpenMaya.MSceneMessage.kAfterOpen, self.__after_open_cb))
            self.maya_callbacks.append(
                OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterReference, self.__after_open_cb))
            self.maya_callbacks.append(
                OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterRemoveReference, self.__after_open_cb))

    def __after_open_cb(self, args):
        del args
        cmds.evalDeferred(self.refresh_containers, low=True)

    def get_active_container(self):
        name_space = self.namespace_widget.combo.currentText()
        partial_name = self.container_combo.currentText()
        if not partial_name:
            return
        if name_space:
            return "{}:{}".format(name_space, partial_name)
        return partial_name

    def set_active_container(self, container):
        """

        Args:
            container(str): The name of container

        Returns:

        """
        if ':' in container:
            namespace, name = container.split(':')
        else:
            namespace = ""
            name = container
        self.namespace_widget.combo.setCurrentText(namespace)
        self.container_combo.setCurrentText(name)

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("MHY Picker")

        picker_view_widget = QtWidgets.QWidget(self)
        picker_view_layout = QtWidgets.QVBoxLayout()
        picker_view_widget.setLayout(picker_view_layout)

        container_layout = QtWidgets.QHBoxLayout()
        container_label = QtWidgets.QLabel("Picker Container: ")
        container_label.setFixedWidth(120)

        self.container_combo = QtWidgets.QComboBox()
        self.add_container_pb = QtWidgets.QPushButton('+')
        self.add_container_pb.setFixedSize(32, 32)
        self.add_container_pb.clicked.connect(self.add_container_cb)
        self.remove_container_pb = QtWidgets.QPushButton('-')
        self.remove_container_pb.setFixedSize(32, 32)
        self.remove_container_pb.clicked.connect(self.remove_container_cb)
        container_layout.addWidget(container_label)
        container_layout.addWidget(self.container_combo)
        container_layout.addWidget(self.add_container_pb)
        container_layout.addWidget(self.remove_container_pb)

        self.__edit_widgets.append(self.add_container_pb)
        self.__edit_widgets.append(self.remove_container_pb)

        self.picker_scene = pv.PickerScene()
        self.picker_view = pv.PickerView(self.picker_scene, self)

        self.sel_set_widget = SelSetWidget(self)

        self.__edit_widgets.append(self.sel_set_widget.add_pb)
        self.__edit_widgets.append(self.sel_set_widget.remove_pb)

        picker_view_layout.addLayout(container_layout)
        picker_view_layout.addWidget(self.picker_view)
        picker_view_layout.addWidget(self.sel_set_widget)

        self.sel_set_widget.sel_set_clicked_signal.connect(self.refresh_active_selection)

        # Edit widget
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.edit_widget = QtWidgets.QWidget(self)
        self.tab_widget.addTab(self.edit_widget, "Edit")

        self.actions_widget = QtWidgets.QWidget(self)
        self.tab_widget.addTab(self.actions_widget, "Actions")

        self.tab_widget.setCurrentIndex(0)
        action_layout = QtWidgets.QVBoxLayout()
        action_layout.addStretch()
        self.actions_widget.setLayout(action_layout)

        edit_layout = QtWidgets.QVBoxLayout()
        self.edit_widget.setLayout(edit_layout)

        container_setting_grp = QtWidgets.QGroupBox("Container Property: ")
        edit_layout.addWidget(container_setting_grp)
        container_setting_layout = QtWidgets.QVBoxLayout()
        container_setting_grp.setLayout(container_setting_layout)

        self.container_property = ContainerPropertyWidget(parent=self)
        container_setting_layout.addWidget(self.container_property)

        picker_setting_grp = QtWidgets.QGroupBox("Picker Property")
        edit_layout.addWidget(picker_setting_grp)
        picker_setting_layout = QtWidgets.QVBoxLayout()
        picker_setting_grp.setLayout(picker_setting_layout)

        self.picker_property = PickerPropertyWidget(parent=self)
        picker_setting_layout.addWidget(self.picker_property)
        self.picker_scene.selection_changed.connect(self.selection_changed_cb)
        self.picker_property.attribute_changed_signal.connect(self.container_property.update_children_info)

        # Finish up splitter
        splitter = QtWidgets.QSplitter(self)
        splitter.addWidget(picker_view_widget)
        splitter.addWidget(self.tab_widget)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        splitter.setStretchFactor(0, 9)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 100])

        main_layout.addWidget(splitter)

        # =========================================================
        # Actions
        # =========================================================

        save_action = QtWidgets.QAction("Save Data", self)
        save_action.setStatusTip("Save data of all the containers in the scene")
        save_action.triggered.connect(self.save_data_cb)

        load_action = QtWidgets.QAction("Load Data", self)
        load_action.setStatusTip("Load data from a file path")
        load_action.triggered.connect(self.load_data_cb)

        create_picker_action = QtWidgets.QAction('&Create Picker', self)
        create_picker_action.setStatusTip("Create picker node from selected controller")
        create_picker_action.triggered.connect(self.create_picker_cb)

        delete_picker_action = QtWidgets.QAction('&Delete Picker', self)
        delete_picker_action.setStatusTip("Delete selected pickers")
        delete_picker_action.setShortcut('Ctrl+d')
        delete_picker_action.triggered.connect(self.delete_pickers_cb)

        clear_picker_action = QtWidgets.QAction("Clear Pickers", self)
        clear_picker_action.setStatusTip("Clear all the pickers in the scene")
        clear_picker_action.setShortcut('Alt+c')
        clear_picker_action.triggered.connect(self.clear_pickers_cb)

        frame_selection_action = QtWidgets.QAction("FrameSelection", self)
        frame_selection_action.setStatusTip("Frame the graphic view to selected pickers")
        frame_selection_action.setShortcut('f')
        frame_selection_action.triggered.connect(lambda: self.picker_view.frame_items(True))

        icon = get_icon(
            sub_dir='/WINDOWS10/text/png/32/edit_document.png',
            color=(178, 233, 235))

        self.edit_mode_action = QtWidgets.QAction(icon, "Edit", self)
        self.edit_mode_action.setToolTip("Switch between Edit/Preview Mode(Currently Edit Mode)")
        self.edit_mode_action.triggered.connect(self.switch_edit_mode)

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_left.png',
            color=(178, 233, 235))

        align_left_action = QtWidgets.QAction(icon, "AlignLeft", self)
        align_left_action.setToolTip("Align selected items by left")
        align_left_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kLeft))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_center.png',
            color=(178, 233, 235))

        align_center_action = QtWidgets.QAction(icon, "AlignCenter", self)
        align_center_action.setToolTip("Align selected items by center")
        align_center_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kCenter))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_right.png',
            color=(178, 233, 235))

        align_right_action = QtWidgets.QAction(icon, "AlignRight", self)
        align_right_action.setToolTip("Align selected items by right")
        align_right_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kRight))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_top.png',
            color=(178, 233, 235))

        align_top_action = QtWidgets.QAction(icon, "AlignTop", self)
        align_top_action.setToolTip("Align selected items by top")
        align_top_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kTop))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_center.png',
            color=(178, 233, 235))
        align_middle_action = QtWidgets.QAction(icon, "AlignMiddle", self)
        align_middle_action.setToolTip("Align selected items by middle")
        align_middle_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kMiddle))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_bottom.png',
            color=(178, 233, 235))
        align_bottom_action = QtWidgets.QAction(icon, "AlignBottom", self)
        align_bottom_action.setToolTip("Align selected items by bottom")
        align_bottom_action.triggered.connect(
            lambda: self.picker_scene.align_selected_items(pv.PickerScene.AlignmentMethod.kBottom))

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/reflect_horizontal.png',
            color=(178, 233, 235))

        mirror_action = QtWidgets.QAction(icon, "Mirror", self)
        mirror_action.setToolTip("Mirror Pickers")
        mirror_action.triggered.connect(self.picker_scene.mirror_pickers)

        icon = get_icon(sub_dir='/IOS/general/png/48/refresh.png', color=(108, 222, 95))

        refresh_action = QtWidgets.QAction(icon, "Refresh", self)
        refresh_action.setToolTip("Refresh the items in the scene")
        refresh_action.triggered.connect(self.refresh_containers)

        self.display_hidden_picker_action = QtWidgets.QAction(
            "Show Hidden Pickers", self, checkable=True)
        self.display_hidden_picker_action.setToolTip(
            "If show hidden objects on this picker view"
        )

        self.display_hidden_picker_action.setChecked(manager.show_hidden_pickers)
        self.display_hidden_picker_action.toggled.connect(
            self.update_hidden_picker_display_cb)

        # =========================================================
        # Toolbar
        # =========================================================
        toolbar = QtWidgets.QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QtCore.QSize(32, 32))
        toolbar.addAction(self.edit_mode_action)
        toolbar.addSeparator()
        toolbar.addAction(align_left_action)
        toolbar.addAction(align_center_action)
        toolbar.addAction(align_right_action)

        sep1 = QtWidgets.QAction()
        sep1.setSeparator(True)
        toolbar.addAction(sep1)

        toolbar.addAction(align_top_action)
        toolbar.addAction(align_middle_action)
        toolbar.addAction(align_bottom_action)

        sep2 = QtWidgets.QAction()
        sep2.setSeparator(True)
        toolbar.addAction(sep2)

        toolbar.addAction(mirror_action)

        sep3 = QtWidgets.QAction()
        sep3.setSeparator(True)
        toolbar.addAction(sep3)

        toolbar.addAction(refresh_action)
        toolbar.addSeparator()

        self.__edit_actions = [align_left_action, align_center_action, align_right_action,
                               align_top_action, align_middle_action, align_bottom_action, mirror_action,
                               sep1, sep2, sep3]

        self.namespace_widget = NameSpaceDropDown(self)
        toolbar.addWidget(self.namespace_widget)
        # =========================================================
        # Menus
        # =========================================================

        menu_bar = self.menuBar()
        file_menu = QtWidgets.QMenu('&File', self)
        menu_bar.addMenu(file_menu)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)

        edit_menu = QtWidgets.QMenu('&Edit', self)
        edit_menu.addAction(create_picker_action)
        edit_menu.addAction(delete_picker_action)
        edit_menu.addAction(clear_picker_action)
        edit_menu.addSeparator()
        edit_menu.addAction(mirror_action)

        align_menu = QtWidgets.QMenu('Align', self)
        align_menu.addAction(align_left_action)
        align_menu.addAction(align_center_action)
        align_menu.addAction(align_right_action)
        align_menu.addAction(align_top_action)
        align_menu.addAction(align_middle_action)
        align_menu.addAction(align_bottom_action)
        edit_menu.addMenu(align_menu)
        menu_bar.addMenu(edit_menu)

        view_menu = QtWidgets.QMenu('&View', self)
        view_menu.addAction(frame_selection_action)
        view_menu.addAction(refresh_action)
        view_menu.addAction(self.display_hidden_picker_action)
        menu_bar.addMenu(view_menu)

        self.container_combo.currentTextChanged.connect(self.selected_container_changed_cb)
        self.namespace_widget.combo.currentTextChanged.connect(self.selected_container_changed_cb)
        self.refresh_containers()

    def selected_container_changed_cb(self, text=None):
        active_container = self.get_active_container()
        self.selected_container_changed(active_container)

    def switch_edit_mode(self):
        manager.edit_mode = not manager.edit_mode
        self.update_widgets()

    def update_hidden_picker_display_cb(self, state):
        manager.show_hidden_pickers = bool(state)
        self.picker_view.repaint()

    def update_widgets(self):
        if manager.edit_mode:
            icon = get_icon(
                sub_dir='/WINDOWS10/text/png/32/edit_document.png',
                color=(178, 233, 235))

            tool_tip = "Switch between Edit/Preview Mode(Currently Edit Mode)"
        else:
            icon = get_icon(
                sub_dir='/WINDOWS10/graphics/png/32/eye.png',
                color=(232, 222, 167))
            tool_tip = "Switch between Edit/Preview Mode" \
                       "(Currently Preview Mode)"

        self.edit_mode_action.setToolTip(tool_tip)

        self.edit_mode_action.setIcon(icon)

        if not manager.edit_mode and self.tab_widget.tabText(0) == "Edit":
            self.tab_widget.removeTab(0)
        else:
            self.tab_widget.insertTab(0, self.edit_widget, "Edit")
            self.tab_widget.setCurrentIndex(0)

        self.display_hidden_picker_action.setChecked(
            manager.show_hidden_pickers
        )

        menu_bar = self.menuBar()
        menu_bar.setVisible(manager.edit_mode)
        for i in self.__edit_widgets:
            i.setVisible(manager.edit_mode)
        for i in self.__edit_actions:
            i.setVisible(manager.edit_mode)

    def add_container_cb(self):
        """
        Add container push button clicked call back
        """
        dialog = QtWidgets.QInputDialog(parent=self)
        new_name, ok = QtWidgets.QInputDialog.getText(
            dialog, 'Container', 'Enter the name')

        if not new_name:
            return

        if ok and new_name:
            # create a new container
            new_container = vp.ViewportPicker.create_container(new_name)
            self.refresh_containers()
            # switch to the new container
            self.set_active_container(new_container.name)
            self.update_all_widgets(new_container.name)

    def remove_container_cb(self):
        """
        Remove container push button clicked call back
        """
        # remove the current selected container
        answer = QtWidgets.QMessageBox.question(
            self,
            "Deleting Container",
            "Deleting is non-revertible. Are you sure?")
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            index = self.container_combo.currentIndex()
            container_name = self.container_combo.currentText()
            self.container_combo.removeItem(index)
            if cmds.objExists(container_name):
                vp.ViewportPicker(container_name).delete()

    def sync_container_children_info(self, container=None):
        """
        Sync the container's children picker information
        Args:
            container(ViewportPicker): The container node

        Returns:

        """
        if not container:
            container = self.get_current_container()
        if not container:  # If no active picker container, skip
            return
        picker_api.sync_container_children_info(container)

    def selection_changed_cb(self, selection):
        """
        Called when selected picker item changed
        Args:
            selection(list): Selected items

        """
        self.picker_property.set_items(selection)
        self.picker_scene.update_active_selection_text(selection)
        sel_objects = [vp.ViewportPicker(i.name).get_parent() for i in selection if cmds.objExists(i.name)]
        cmds.select(sel_objects)
        self.update_action_widget()
        self.refresh_sel_set_widget(sel_objects)

    def update_action_widget(self):
        """
        Update action widgets
        Returns:

        """
        layout = self.actions_widget.layout()
        layout_count = layout.count()
        for i in reversed(range(layout_count-1)):
            item = layout.itemAt(i)
            item_widget = item.widget()
            item_widget.setParent(None)

        sel = cmds.ls(sl=True)
        actions = []
        if sel:
            tgt = Node(sel[0])
            attr = '{}.{}'.format(tgt, nodezoo_mm_attr)
            if cmds.objExists(attr):
                menu_names = cmds.getAttr(attr)
                for menu_name in menu_names.split(';'):
                    item_command = MMENU_DATA.get(menu_name)
                    try:
                        command_to_exec = item_command.format(NODE='"{}", dry_run=True'.format(tgt.name))
                        exec(command_to_exec, globals())
                        actions.extend(action_items)
                    except BaseException as e:
                        print(str(e))

        # Select all controls as pb = QtWidgets.QPushButton(label) action
        pb = QtWidgets.QPushButton("Select All Ctrls")
        pb.clicked.connect(self.select_all_ctrls)
        layout.insertWidget(0, pb)

        idx = 1
        for i in actions:
            command = i.command
            label = i.label
            pb = QtWidgets.QPushButton(label)
            if not command or not label:
                continue
            pb.clicked.connect(lambda checked=True, cmd=command: self.run_script(checked, cmd))
            layout.insertWidget(idx, pb)
            idx = idx + 1

    def select_all_ctrls(self):
        try:
            _select_rig_ctrls(self.current_name_space or "")
        except Exception as e:
            print(str(e))

    def refresh_sel_set_widget(self, sel_ctrls):
        self.sel_set_widget.refresh_pb(sel_ctrls)

    def run_script(self, state, command):
        exec(command)
        self.refresh_active_selection()

    def update_container_image_cb(self, path):
        """
        Called when image path line edit updates. If text is set to a
        valid image path, container will resize to the image size as initial
        state
        Args:
            path(str):

        """
        current_container = self.get_current_container()
        if current_container:
            current_container.set_image_path(path)
            if os.path.isfile(path):
                bounding_box = self.picker_scene.itemsBoundingRect()
                center = bounding_box.center()
                reader = QtGui.QImageReader(path)
                size = reader.size()
                current_container.set_width(size.width())
                current_container.set_height(size.height())
                current_container.set_picker_position([center.x(), -1*center.y()])
        container_node = self.picker_scene.find_container_node()
        if container_node:
            container_node.update_internal_data(current_container)
            self.picker_scene.update()

    def update_partial_name_combo(self, container_name, container_cache):
        self.container_combo.clear()
        if ':' not in container_name:
            container_partial_names = container_cache.get(':', [])
        else:
            container_partial_names = container_cache.get(container_name.split(":")[0], [])

        container_partial_names = [pn.split(':')[-1] for pn in container_partial_names]
        self.container_combo.addItems(container_partial_names)
        self.set_active_container(container_name)

    def refresh_containers(self, sync_children=False):
        """

        Args:
            sync_children(bool): If update the children information of current container node before
            switching active container

        """

        self.namespace_widget.combo.blockSignals(True)
        self.container_combo.blockSignals(True)

        self.namespace_widget.combo.clear()
        self.container_combo.clear()
        container_map = picker_api.get_name_space_container_map()
        containers = vp.ViewportPicker.list_containers()

        containers = [container.name for container in containers]
        name_spaces = sorted([i if i != ':' else "" for i in container_map.keys()])
        self.namespace_widget.combo.addItems(name_spaces)
        self.current_name_space = self.namespace_widget.combo.currentText()

        has_active = False
        for container in containers:
            container = vp.ViewportPicker(container)
            if container.v.value:
                self.update_partial_name_combo(container.name, container_map)
                has_active = True
                break

        if containers and not has_active:
            container_name = containers[0]
            self.update_partial_name_combo(container_name, container_map)

        self.container_combo.blockSignals(False)
        self.namespace_widget.combo.blockSignals(False)

        active_container = self.get_active_container()
        self.selected_container_changed(active_container, sync_children)

    def selected_container_changed(self, text=None, sync_children=True):
        """
        Called when selected container node changed. This method will set active container and switch
        the visibility of children pickers
        Args:
            text(str or None):
            sync_children(bool): If update the children information of current container node before
            switching active container

        """
        self.update_all_widgets(text, sync_children)
        self.current_container = text

    def update_all_widgets(self, container=None, sync_children=False):
        """

        Args:
            container:
            sync_children:

        Returns:

        """
        item = self.picker_view.set_container(container=container, sync_children=sync_children)
        if item:
            self.container_property.set_items([item])

    @staticmethod
    def get_current_container():
        """
        Get the active(visible) container
        Returns:

        """
        containers = vp.ViewportPicker.list_containers()
        for container in containers:
            if container.v.value:
                return container

    def create_picker_cb(self):
        """
        Create pickers from selected controllers

        """
        if not self.container_combo.currentText():
            # Need to create a container for created pickers
            current_container = vp.ViewportPicker.create_container()
        else:
            current_container = self.get_current_container()

        picker_api.create_picker_for_selected(current_container)

        self.refresh_containers()

    def delete_pickers_cb(self):
        """
        Remove the pickers in the scene
        Returns:

        """
        pickers = picker_api.find_pickers()
        containers = vp.ViewportPicker.list_containers()
        for container in containers:
            container.remove_child_pickers(pickers)
        for picker in pickers:
            vp.ViewportPicker.remove_picker(picker)
        self.refresh_containers()

    def clear_pickers_cb(self):
        """
        Clear all pickers in the scene
        Returns:

        """
        answer = QtWidgets.QMessageBox.question(
            self,
            "Clear Pickers",
            "Clearing is non-revertible. Are you sure?")
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            vp.ViewportPicker.clear_pickers()
            self.picker_scene.clear()

    @staticmethod
    def _get_picker_workspace_path():
        """
        Get the path to picker asset data in the current workspace
        Returns:
            str:
        """
        current_workspace = cmds.workspace(query=True, rootDirectory=True)
        picker_path = os.path.join(current_workspace, 'assert', 'picker')
        if os.path.isdir(picker_path):
            return picker_path
        return current_workspace

    def save_data_cb(self):
        """
        Save picker data push button call back

        """
        default_dir = self._get_picker_workspace_path()
        if Window.default_export_path and Window.default_export_path.startswith(default_dir):
            default_dir = Window.default_export_path
            if os.path.isfile(default_dir):
                default_dir = os.path.dirname(default_dir)

        file_dialog = QtWidgets.QFileDialog(self, "Save Picker Data", default_dir)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setNameFilters([Window.picker_file_filter])
        result = file_dialog.exec_()
        if result:
            export_file = file_dialog.selectedFiles()[0]
        else:
            return

        self.sync_container_children_info()
        pickers = cmds.ls(type=vp.ViewportPicker.api_type_str)
        pickers = [vp.ViewportPicker(picker) for picker in pickers]

        data = picker_api.export_data_to_file(export_file, pickers)

        Window.default_export_path = os.path.dirname(export_file)  # Update default path
        return data

    def load_data_cb(self):
        """
        Load data into the scene

        """
        default_dir = self._get_picker_workspace_path()
        if Window.default_export_path and Window.default_export_path.startswith(default_dir):
            default_dir = Window.default_export_path
            if os.path.isfile(default_dir):
                default_dir = os.path.dirname(default_dir)
        file_dialog = QtWidgets.QFileDialog(self, "Load Picker Data", default_dir)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        file_dialog.setNameFilters([Window.picker_file_filter])
        result = file_dialog.exec_()
        if result:
            files_to_import = file_dialog.selectedFiles()
            files_to_import = [file_path.replace('\\', '/') for file_path in files_to_import]
        else:
            return

        file_path = files_to_import[0]
        if os.path.isfile(file_path):
            vp.ViewportPicker.clear_pickers()
            picker_api.load_data_from_file(file_path)
        Window.default_export_path = os.path.dirname(file_path)
        self.refresh_containers(sync_children=False)

    def show(self):
        super(Window, self).show()
        self.picker_view.frame_items()


class NameSpaceDropDown(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NameSpaceDropDown, self).__init__(parent=parent)
        main_layout = QtWidgets.QHBoxLayout(self)
        label = QtWidgets.QLabel("Namespace: ", self)
        self.combo = QtWidgets.QComboBox(self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.combo)


def launch():
    return Window.launch()
