import os

from maya import cmds

from mhy.qt.core import QtGui, QtCore, QtWidgets
import mhy.qt.core.utils as qtutil

from mhy.maya.nodezoo.constant import SurfaceAssociation
import mhy.maya.rig.workarea as wa
import mhy.maya.rig.data as dutil
import mhy.maya.rig.rig_global as rg

_LAST_PATH = None


class DataPushButton(QtWidgets.QPushButton):
    """
    Customized QPushButton for data IO.
    """

    def __init__(self, *args, **kwargs):
        super(DataPushButton, self).__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.create_context_menu)
        self.__trigger = None
        self.__file_ext = None

    def set_trigger(self, func, file_ext=None):
        """sets the triggers of this button."""
        self.clicked.connect(func)
        self.__trigger = func
        self.__file_ext = file_ext

    def create_context_menu(self):
        """Creates the right-click context menu."""
        if not self.__trigger:
            return

        menu = QtWidgets.QMenu(self)
        name = 'Load from '
        if 'save' in self.__trigger.__name__.lower():
            name = 'Save to '
        if self.__file_ext:
            name += 'File'
        else:
            name += 'Folder'

        action = menu.addAction(name)
        action.triggered.connect(self.manual_trigger)
        menu.popup(QtGui.QCursor.pos())

    def manual_trigger(self):
        """Ask the user to manually specify export/import path."""
        global _LAST_PATH

        act = 'Load'
        if 'save' in self.__trigger.__name__.lower():
            act = 'Save'

        path = _LAST_PATH if _LAST_PATH else 'C:/'

        if self.__file_ext:
            if act == 'Load':
                result = QtWidgets.QFileDialog.getOpenFileName(
                    self, act, path, '{0} (*.{0})'.format(self.__file_ext))[0]
            else:
                result = QtWidgets.QFileDialog.getSaveFileName(
                    self, act, path, '{0} (*.{0})'.format(self.__file_ext))[0]
        else:
            result = QtWidgets.QFileDialog.getExistingDirectory(
                self, act, path)

        if result:
            self.__trigger(path=result)
            if os.path.isdir(result):
                _LAST_PATH = result
            else:
                _LAST_PATH = os.path.dirname(result)


class DataWidget(QtWidgets.QWidget):
    """
    A widget for rig data export/import.
    """

    def __init__(self, *args, **kwargs):
        super(DataWidget, self).__init__(*args, **kwargs)

        central_layout = QtWidgets.QVBoxLayout()
        self.setLayout(central_layout)

        widget = QtWidgets.QGroupBox('Project Settings')
        central_layout.addWidget(widget)
        grid = QtWidgets.QGridLayout()
        widget.setLayout(grid)

        grid.addWidget(QtWidgets.QLabel('Workarea: '), 0, 0, 1, 1)
        self.le_workarea = QtWidgets.QLineEdit()
        grid.addWidget(self.le_workarea, 0, 1, 1, 1)
        self.btn_browse = QtWidgets.QPushButton()
        self.btn_browse.setIcon(qtutil.get_icon(':/openLoadGeneric.png'))
        grid.addWidget(self.btn_browse, 0, 2, 1, 1)
        self.btn_browse.clicked.connect(self.browse_workarea)

        grid.addWidget(QtWidgets.QLabel('Project: '), 1, 0, 1, 1)
        self.le_project = QtWidgets.QLineEdit()
        grid.addWidget(self.le_project, 1, 1, 1, 2)

        grid.addWidget(QtWidgets.QLabel('Character: '), 2, 0, 1, 1)
        self.le_char = QtWidgets.QLineEdit()
        grid.addWidget(self.le_char, 2, 1, 1, 2)

        grid.addWidget(QtWidgets.QLabel('Rig Type: '), 3, 0, 1, 1)
        hbox = QtWidgets.QHBoxLayout()
        grid.addLayout(hbox, 3, 1, 1, 2)

        self.rb_type_body = QtWidgets.QRadioButton('Body')
        hbox.addWidget(self.rb_type_body)
        self.rb_type_face = QtWidgets.QRadioButton('Face')
        hbox.addWidget(self.rb_type_face)
        self.rb_type_body.setChecked(True)

        hbox.addStretch(10)

        self.btn_make_workarea = QtWidgets.QPushButton('Make Workarea')
        self.btn_make_workarea.setIcon(qtutil.get_icon(':/folder-new.png'))
        hbox.addWidget(self.btn_make_workarea)
        self.btn_make_workarea.clicked.connect(self.make_workarea)

        hbox = QtWidgets.QHBoxLayout()
        central_layout.addLayout(hbox)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        hbox.addWidget(QtWidgets.QLabel('Deformer Export Method: '))
        self.cbx_export_method = QtWidgets.QComboBox()
        self.cbx_export_method.addItems(('both', 'compressed', 'uncompressed'))
        hbox.addWidget(self.cbx_export_method)

        hbox.addWidget(QtWidgets.QLabel('Deformer Import Method: '))
        self.cbx_import_method = QtWidgets.QComboBox()
        self.cbx_import_method.addItems(SurfaceAssociation.items())
        hbox.addWidget(self.cbx_import_method)

        hbox.addStretch(10)

        hbox = QtWidgets.QHBoxLayout()
        central_layout.addLayout(hbox)

        gbox = QtWidgets.QGroupBox('Export')
        hbox.addWidget(gbox)
        vbox_exp = QtWidgets.QVBoxLayout()
        gbox.setLayout(vbox_exp)

        gbox = QtWidgets.QGroupBox('Import')
        hbox.addWidget(gbox)
        vbox_imp = QtWidgets.QVBoxLayout()
        gbox.setLayout(vbox_imp)

        icon = qtutil.get_icon(':/HIKCustomRigToolTranslate.png')
        self.btn_marker_save = DataPushButton('Save Markers')
        self.btn_marker_save.setIcon(icon)
        self.btn_marker_save.set_trigger(self.save_markers, 'json')
        vbox_exp.addWidget(self.btn_marker_save)
        self.btn_marker_load = DataPushButton('Load Markers')
        self.btn_marker_load.setIcon(icon)
        self.btn_marker_load.set_trigger(self.load_markers, 'json')
        vbox_imp.addWidget(self.btn_marker_load)

        icon = qtutil.get_icon(':/HIKcreateControlRig.png')
        self.btn_ctrl_save = DataPushButton('Save Ctrl Shapes')
        self.btn_ctrl_save.setIcon(icon)
        self.btn_ctrl_save.set_trigger(self.save_ctrl_data, 'json')
        vbox_exp.addWidget(self.btn_ctrl_save)
        self.btn_ctrl_load = DataPushButton('Load Ctrl Shapes')
        self.btn_ctrl_load.setIcon(icon)
        self.btn_ctrl_load.set_trigger(self.load_ctrl_data, 'json')
        vbox_imp.addWidget(self.btn_ctrl_load)

        icon = qtutil.get_icon(':/exportSmoothSkin.png')
        self.btn_dfm_save = DataPushButton('Save Deformers')
        self.btn_dfm_save.setIcon(icon)
        self.btn_dfm_save.set_trigger(self.save_deformers)
        vbox_exp.addWidget(self.btn_dfm_save)
        icon = qtutil.get_icon(':/importSmoothSkin.png')
        self.btn_dfm_load = DataPushButton('Load Deformers')
        self.btn_dfm_load.setIcon(icon)
        self.btn_dfm_load.set_trigger(self.load_deformers)
        vbox_imp.addWidget(self.btn_dfm_load)

        icon = qtutil.get_icon(':/out_objectSet.png')
        self.btn_set_save = DataPushButton('Save Export Set Data')
        self.btn_set_save.setIcon(icon)
        self.btn_set_save.set_trigger(self.save_set_data)
        vbox_exp.addWidget(self.btn_set_save)
        self.btn_set_load = DataPushButton('Load Export Set Data')
        self.btn_set_load.setIcon(icon)
        self.btn_set_load.set_trigger(self.load_set_data)
        vbox_imp.addWidget(self.btn_set_load)

    def __get_path_args(self):
        """Returns the path arguments from the current project settings."""
        workarea = self.le_workarea.text()
        project = self.le_project.text()
        char = self.le_char.text()
        rig_type = 'body' if self.rb_type_body.isChecked() else 'face'

        args = (workarea, project, char)
        kwargs = {'rig_type': rig_type}

        return args, kwargs

    def is_config_matching(self):
        """Checks if the asset in the scene matches
        the current project config settings.

        Returns the status
        """
        status = True

        rig = rg.RigGlobal.get_rigs()
        if len(rig) != 1:
            cmds.warning('More than 1 rig found in the scene.')
            status = False
        elif rig[0].namespace:
            cmds.warning('Rig is referenced.')
            status = False

        rig = rig[0]
        if rig.project_name:
            project_name = self.le_project.text()
            char_name = self.le_char.text()
            rig_type = 'body' if self.rb_type_body.isChecked() else 'face'
            if project_name != rig.project_name or \
               char_name != rig.char_name or \
               rig_type != rig.rig_type:
                status = False

        if not status:
            result = QtWidgets.QMessageBox.question(
                self,
                'Warning',
                ('Rig in the scene doesn\'t match the project settings... '
                 'Continue anyway?'))
            return result == QtWidgets.QMessageBox.StandardButton.Yes

        return status

    @QtCore.Slot()
    def browse_workarea(self):
        """Pops up a file dialog for the user to specify the workarea path."""
        path = self.le_workarea.text().replace('\\', '/')
        if not os.path.isdir(path):
            path = 'C:/'

        result = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Asset Workarea', path)

        if result:
            result.replace('\\', '/')
            self.le_workarea.setText(result)

    @QtCore.Slot()
    def make_workarea(self):
        """Creates folders for the specified workarea."""
        args, kwargs = self.__get_path_args()
        wa.create_workarea(*args, **kwargs)

    @QtCore.Slot()
    def save_markers(self, path=None):
        """Saves marker data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.marker_data_file(*args, **kwargs)
        dutil.export_marker_data(path)

    @QtCore.Slot()
    def load_markers(self, path=None):
        """Loads marker data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.marker_data_file(*args, **kwargs)
        dutil.import_marker_data(path)

    @QtCore.Slot()
    def save_ctrl_data(self, path=None):
        """Saves ctrl shape data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.ctrl_data_file(*args, **kwargs)
        dutil.export_ctrl_data(path)

    @QtCore.Slot()
    def load_ctrl_data(self, path=None):
        """Loads ctrl shape data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.ctrl_data_file(*args, **kwargs)
        dutil.import_ctrl_data(path)

    @QtCore.Slot()
    def save_deformers(self, path=None):
        """Saves deformer data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.deformer_path(*args, **kwargs)
        method = self.cbx_export_method.currentIndex()
        if method == 0:
            kwargs = {'compressed': True, 'uncompressed': True}
        elif method == 1:
            kwargs = {'compressed': True, 'uncompressed': False}
        else:
            kwargs = {'compressed': False, 'uncompressed': True}
        dutil.export_rig_deformer_data(path, **kwargs)

    @QtCore.Slot()
    def load_deformers(self, path=None):
        """Loads deformer data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.deformer_path(*args, **kwargs)
        method = self.cbx_import_method.currentText()
        dutil.import_rig_deformer_data(path, method=method)

    @QtCore.Slot()
    def save_set_data(self, path=None):
        """Saves ctrl shape data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.set_data_file(*args, **kwargs)
        dutil.export_set_data(path)

    @QtCore.Slot()
    def load_set_data(self, path=None):
        """Loads ctrl shape data."""
        if not self.is_config_matching():
            return

        if not path:
            args, kwargs = self.__get_path_args()
            wa.create_workarea(*args, **kwargs)
            path = wa.set_data_file(*args, **kwargs)
        dutil.import_set_data(path)
