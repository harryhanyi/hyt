import os
import tempfile
import shutil
import subprocess

from mhy.qt.core import QtWidgets, QtCore, QtGui
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

import mhy.maya.rigtools.deformer_decompose.ui.manager as manager
import mhy.maya.rigtools.deformer_decompose.ui.dialog as dialog
import mhy.maya.nodezoo.utils as utils
import mhy.maya.rigtools.deformer_decompose.api.share as share

settingIconPath = os.path.join(os.path.dirname(manager.__file__), 'icons', 'setting.png')


class ExportImportWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        main_layout = QtWidgets.QVBoxLayout()
        content_layout = QtWidgets.QGridLayout(self)
        box = QtWidgets.QGroupBox("Import/Export")
        box.setLayout(content_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.quickPathCheckBox = QtWidgets.QCheckBox("Use Quick Path")
        self.quickPathCheckBox.setToolTip("Save data to local temp folder")
        self.quickPathCheckBox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.quickPathCheckBox.customContextMenuRequested.connect(self.quick_path_context_menu)
        self.quickPathCheckBox.setChecked(True)

        import_button = QtWidgets.QPushButton("&Import")
        import_config_button = QtWidgets.QPushButton(QtGui.QIcon(settingIconPath), "")
        import_config_button.setFixedSize(32, 32)
        import_to_sel_button = QtWidgets.QPushButton("Import To Selected")
        import_to_sel_button.setToolTip("Import data to selected object(s)")
        import_to_sel_config_button = QtWidgets.QPushButton(QtGui.QIcon(settingIconPath), "")
        import_to_sel_config_button.setFixedSize(32, 32)

        export_button = QtWidgets.QPushButton("&Export")
        export_config_button = QtWidgets.QPushButton(QtGui.QIcon(settingIconPath), "")
        export_config_button.setFixedSize(32, 32)

        content_layout.addWidget(self.quickPathCheckBox, 0, 0)
        content_layout.addWidget(import_button, 1, 0)
        content_layout.addWidget(import_config_button, 1, 1)
        content_layout.addWidget(import_to_sel_button, 2, 0)
        content_layout.addWidget(import_to_sel_config_button, 2, 1)
        content_layout.addWidget(export_button, 3, 0)
        content_layout.addWidget(export_config_button, 3, 1)
        main_layout.addWidget(box)
        export_button.clicked.connect(self.do_export)
        export_config_button.clicked.connect(self.launch_export_config_ui)
        import_to_sel_button.clicked.connect(self.import_to_sel_button)
        import_to_sel_config_button.clicked.connect(self.launch_import_to_sel_config_ui)
        import_button.clicked.connect(self.do_import)
        import_config_button.clicked.connect(self.launch_import_config_ui)

    def quick_path_context_menu(self):
        menu = QtWidgets.QMenu(self)
        open_quick_path_action = QtWidgets.QAction("Open", self)
        open_quick_path_action.triggered.connect(open_quick_path)
        menu.addAction(open_quick_path_action)
        menu.exec_(QtGui.QCursor.pos())

    def launch_export_config_ui(self):
        ui = dialog.ExportConfig(self)
        ui.exec_()

    def launch_import_config_ui(self):
        ui = dialog.ImportConfig(self)
        ui.exec_()

    def launch_import_to_sel_config_ui(self):
        ui = dialog.ImportToSelConfig(self)
        ui.exec_()

    def do_import(self):
        import_config = manager.Current_Config['import']
        if_connection = import_config.get('connection', 1)
        if_creation = import_config.get('creationData', 1)
        name_map = import_config.get('nameMap')
        namespace_map = import_config.get('namespaceMap')

        if self.quickPathCheckBox.isChecked():
            files_to_import = []
            export_dir = os.path.join(tempfile.gettempdir(), "nodezooData")
            for filename in os.listdir(export_dir):
                file_path = os.path.join(export_dir, filename)
                if file_path.endswith('.nzd') or file_path.endswith('.gnzd'):
                    file_path = file_path.replace('\\', '/')
                    files_to_import.append(file_path)
        else:
            fileDialog = QtWidgets.QFileDialog(self)
            fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            fileDialog.setNameFilters(["Compressed Nodezoo files (*.gnzd)",
                                       "Nodezoo files (*.nzd)"])
            fileDialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
            result = fileDialog.exec_()
            if result:
                files_to_import = fileDialog.selectedFiles()
                files_to_import = [file_path.replace('\\', '/') for file_path in files_to_import]
            else:
                return

        utils.import_node_data(files_to_import, create_node=if_creation,
                               make_connections=if_connection, name_map=name_map,
                               namespace_map=namespace_map, ui=True)

    def import_to_sel_button(self):
        """
        Import data from a file to selected objects

        Returns:

        """

        # Firstly, get the data file path
        if self.quickPathCheckBox.isChecked():
            files_to_import = []
            export_dir = os.path.join(tempfile.gettempdir(), "nodezooData")
            for filename in os.listdir(export_dir):
                file_path = os.path.join(export_dir, filename)
                if file_path.endswith('.nzd') or file_path.endswith('.gnzd'):
                    files_to_import.append(file_path)
            if not files_to_import:
                QtWidgets.QMessageBox.critical(None, 'No source files',
                                               "Found no source file in the quick path: '{}'.\n"
                                               "It supports importing to selected object"
                                               " from data of one node only.".format(export_dir))
                return
            elif len(files_to_import) > 1:
                QtWidgets.QMessageBox.critical(None, 'Invalid source files',
                                               "Found more than 1 file in the quick path: '{}'.\n"
                                               "It supports importing to selected object"
                                               " from data of one node only.".format(export_dir))
                return
            file_path = files_to_import[0]
        else:
            file_dialog = QtWidgets.QFileDialog(self)
            files_to_import = file_dialog.getOpenFileName(self, 'Select data to import', "",
                                                          "Compressed Nodezoo files (*.gnzd);;Nodezoo files (*.nzd)")
            file_path = files_to_import[0]
            if not file_path:
                return

        file_path = file_path.replace('\\', '/')

        # Secondly, check there is data only for one node in the file
        data = utils.inspect_data_file(file_path)
        nodes = data.get('nodes')
        if not nodes:
            QtWidgets.QMessageBox.critical(None, 'No Data',
                                           "File '{}' has no node information".format(file_path))
            return
        if len(nodes) > 1:
            QtWidgets.QMessageBox.critical(None, 'More than one',
                                           "File '{}' has more than one node".format(file_path))
            return

        node_data = nodes[0]

        node_type = node_data.get('type')

        sel = cmds.ls(sl=True)
        transfer_config = manager.Current_Config.get('transfer', manager.Default_Config['transfer'])
        surface_association = transfer_config.get("surfaceAssociation", "closestPoint")
        if node_type == 'skinCluster':
            normalize = transfer_config.get("normalize", True)
            influence_association = transfer_config.get("influenceAssociation", None)
            share.load_skin_to_objects(node_data, sel, surface_association=surface_association,
                                       influence_association=influence_association, normalize=normalize,
                                       ui=True)

        elif node_type == "blendShape":
            share.load_blendshape_to_objects(node_data, sel, surface_association=surface_association, ui=True)

        elif node_type == "cluster":
            share.load_cluster_to_objects(node_data, sel, surface_association=surface_association, ui=True)
        else:
            QtWidgets.QMessageBox.critical(None, 'Not implemented',
                                           "Data type '{}' is not currently supported".format(node_type))
            return

    def do_export(self):
        export_dir = ""
        export_file = ""
        export_config = manager.Current_Config['export']
        if_multiple_file = export_config.get('multipleFiles', 0)
        if_weight_only = export_config.get('weightsOnly', 0)
        if_connection = export_config.get('connection', 1)
        if_compress = export_config.get('compress', 1)

        if self.quickPathCheckBox.isChecked():

            if if_multiple_file:
                export_dir = os.path.join(tempfile.gettempdir(), "nodezooData")
            elif if_compress:
                export_file = os.path.join(tempfile.gettempdir(), "nodezooData", "tmpData.gnzd")
            else:
                export_file = os.path.join(tempfile.gettempdir(), "nodezooData", "tmpData.nzd")

        else:
            file_dialog = QtWidgets.QFileDialog(self)
            if if_multiple_file:
                file_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
                result = file_dialog.exec_()
                if result:
                    export_dir = file_dialog.selectedFiles()[0]
                else:
                    return
            else:
                file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
                if if_compress:
                    file_dialog.setNameFilters(["Compressed Nodezoo files (*.gnzd)"])
                else:
                    file_dialog.setNameFilters(["Nodezoo files (*.nzd)"])
                result = file_dialog.exec_()
                if result:
                    export_file = file_dialog.selectedFiles()[0]
                else:
                    return

        # Fetch data from the list view and maya scene
        sel_model = manager.Node_List_View.selectionModel()
        selected_rows = sel_model.selectedRows()
        proxy_model = manager.Node_List_View.model()
        sel_list = []
        for row in selected_rows:
            source_index = proxy_model.mapToSource(row)
            item = source_index.data(QtCore.Qt.UserRole)
            if cmds.objExists(item.name):
                sel_list.append(item.name)
            else:
                OpenMaya.MGlobal.displayWarning('{} does not exists in the scene'.format(item.name))

        sel_list = list(set(sel_list))

        nodes = utils.ls(sel_list)

        if self.quickPathCheckBox.isChecked():
            # Clear existing temp files in quick path
            clear_tmp_folder()

        if if_multiple_file:
            export_dir = export_dir.replace('\\', '/')
            utils.export_node_data_to_multiple_files(nodes,
                                                     export_dir,
                                                     compress=if_compress,
                                                     connection_data=if_connection,
                                                     ui=True,
                                                     weight_only=if_weight_only)
        else:
            export_file = export_file.replace('\\', '/')
            utils.export_node_data(nodes,
                                   export_file,
                                   compress=if_compress,
                                   connection_data=if_connection,
                                   ui=True,
                                   weight_only=if_weight_only)


def clear_tmp_folder():
    """
    Clear the files in temp directory folder

    """
    tmp_dir = os.path.join(tempfile.gettempdir(), "nodezooData")
    if not os.path.exists(tmp_dir):
        return
    for filename in os.listdir(tmp_dir):
        file_path = os.path.join(tmp_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            OpenMaya.MGlobal.displayError('Failed to delete %s. Reason: %s' % (file_path, str(e)))


def open_quick_path():
    tmp_dir = os.path.join(tempfile.gettempdir(), "nodezooData")
    if not os.path.exists(tmp_dir):
        return
    command = 'explorer "{}"'.format(tmp_dir)
    subprocess.Popen(command)




