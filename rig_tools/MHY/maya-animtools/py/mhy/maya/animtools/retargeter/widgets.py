import os
import subprocess
from functools import partial

from maya import cmds

from mhy.qt.core import QtWidgets, QtGui, QtCore
import mhy.qt.core.widgets.dialogs as dlg

import mhy.maya.scene as sutil

import mhy.maya.anim.retarget.utils as util
import mhy.maya.animtools.retargeter.thread as thd


DEFAULT_PATH = ''
COLOR_HAS_CONFIG = QtGui.QColor(100, 180, 250)
COLOR_NO_CONFIG = QtGui.QColor(250, 250, 250)


class MayaFileWidgetGroup(object):
    """A goup of widgets interfacing a Maya file path.

    It contains a label, a line edit, a button for browsing files,
    and a button for opening the file in Maya.
    """

    _FILE_FILTER = 'Maya Files (*.ma *.mb)'

    def __init__(
            self, pixmap, label, grid, row=0,
            default=None, placeholder=None, *args, **kwargs):
        """Initialization.

        Args:
            label (string): The label string
            grid (QGridLayout): The grid layout to add widgets to.
            row (int): Which row in the grid to add the widgets to?
            default (string): The default path.
        """
        super(MayaFileWidgetGroup, self).__init__(*args, **kwargs)

        self.default = default if default is not None else DEFAULT_PATH

        self.pixmap = QtWidgets.QLabel()
        self.pixmap.setPixmap(pixmap)
        grid.addWidget(self.pixmap, row, 0, 1, 1)
        self.label = QtWidgets.QLabel()
        self.label.setText(label + ':')
        grid.addWidget(self.label, row, 1, 1, 1)
        grid.setAlignment(self.pixmap, QtCore.Qt.AlignCenter)
        grid.setAlignment(self.label, QtCore.Qt.AlignRight)

        self.le_path = QtWidgets.QLineEdit()
        if placeholder:
            self.le_path.setPlaceholderText(placeholder)
        grid.addWidget(self.le_path, row, 2, 1, 1)
        self.le_path.editingFinished.connect(self.validate_path)

        self.btn_browse = QtWidgets.QPushButton()
        self.btn_browse.setIcon(QtGui.QIcon(':/advancedSettings.png'))
        self.btn_browse.setToolTip('Pick a file in File Explorer.')
        grid.addWidget(self.btn_browse, row, 3, 1, 1)
        self.btn_browse.clicked.connect(self.browse)

        self.btn_open = QtWidgets.QPushButton()
        self.btn_open.setIcon(QtGui.QIcon(':/mayaIcon.png'))
        self.btn_open.setToolTip('Open File.')
        grid.addWidget(self.btn_open, row, 4, 1, 1)
        self.btn_open.clicked.connect(self.open)

        self.file_path = self.default

    @property
    def file_path(self):
        """ Returns the file path. """
        return self.le_path.text()

    @file_path.setter
    def file_path(self, p):
        """ Sets the file path and validates it. """
        self.le_path.setText(p)
        self.validate_path()

    def validate_path(self):
        """ Validates this path. """
        p = self.file_path
        p = p.replace('\\', '/')
        self.le_path.setText(p)

    @QtCore.Slot()
    def browse(self):
        """ Opens a file browser to let the user pick a path. """
        path = os.path.split(self.le_path.text())[0]
        if os.path.isfile(path):
            path = os.path.split(path)[0]
        elif not os.path.isdir(path):
            path = self.default

        result = QtWidgets.QFileDialog.getOpenFileName(
            self.le_path, 'Pick a ' + self.label.text(),
            path, self._FILE_FILTER)[0]
        if result:
            self.file_path = result

    @QtCore.Slot()
    def open(self):
        """ Opens this file in Maya. """
        p = self.file_path
        if p and os.path.isfile(p):
            if dlg.prompt_scene_modified_dialog(self.le_path):
                cmds.file(p, open=True, f=True)


class ConfigFileWidgetGroup(MayaFileWidgetGroup):
    """A goup of widgets interfacing a retarget config file path.

    It contains a label, a line edit, a button for browsing files,
    and a button for opening the map dialog.
    """

    _FILE_FILTER = 'JSON (*.json)'

    def __init__(self, *args, **kwargs):
        super(ConfigFileWidgetGroup, self).__init__(*args, **kwargs)
        self.btn_open.setIcon(QtGui.QIcon(':/SP_FileIcon.png'))

    @property
    def widgets(self):
        return (self.label, self.le_path, self.btn_browse, self.btn_open)

    @QtCore.Slot()
    def open(self):
        """Opens this file in the default text editor."""
        p = self.le_path.text()
        if not p:
            p = QtWidgets.QFileDialog.getSaveFileName(
                self.le_path, 'Create a Retarget Config File',
                DEFAULT_PATH, self._FILE_FILTER)[0]
            if not p:
                return

        if not p.endswith('json'):
            util.log_warn('Invalid config file type: {}'.format(p))
            return

        if not os.path.isfile(p):
            with open(p, 'w+') as f:
                f.writelines(['{\n}'])

        if os.path.isfile(p):
            os.startfile(p)

        self.le_path.setText(p)
        self.validate_path()


class FolderWidegtGroup(MayaFileWidgetGroup):
    """A goup of widgets interfacing a folder path.

    It contains a label, a line edit, a button for browsing files,
    and a button for opening the folder in a file browser.
    """

    def __init__(self, *args, **kwargs):
        super(FolderWidegtGroup, self).__init__(*args, **kwargs)
        self.btn_browse.setToolTip('Pick a directory in File Explorer.')
        self.btn_open.setIcon(QtGui.QIcon(':/fileOpen.png'))
        self.btn_open.setToolTip('Open directory.')

    @QtCore.Slot()
    def open(self):
        """ Opens this folder in a file browser. """
        p = self.file_path
        if p and os.path.isdir(p):
            subprocess.Popen('explorer "{}"'.format(p.replace('/', '\\')))

    @QtCore.Slot()
    def browse(self):
        """ Opens a file browser to let the user pick a path. """
        path = os.path.split(self.le_path.text())[0]
        if not os.path.isdir(path):
            path = self.default

        result = QtWidgets.QFileDialog.getExistingDirectory(
            self.le_path, 'Pick a ' + self.label.text(),
            path, QtWidgets.QFileDialog.ShowDirsOnly)
        if result:
            self.file_path = result


class AnimFileWidget(QtWidgets.QWidget):
    """
    A custom widget interfacing a list of animation files.
    """

    _FILE_FILTER = 'Maya Files (*.ma *.mb *.fbx)'

    def __init__(self, *args, **kwargs):
        """
        Initialization.
        """
        super(AnimFileWidget, self).__init__(*args, **kwargs)
        self.__cache_icons()

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.setSpacing(3)
        vbox.setContentsMargins(6, 4, 6, 4)

        # hbox = QtWidgets.QHBoxLayout()
        # vbox.addLayout(hbox)
        # hbox.setSpacing(5)

        # self.btn_add = QtWidgets.QPushButton('')
        # self.btn_add.setFixedWidth(70)
        # self.btn_add.setIcon(QtGui.QIcon(':/p-add.png'))
        # hbox.addWidget(self.btn_add)
        # self.btn_add.setSizePolicy(
        #     QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.btn_add.clicked.connect(self.browse)

        # lb = QtWidgets.QLabel('Source Animations :')
        # hbox.addWidget(lb)
        # lb.setSizePolicy(
        #     QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.tw_files = QtWidgets.QTreeWidget()
        self.tw_files.setHeaderLabels(('Source Animation', 'Status'))
        self.tw_files.setRootIsDecorated(False)
        header = self.tw_files.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        vbox.addWidget(self.tw_files)
        self.tw_files.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tw_files.setStyleSheet('font: 13px;')

        # hbox.addStretch(10)

        self.tw_files.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tw_files.customContextMenuRequested.connect(self.pop_context_menu)

    def __cache_icons(self):
        self.__icon_anim = QtGui.QIcon(':/out_timeEditorAnimSource.png')
        self.__icon_none = QtGui.QIcon(':/precompExportUnchecked.png')
        self.__icon_running = QtGui.QIcon(':/waitBusy.png')
        self.__icon_success = QtGui.QIcon(':/precompExportChecked.png')
        self.__icon_fail = QtGui.QIcon(':/error.png')

    def set_line_edits(
            self, le_out_path, le_from_string, le_to_string):
        self.__le_out_path = le_out_path
        self.__le_from_string = le_from_string
        self.__le_to_string = le_to_string

    @QtCore.Slot()
    def pop_context_menu(self):
        """Creates the right click context menu."""
        menu = QtWidgets.QMenu(self)
        count = self.tw_files.topLevelItemCount()
        sel_count = len(self.tw_files.selectedItems())

        action = menu.addAction('Add Source Files')
        action.setIcon(QtGui.QIcon(':/p-add.png'))
        action.triggered.connect(self.browse)

        if sel_count == 1:
            action = menu.addAction('Open Source')
            action.setIcon(self.__icon_anim)
            action.triggered.connect(self.open_source_anim)
            action = menu.addAction('Open Output')
            action.setIcon(self.__icon_anim)
            action.triggered.connect(self.open_output_anim)
            action = menu.addAction('Compare')
            action.setIcon(QtGui.QIcon(':/animateSnapshot.png'))
            action.triggered.connect(self.compare_anims)

            menu.addSeparator()

            path = self.get_selected_file()
            if self.__get_config_file(path):
                action = menu.addAction('Open Animation Config')
                action.triggered.connect(partial(self.open_config, False))
                action.setIcon(QtGui.QIcon(':/SP_FileIcon.png'))
                action = menu.addAction('Delete Animation Config')
                action.triggered.connect(self.delete_config)
                action.setIcon(QtGui.QIcon(':/delete.png'))
            else:
                action = menu.addAction('Create Animation Config')
                action.triggered.connect(partial(self.open_config, True))
                action.setIcon(QtGui.QIcon(':/SP_FileIcon.png'))

        menu.addSeparator()

        if sel_count > 0:
            action = menu.addAction('Clear Selected Status')
            action.setIcon(QtGui.QIcon(':/clearHistory.png'))
            action.triggered.connect(self.clear_selected_status)

            action = menu.addAction('Remove Seleted Files')
            action.setIcon(QtGui.QIcon(':/delete.png'))
            action.triggered.connect(self.remove_selected)
        elif count > 0:
            action = menu.addAction('Clear All Status')
            action.setIcon(QtGui.QIcon(':/clearAll.png'))
            action.triggered.connect(self.clear_all_status)

            action = menu.addAction('Remove All Files')
            action.setIcon(QtGui.QIcon(':/delete.png'))
            action.triggered.connect(self.remove_all)

        menu.popup(QtGui.QCursor.pos())

    def refresh(self):
        for i in range(self.tw_files.topLevelItemCount()):
            item = self.tw_files.topLevelItem(i)
            file_path = item.text(0)
            config_file = self.__get_config_file(file_path)
            if config_file:
                item.setForeground(0, COLOR_HAS_CONFIG)
            else:
                item.setForeground(0, COLOR_NO_CONFIG)

    def enterEvent(self, event):
        """Refreshes this UI on cursor enter. This ensures the UI is
        in sync with any potential manual changes in the scene."""
        self.refresh()
        return super(AnimFileWidget, self).enterEvent(event)

    def get_files(self):
        """Returns a list of file pathes in the widget."""
        return [self.tw_files.topLevelItem(i).text(0)
                for i in range(self.tw_files.topLevelItemCount())]

    def get_selected_file(self):
        """Returns a list of selected file pathes in the widget."""
        sel = self.tw_files.selectedItems()
        if not sel:
            cmds.warning('No animation selected!')
        else:
            return sel[0].text(0)

    def __get_config_file(self, path, check_exists=True):
        h, f = os.path.split(path)
        f, _ = os.path.splitext(f)
        config_file = os.path.join(h, f + '.json').replace('/', '\\')
        if not check_exists or os.path.isfile(config_file):
            return config_file

    def __create_file_item(self, path):
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, path)
        item.setIcon(0, self.__icon_anim)
        return item

    def set_files(self, files):
        """ Sets the file pathes. """
        self.tw_files.clear()
        for f in [x.replace('\\', '/') for x in files]:
            if not os.path.isfile(f):
                cmds.warning('File not found: {}'.format(f))
                continue
            item = self.__create_file_item(f)
            self.tw_files.addTopLevelItem(item)
        self.clear_all_status()
        self.refresh()

    def add_files(self, files):
        """Adds a list of files."""
        cur_items = []
        cur_files = set()
        for _ in range(self.tw_files.topLevelItemCount()):
            cur_items.append(self.tw_files.takeTopLevelItem(0))
            cur_files.add(cur_items[-1].text(0))

        for f in files:
            if f not in cur_files:
                item = self.__create_file_item(f)
                cur_items.append(item)

        cur_items.sort(key=lambda x: x.text(0))
        self.tw_files.addTopLevelItems(cur_items)
        self.refresh()

    @QtCore.Slot()
    def browse(self):
        """ Opens a file browser to let the user pick file pathes. """
        path = DEFAULT_PATH
        if self.tw_files.topLevelItemCount():
            p = os.path.split(self.tw_files.topLevelItem(0).text(0))[0]
            if os.path.isdir(p):
                path = p

        result = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Source Animations', path, self._FILE_FILTER)[0]
        if result:
            self.add_files(result)

    @QtCore.Slot()
    def remove_selected(self):
        """Removes selected files."""
        ids = []
        for i in range(self.tw_files.topLevelItemCount()):
            if self.tw_files.topLevelItem(i).isSelected():
                ids.insert(0, i)

        if not ids:
            return

        msg = 'Do you really want to remove the selected animations?'
        btn = QtWidgets.QMessageBox.question(self, 'Warning', msg)
        if btn != QtWidgets.QMessageBox.No:
            for i in ids:
                self.tw_files.takeTopLevelItem(i)

    @QtCore.Slot()
    def remove_all(self):
        """Removes all files."""
        if self.tw_files.topLevelItemCount() == 0:
            return
        msg = 'Do you really want to remove all source animations?'
        btn = QtWidgets.QMessageBox.question(self, 'Warning', msg)
        if btn != QtWidgets.QMessageBox.No:
            self.tw_files.clear()

    def __get_item(self, id_or_path):
        """ Returns a QTreeWidgetItem based on an index or file path. """
        if isinstance(id_or_path, int):
            return self.tw_files.topLevelItem(id_or_path)
        else:
            path = id_or_path.lower().split('art')[-1].replace('\\', '/')
            for i in range(self.tw_files.topLevelItemCount()):
                item = self.tw_files.topLevelItem(i)
                if item.text(0).replace('\\', '/').lower().endswith(path):
                    return item

    @QtCore.Slot()
    def set_status(self, id_or_path, status):
        """Sets the transferred status of a file."""
        item = self.__get_item(id_or_path)
        if not item:
            print('Path not found: {}'.format(id_or_path))
            return

        if status == thd.ExecStatus.kRunning:
            item.setIcon(1, self.__icon_running)
        elif status == thd.ExecStatus.kSuccess:
            item.setIcon(1, self.__icon_success)
        elif status == thd.ExecStatus.kFail:
            item.setIcon(1, self.__icon_fail)
        else:
            item.setIcon(1, self.__icon_none)

        item.setData(0, QtCore.Qt.UserRole, status)
        QtCore.QCoreApplication.processEvents()

    def get_status(self, i):
        """Returns the transferred status of a file."""
        return self.tw_files.topLevelItem(i).data(0, QtCore.Qt.UserRole)

    def get_output(self, i):
        """Returns the output file path (the retargeted file)
        associated with a file."""
        src_path = self.tw_files.topLevelItem(i).text(0)
        _, src_file = os.path.split(src_path)
        src_file = os.path.splitext(src_file)[0]
        from_string = self.__le_from_string.text()
        to_string = self.__le_to_string.text()
        if from_string:
            src_file = src_file.replace(from_string, to_string)
        out_path = self.__le_out_path.text()
        out_path = os.path.join(out_path, src_file + '.ma')
        if os.path.isfile(out_path):
            return out_path

    @QtCore.Slot()
    def clear_selected_status(self):
        """Clears the transferred status of the selected files."""
        for i in range(self.tw_files.topLevelItemCount()):
            if self.tw_files.topLevelItem(i).isSelected():
                self.set_status(i, None)

    @QtCore.Slot()
    def clear_all_status(self):
        """ Clears the transferred status of all the files. """
        for i in range(self.tw_files.topLevelItemCount()):
            self.set_status(i, None)

    @QtCore.Slot()
    def open_source_anim(self):
        """Opens the source animation in Maya."""
        f = self.get_selected_file()
        if not f:
            return
        if not os.path.isfile(f):
            cmds.warning('Source animation not found: ' + f)
            return

        if dlg.prompt_scene_modified_dialog(self):
            try:
                cmds.file(f, open=True, f=True)
            finally:
                return True
        return False

    @QtCore.Slot()
    def open_output_anim(self):
        """Opens the output/transferred animation in Maya."""
        sel = self.tw_files.selectedItems()
        if not sel:
            return

        row = self.tw_files.indexOfTopLevelItem(sel[0])
        f = self.get_output(row)
        if not f:
            cmds.warning('Output animation not found!')
            return
        if dlg.prompt_scene_modified_dialog(self):
            try:
                cmds.file(f, open=True, f=True)
                return True
            except BaseException:
                pass
        return False

    @QtCore.Slot()
    def open_config(self, touch=False):
        """Opens an animation config file in the default editor."""
        f = self.get_selected_file()
        if not f:
            return
        if not os.path.isfile(f):
            cmds.warning('Source animation not found: ' + f)
            return
        config_file = self.__get_config_file(f, check_exists=False)
        if touch and not os.path.isfile(config_file):
            with open(config_file, 'w+') as f:
                f.writelines(['{\n}'])
            self.refresh()
        if os.path.isfile(config_file):
            os.startfile(config_file)

    @QtCore.Slot()
    def delete_config(self):
        """Deletes an animation config file in the default editor."""
        f = self.get_selected_file()
        if not f:
            return
        if not os.path.isfile(f):
            cmds.warning('Source animation not found: ' + f)
            return
        config_file = self.__get_config_file(f, check_exists=True)
        if config_file:
            try:
                os.remove(config_file)
                self.refresh()
                util.log_info('Deleted anim config: {}'.format(config_file))
            except OSError as e:
                util.log_warn(
                    'Failed deleting anim config: {}'.format(config_file))
                util.log_error(str(e.strerror))

    @QtCore.Slot()
    def compare_anims(self):
        """Compares the source animation and the
        output/retargeted animation in Maya."""
        if not self.open_source_anim():
            return
        sel = self.tw_files.selectedItems()
        if not sel:
            return

        row = self.tw_files.indexOfTopLevelItem(sel[0])
        f = self.get_output(row)
        if not f:
            cmds.warning('Output animation not found: {}'.format(f))
            return

        sutil.safe_open(
            f, reference=True, ignoreVersion=True,
            groupLocator=True, mergeNamespacesOnClash=False,
            namespace='OUTPUT', options='v=0;')
