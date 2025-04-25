"""
This is the main window of animation library.
"""
from PySide2 import QtWidgets, QtCore
import mhy.maya.anim_lib.widgets.item_widget as iw
import mhy.maya.anim_lib.widgets.attribute_widget as aw
import mhy.maya.anim_lib.file_browser.file_widget as fw
import mhy.maya.anim_lib.manager as manager
import mhy.maya.anim_lib.widgets.pose_creation_dialog as pcd
from mhy.maya.anim_lib.utils import resolve_root_paths

import mhy.qt.core.base_main_window as mw
base_class = mw.get_window_class(app_name='MHY Anim Lib')


class Window(base_class):
    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("MHY Anim Library")

        menu_bar = self.menuBar()
        file_menu = QtWidgets.QMenu('&File', self)
        menu_bar.addMenu(file_menu)

        create_menu = QtWidgets.QMenu("Create", self)
        menu_bar.addMenu(create_menu)
        create_pose_action = QtWidgets.QAction("Pose", self)
        create_menu.addAction(create_pose_action)
        create_anim_action = QtWidgets.QAction("Animation", self)
        create_menu.addAction(create_anim_action)

        create_pose_action.triggered.connect(lambda: self.launch_pose_creation_dialog(True))
        create_anim_action.triggered.connect(lambda: self.launch_pose_creation_dialog(False))
        menu_bar.addMenu(create_menu)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, parent=self)
        file_browser = fw.FileTreeWidget(self)
        pose_item_view = iw.ItemWidget(self)
        attribute_view = aw.AttibuteWidget(self)

        splitter.addWidget(file_browser)
        splitter.addWidget(pose_item_view)
        splitter.addWidget(attribute_view)

        main_layout.addWidget(splitter)

        lib = fw.Library()
        data_roots = resolve_root_paths()
        for i in data_roots:
            lib.add_root(i)
        file_browser.set_library(lib)

    def launch_pose_creation_dialog(self, static):
        """
        Launch pose creation dialog
        Args:
            static(bool): If creating animation data or pose data

        """
        if not manager.current_path:
            QtWidgets.QMessageBox.critical(self,
                                           'No Path Selected',
                                           'Please selected a path from the file browser to create pose to')
            return

        if static:
            title = 'Create Pose'
        else:
            title = 'Create Animation'
        ui = pcd.PoseCreationDialog(title=title, static=static, parent=self)
        ui.set_root_path(manager.current_path)
        ui.show()


def launch():
    Window.launch()
