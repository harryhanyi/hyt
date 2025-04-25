"""
This module is for launching protostar ui
"""

import sys
import os
import webbrowser
import json
from six import string_types
import logging
from mhy.qt.icon_lib.api import get_icon
# from mhy.qt.core.Qt import QtGui, QtWidgets, QtCore
from PySide2 import QtGui, QtWidgets, QtCore
import mhy.qt.core.base_main_window as mw

from mhy.protostar.ui.view.node_view import GraphicView, GraphicScene
from mhy.protostar.lib import ActionLibrary as alib
from mhy.protostar.constants import GRAPH_EXT
from mhy.protostar.ui.widget.parameter_widget import ParameterWidget,\
    GraphParameterWidget
from mhy.protostar.ui.widget.logging_widget import LoggingLine
from mhy.protostar.ui.widget.library_browser import LibraryWidget
import mhy.protostar.ui.manager as manager
logger = logging.getLogger(__name__)

base_class = mw.get_window_class(app_name='MHY Protostar')


class Window(base_class):
    file_ext_filter = "MHY Protostar files (*{})".format(GRAPH_EXT)
    default_export_path = None
    default_graph_name = 'main'

    def __init__(self, parent=None):
        self.graph_tabs = list()
        self.__current_file_path = None
        super(Window, self).__init__(parent=parent)

    def save_settings(self):
        """Updates the app settings and saves it to disk.

        Returns:
            QSettings: The settings object.
        """
        settings = super(Window, self).save_settings()
        settings.beginGroup('io_setting')
        settings.setValue('out_path', Window.default_export_path or "")
        settings.setValue('tag_filter', LibraryWidget.tag_filter_state or [])
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
        LibraryWidget.tag_filter_state = settings.value('tag_filter', [])
        settings.endGroup()
        return settings

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.current_file_path = self.current_file_path




        # =========================================================
        # Actions
        # =========================================================
        new_action = QtWidgets.QAction("New graph", self)
        new_action.setStatusTip(
            "Start from a new graph"
        )

        save_action = QtWidgets.QAction("Save", self)
        save_action.setStatusTip(
            "Save the main graph"
        )

        save_as_action = QtWidgets.QAction("Save As", self)
        save_as_action.setStatusTip(
            "Save the main graph to a file path"
        )

        open_action = QtWidgets.QAction("Open", self)
        open_action.setStatusTip("Load data from a file path")

        export_action = QtWidgets.QAction("Export", self)
        export_action.setStatusTip("Export selected graph to a file path")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_left.png',
            color=(178, 233, 235))

        align_left_action = QtWidgets.QAction(icon, "Align Left", self)
        align_left_action.setToolTip("Align selected items by left")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_center.png',
            color=(178, 233, 235))

        align_center_action = QtWidgets.QAction(icon, "Align Center", self)
        align_center_action.setToolTip("Align selected items by center")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_vertical_right.png',
            color=(178, 233, 235))

        align_right_action = QtWidgets.QAction(icon, "Align Right", self)
        align_right_action.setToolTip("Align selected items by right")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_top.png',
            color=(178, 233, 235))

        align_top_action = QtWidgets.QAction(icon, "Align Top", self)
        align_top_action.setToolTip("Align selected items by top")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_center.png',
            color=(178, 233, 235))
        align_middle_action = QtWidgets.QAction(icon, "Align Middle", self)
        align_middle_action.setToolTip("Align selected items by middle")

        icon = get_icon(
            sub_dir='/WINDOWS10/graphics/png/32/align_horizontal_bottom.png',
            color=(178, 233, 235))
        align_bottom_action = QtWidgets.QAction(icon, "Align Bottom", self)
        align_bottom_action.setToolTip("Align selected items by bottom")

        icon = get_icon(
            sub_dir='/IOS/general/png/72/refresh.png',
            color=(126, 181, 222))
        refresh_action = QtWidgets.QAction(icon, "Refresh", self)
        refresh_action.setToolTip("Refresh the protostar library")

        icon = get_icon(
            sub_dir='/WINDOWS10/video_production/png/72/play_2.png',
            color=[88, 255, 172])
        execute_action = QtWidgets.QAction(icon, "Execute", self)
        execute_action.setToolTip("Execute the main graph")

        icon = get_icon(
            sub_dir='/GLYPH/general/png/72/arrow_down.png',
            color=[38, 204, 255])
        step_action = QtWidgets.QAction(icon, "Step", self)
        step_action.setToolTip("Execute the main graph in step(F8)")
        step_action.setShortcut('F8')

        icon = get_icon(
            sub_dir='/WINDOWS10/video_production/png/72/next_2.png',
            color=[38, 204, 255])
        resume_action = QtWidgets.QAction(icon, "Resume", self)
        resume_action.setToolTip(
            "Resume the execution and continue until the end of the graph(F9)")
        resume_action.setShortcut('F9')

        icon = get_icon(
            sub_dir='/WINDOWS10/multimedia/png/72/stop.png',
            color=[255, 98, 101])
        reset_action = QtWidgets.QAction(icon, "Reset", self)
        reset_action.setToolTip(
            "Reset the execution graph and start from beginning")

        # Creation actions
        create_graph_action = QtWidgets.QAction("Create Graph", self)
        create_graph_action.setToolTip("Create an empty graph node")

        create_graph_for_sel_action = QtWidgets.QAction(
            "Create Graph For Selected", self)
        create_graph_for_sel_action.setToolTip(
            "Create a graph for selected objects")

        icon = get_icon(
            sub_dir='/IOS/general/png/72/help.png', color=[255, 255, 255])
        help_action = QtWidgets.QAction(icon, "&Help", self)
        help_action.setToolTip("Open the help page")

        # =========================================================
        # Toolbar
        # =========================================================
        toolbar = QtWidgets.QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QtCore.QSize(32, 32))
        toolbar.addAction(align_left_action)
        toolbar.addAction(align_center_action)
        toolbar.addAction(align_right_action)

        toolbar.addAction(align_top_action)
        toolbar.addAction(align_middle_action)
        toolbar.addAction(align_bottom_action)

        toolbar.addSeparator()

        toolbar.addAction(refresh_action)
        toolbar.addSeparator()

        # toolbar.addAction(break_pnt_action)
        # toolbar.addSeparator()

        toolbar.addAction(step_action)
        toolbar.addAction(resume_action)
        toolbar.addAction(reset_action)

        toolbar.addSeparator()
        toolbar.addAction(execute_action)

        # =========================================================
        # Menus
        # =========================================================

        menu_bar = self.menuBar()
        file_menu = QtWidgets.QMenu('&File', self)
        menu_bar.addMenu(file_menu)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(export_action)

        edit_menu = QtWidgets.QMenu('&Edit', self)

        align_menu = QtWidgets.QMenu('Align', self)
        align_menu.addAction(align_left_action)
        align_menu.addAction(align_center_action)
        align_menu.addAction(align_right_action)
        align_menu.addAction(align_top_action)
        align_menu.addAction(align_middle_action)
        align_menu.addAction(align_bottom_action)
        edit_menu.addMenu(align_menu)
        menu_bar.addMenu(edit_menu)

        create_menu = QtWidgets.QMenu('&Create', self)
        create_menu.addAction(create_graph_action)
        # create_menu.addAction(create_graph_for_sel_action)
        menu_bar.addMenu(create_menu)

        view_menu = QtWidgets.QMenu('&View', self)
        view_menu.addAction(refresh_action)
        menu_bar.addMenu(view_menu)

        help_menu = QtWidgets.QMenu('&Help', self)
        help_menu.addAction(help_action)
        menu_bar.addMenu(help_menu)

        work_area_widget = QtWidgets.QWidget(self)
        work_area_widget.setContentsMargins(0, 0, 0, 0)
        work_area_layout = QtWidgets.QVBoxLayout()
        work_area_widget.setLayout(work_area_layout)
        work_area_layout.setSpacing(0)

        self.tab_widget = QtWidgets.QTabWidget(work_area_widget)
        self.tab_widget.setTabsClosable(True)

        self.tab_widget.tabCloseRequested.connect(self.close_tab_cb)

        work_area_layout.addWidget(self.tab_widget)

        self.logging_widget = LoggingLine(work_area_widget)
        work_area_layout.addWidget(self.logging_widget)

        # right_side_panel = QtWidgets.QWidget(self)
        self.parameter_panel = ParameterWidget(self)
        self.parameter_panel.setMinimumWidth(130)

        self.graph_detail_widget = GraphParameterWidget(self)

        right_side_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        right_side_splitter.addWidget(self.parameter_panel)
        right_side_splitter.addWidget(self.graph_detail_widget)

        # Finish up splitter
        splitter = QtWidgets.QSplitter(self)
        splitter.addWidget(work_area_widget)
        splitter.addWidget(right_side_splitter)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        splitter.setStretchFactor(0, 9)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 100])

        main_layout.addWidget(splitter)

        main_graph = alib.create_graph(name=self.default_graph_name)
        self.add_graph_tab(main_graph, main_graph=True)

        # =========================================================
        # Connect Signals
        # =========================================================
        new_action.triggered.connect(self.new_graph_cb)
        save_action.triggered.connect(self.save_data_cb)
        save_as_action.triggered.connect(self.save_as_data_cb)
        open_action.triggered.connect(self.load_data_cb)
        export_action.triggered.connect(self.export_data_cb)
        execute_action.triggered.connect(self.main_graph_scene.execute)
        step_action.triggered.connect(self.main_graph_scene.step)
        resume_action.triggered.connect(self.main_graph_scene.resume)
        reset_action.triggered.connect(self.main_graph_scene.reset_execution)
        refresh_action.triggered.connect(self.refresh_library)

        # Alignment actions
        align_center_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kCenter))

        align_left_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kLeft))

        align_right_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kRight))

        align_top_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kTop))

        align_middle_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kMiddle))

        align_bottom_action.triggered.connect(
            lambda: self.current_scene.align_selected_items(
                GraphicScene.AlignmentMethod.kBottom))

        create_graph_action.triggered.connect(
            lambda: self.current_view.create_graph_cb())
        help_action.triggered.connect(self.open_help_link)

        self.tab_widget.currentChanged.connect(self.tab_changed_cb)
        manager.SignalManager.tab_opened_signal.connect(self.add_graph_tab)
        manager.SignalManager.graph_updated_signal.connect(
            self.refresh_graph_status)

        manager.SignalManager.parameter_connection_changed_signal.connect(
            self.update_parameter_connection_cb
        )
        manager.SignalManager.file_to_open_signal.connect(
            self.open_file_cb
        )
        manager.SignalManager.focus_on_item_signal.connect(
            self.focus_on_item_cb
        )

    @property
    def current_file_path(self):
        return self.__current_file_path

    @current_file_path.setter
    def current_file_path(self, val):
        self.__current_file_path = val
        if self.__current_file_path:
            self.setWindowTitle("MHY Protostar: `{}`".format(self.__current_file_path))
        else:
            self.setWindowTitle("MHY Protostar: *")

    @property
    def main_graph(self):
        return self.graph_tabs[0]['graph']

    @property
    def main_graph_view(self):
        return self.graph_tabs[0]['view']

    @property
    def main_graph_scene(self):
        return self.graph_tabs[0]['scene']

    @property
    def current_scene(self):
        current = self.tab_widget.currentIndex()
        return self.graph_tabs[current]['scene']

    @property
    def current_view(self):
        current = self.tab_widget.currentIndex()
        return self.graph_tabs[current]['view']

    def add_graph_tab(self, graph, main_graph=False, switch_tab=True):
        """

        Args:
            graph:
            main_graph:
            switch_tab(bool): If switching active tab to the created one

        Returns:

        """
        found = False
        active_index = self.tab_widget.currentIndex()

        # Check if the graph has already been open
        # If so, set the active index to that tab
        for idx, i in enumerate(self.graph_tabs):
            g = i.get('graph', None)
            if g == graph:
                found = True
                active_index = idx
                break

        if not found:
            graph_name = graph.long_name
            node_scene = GraphicScene(graph)
            node_view = GraphicView(node_scene, parent=self)

            self.graph_tabs.append({'graph': graph,
                                    'view': node_view,
                                    'scene': node_scene})
            if main_graph:
                graph_name = '*{}*'.format(graph_name)
            self.tab_widget.addTab(node_view, graph_name)
            tab_bar = self.tab_widget.tabBar()

            count = tab_bar.count()
            if main_graph:
                tab_bar.setTabButton(
                    count-1,
                    QtWidgets.QTabBar.LeftSide,
                    None
                )

                tab_bar.setTabButton(
                    count-1,
                    QtWidgets.QTabBar.RightSide,
                    None
                )
            node_scene.populate_graph()
            node_scene.selection_changed.connect(
                self.parameter_panel.refresh_param_widgets)
            count = tab_bar.count()
            active_index = count-1

        if switch_tab:
            self.set_active_tab(active_index)
        return self.graph_tabs[active_index]

    def set_active_tab(self, index):
        self.tab_widget.setCurrentIndex(index)
        self.tab_changed_cb(index)

    def refresh_param_widget_cb(self, items=None):
        if items is None:
            items = self.current_scene.selectedItems()
        self.parameter_panel.refresh_param_widgets(items)

    def update_parameter_connection_cb(self, parameter):
        if not parameter:
            return
        owner = parameter.owner
        if not owner:
            return
        graph = owner.graph
        for idx, i in enumerate(self.graph_tabs):
            g = i.get('graph', None)
            scene = i.get('scene')
            view = i.get('view')
            if g == graph:
                node = scene.find_item(owner.name)
                parameter_item = node.get_param_item(parameter.name)
                parameter_item.rebuild_connections(
                    source=True,
                    destinations=True
                )
                view.refresh_line_items_cb()

        self.refresh_param_widget_cb()

    def save_data_cb(self):
        if not self.current_file_path:
            return self.save_as_data_cb()
        else:
            export_file = self.current_file_path

        self.export_data(
            graph_node=self.main_graph,
            path=export_file, tab_data=True)
        self.current_file_path = export_file
        Window.default_export_path = os.path.dirname(export_file)

    def save_as_data_cb(self):
        file_dialog = QtWidgets.QFileDialog(
            self, "Save Protostar Data", Window.default_export_path)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setNameFilters([Window.file_ext_filter])
        result = file_dialog.exec_()
        if result:
            export_file = file_dialog.selectedFiles()[0]
        else:
            return

        self.export_data(
            graph_node=self.main_graph,
            path=export_file, tab_data=True)
        self.current_file_path = export_file
        Window.default_export_path = os.path.dirname(export_file)

    def get_tab_data(self):
        ui_data = {'ui_data': {'tabs': []}}
        for i in self.graph_tabs:
            view = i['view']
            graph_long_name = i['graph'].long_name
            view_center = view.mapToScene(view.viewport().rect().center())

            transform = i['view'].transform()

            view_transform = [
                transform.m11(),
                transform.m12(),
                transform.m13(),
                transform.m21(),
                transform.m22(),
                transform.m23(),
                transform.m31(),
                transform.m32(),
                transform.m33(),
            ]
            ui_data['ui_data']['tabs'].append({
                'long_name': graph_long_name,
                'transform': view_transform,
                'center': (view_center.x(), view_center.y())
            })

        ui_data['ui_data']['active_tab'] = self.current_scene.graph.long_name
        return ui_data

    def set_ui_data(self, data):
        main_graph = self.main_graph
        tab_data = data.get('tabs')
        if tab_data:
            for i in tab_data:
                long_name = i['long_name']
                graph = self.find_graph_from_long_name(main_graph, long_name)
                if graph:
                    tab_data = self.add_graph_tab(graph, switch_tab=False)
                    view = tab_data['view']
                    transform = QtGui.QTransform(*i['transform'])
                    tab_data['view'].setTransform(transform)
                    center = i['center']
                    view.centerOn(*center)
                    view.update_center()
        active_tab = data.get('active_tab')
        if active_tab:
            for idx, tab in enumerate(self.graph_tabs):
                graph = tab['graph']
                if graph.long_name == active_tab:
                    self.set_active_tab(idx)
                    return

    def load_data_cb(self):
        if self.main_graph_scene.items():
            result = QtWidgets.QMessageBox.question(
                self,
                "Open Graph",
                "Open graph file will override current graph views."
                " Are you sure?")
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        file_dialog = QtWidgets.QFileDialog(
            self, "Load Protostar Data", Window.default_export_path)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        file_dialog.setNameFilters([Window.file_ext_filter])
        result = file_dialog.exec_()
        if result:
            file_to_load = file_dialog.selectedFiles()
            file_to_load = [file_path.replace('\\', '/') for
                            file_path in file_to_load]
        else:
            return

        file_path = file_to_load[0]
        self.open_file_cb(file_path, prompt=False)

    def open_file_cb(self, file_path, prompt=True):
        if prompt:
            result = QtWidgets.QMessageBox.question(
                self,
                "Open Graph",
                "Open graph file will override current graph views."
                " Are you sure?")
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        file_path = file_path.replace('\\', '/')
        if os.path.isfile(file_path):
            self.current_file_path = file_path
            self.load_graph(file_path)
        else:
            logging.warning('{} is not a valid file path'.format(file_path))
            return
        Window.default_export_path = os.path.dirname(file_path)

    def new_graph_cb(self, prompt=True):
        if prompt and self.main_graph_scene.items():
            result = QtWidgets.QMessageBox.question(
                self,
                "New Graph",
                "Starting a new graph will override current graph views."
                " Are you sure?")
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        self.current_file_path = None
        self.load_graph(None)

    def load_graph(self, data):
        for idx in range(self.tab_widget.count(), 1, -1):
            print(idx)
            self.graph_tabs.pop(idx-1)
            self.tab_widget.removeTab(idx-1)

        self.main_graph.clear_objects(force=True)

        data = self.main_graph_view.load_data(data)
        if isinstance(data, string_types) and os.path.isfile(data):
            Window.default_export_path = os.path.dirname(data)
        self.update_tab_name(0, self.main_graph_scene.graph.name)
        self.graph_tabs[0]['graph'] = self.main_graph_scene.graph

        if 'ui_data' not in data:
            self.main_graph_view.frame_items()
        else:
            self.set_ui_data(data['ui_data'])
        manager.SignalManager.repaint_lines_signal.emit()

    def export_data_cb(self):
        sel = self.current_scene.selectedItems()
        if not sel:
            sel = [self.main_graph]
        graph_items = []
        for i in sel:
            if i.type_name == 'node' and i.is_graph:
                graph_items.append(i)

        if len(graph_items) > 1:
            QtWidgets.QMessageBox.warning(
                self,
                "More than one graph selected",
                "Please select one graph node only")
            return
        if not graph_items:
            QtWidgets.QMessageBox.warning(
                self,
                "No graph selected",
                "No graph node selected, main graph will be exported")
            graph_node = self.main_graph
        else:
            graph_node = graph_items[0]
        file_dialog = QtWidgets.QFileDialog(
            self,
            "Export Protostar Data",
            Window.default_export_path
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setNameFilters([Window.file_ext_filter])
        result = file_dialog.exec_()
        if result:
            export_file = file_dialog.selectedFiles()[0]
        else:
            return
        file_name = os.path.basename(export_file).split('.')[0]
        data = self.export_data(graph_node=graph_node, path=None)
        data['name'] = file_name
        with open(export_file, 'w+') as f:
            json.dump(data, f, indent=2)

        Window.default_export_path = os.path.dirname(export_file)

    def export_data(self, graph_node=None, path=None, tab_data=False):
        if graph_node is None:
            graph_node = self.main_graph
        for i in self.graph_tabs:
            i['scene'].sync_ui_data()
        data = graph_node._get_data()
        if tab_data:
            tab_ui_data = self.get_tab_data()
            if 'ui_data' not in data:
                data['ui_data'] = {}
            data['ui_data'].update(tab_ui_data['ui_data'])

        if not path:
            return data
        d = os.path.split(path)[0]
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(path, 'w+') as f:
            json.dump(data, f, indent=2)
            logger.info(
                'Saved action graph "{}" to {}'.format(graph_node.name, path)
            )

        return data

    def refresh_library(self):
        data = self.export_data(None, None, tab_data=True)
        self.new_graph_cb(prompt=False)
        alib.refresh()
        self.load_graph(data)

    def update_tab_name(self, idx, graph_name):
        if idx == 0:
            graph_name = "*{}*".format(graph_name)
        self.tab_widget.setTabText(idx, graph_name)

    def close_tab_cb(self, idx):
        """
        Callback that close the tab at a specific index
        Args:
            idx:

        Returns:

        """
        if idx > 0:
            self.tab_widget.removeTab(idx)
            graph_dict = self.graph_tabs[idx]
            graph_scene = graph_dict.get('scene')
            if graph_scene:
                graph_scene.sync_ui_data()
            self.graph_tabs.pop(idx)

    def refresh_graph_status(self, graph):
        """
        Check if visible node in the active tag has promoted attribute changes.
        If so, refresh the node item
        Args:
            graph:

        Returns:

        """
        if not graph:
            return

        owner = graph.graph
        for idx, tab in enumerate(self.graph_tabs):
            scene = tab.get('scene')
            _graph = tab.get('graph')
            if _graph and graph == _graph:
                self.update_tab_name(idx, graph.name)
            if owner and _graph == owner:
                item = scene.find_item(graph.name)
                if item:
                    item.reload_parameters()

    def tab_changed_cb(self, index):
        """
        Called when active tab changed to refresh parameter widget based on
        selection
        Args:
            index(int): The index of current index

        """
        current = self.graph_tabs[index]

        for i in self.graph_tabs:
            i['scene'].active = False

        scene = current['scene']
        graph = current['graph']
        scene.active = True
        selected_items = scene.selectedItems()
        self.parameter_panel.refresh_param_widgets(selected_items)
        manager.SignalManager.reload_graph_parameters_signal.emit(graph)

    def focus_on_item_cb(self, item):
        if not item:
            return
        for idx, i in enumerate(self.graph_tabs):
            view = i['view']
            obj = view.find_item(item)
            if obj:
                self.tab_widget.setCurrentIndex(idx)
                view.frame_items(items=[obj])
                return

    @staticmethod
    def open_help_link():
        """
        Open the help link in webbrowser

        """
        html_root = os.environ.get('PROTOSTAR_HELP_HTML')
        full_path = os.path.join(html_root, 'what_is.html')
        if os.path.isfile(full_path):
            webbrowser.open(full_path, new=2)

    @staticmethod
    def find_graph_from_long_name(graph, long_name):
        graph_long_name = graph.long_name
        if graph_long_name == long_name:
            return graph
        if not long_name.startswith(graph_long_name):
            return
        remaining = long_name.replace(graph_long_name, '', 1)
        splits = remaining.split(':')
        splits = [i for i in splits if i]
        if splits:
            child_graph = graph.get_object(splits[0])
            if child_graph and child_graph.is_graph:
                return Window.find_graph_from_long_name(child_graph, long_name)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Window()
    w.resize(300, 300)
    w.show()
    sys.exit(app.exec_())
