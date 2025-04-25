import os
import json
from collections import OrderedDict

from maya import cmds, OpenMaya

from mhy.qt.core import QtWidgets, QtCore, QtGui
from mhy.qt.core.base_main_window import get_window_class

import mhy.maya.anim.retarget.bind_pose as bp
import mhy.maya.animtools.retargeter.widgets as wd
import mhy.maya.animtools.retargeter.thread as thd


# get the base main window class
base_class = get_window_class(app_name='MHY Animation Retargeter')


class AnimRetargeterWindow(base_class):
    """
    The main animation retargeter UI
    """

    _REUSE_SINGLETON = False

    def __init__(self):
        """ Creates and initializes this window. """
        self.__thread = None
        self.__save_path = None
        super(AnimRetargeterWindow, self).__init__()
        self.connect_signals()

    def create_menu_bar(self):
        """ Creates the menu bar. """
        bar = self.menuBar()
        menu = bar.addMenu('Project')
        action = menu.addAction('Save Project', self.save_project)
        action.setIcon(QtGui.QIcon(':/save.png'))
        action = menu.addAction('Load Project', self.load_project)
        action.setIcon(QtGui.QIcon(':/loadPreset.png'))

        menu = bar.addMenu('Cache')
        action = menu.addAction('Clear Bind Pose Cache', self.clear_cache)
        action.setIcon(QtGui.QIcon(':/delete.png'))

    def setup_ui(self):
        """Creates UI elements."""
        self.create_menu_bar()

        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.setCentralWidget(main_splitter)

        w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        w.setLayout(vbox)
        main_splitter.addWidget(w)
        vbox.setSpacing(3)
        vbox.setContentsMargins(5, 5, 5, 5)

        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        pix = QtGui.QPixmap(':/HIKCharacterToolFullBody.png')
        self.pg_src_rig = wd.MayaFileWidgetGroup(
            pix, 'Source Rig', grid, 0, placeholder='Source rig file path.')
        pix = QtGui.QPixmap(':/HIKCharacterToolStancePose.png')
        self.pg_tgt_rig = wd.MayaFileWidgetGroup(
            pix, 'Target Rig', grid, 1, placeholder='Target rig file path.')
        pix = QtGui.QPixmap(':/browseFolder.png')
        self.pg_output = wd.FolderWidegtGroup(
            pix, 'Out Folder', grid, 2, placeholder='Output folder.')
        pix = QtGui.QPixmap(':/SP_FileIcon.png')
        self.pg_config = wd.ConfigFileWidgetGroup(
            pix, 'Config File', grid, 3,
            placeholder='Retarget config file path.')

        # name swapping
        hbox = QtWidgets.QHBoxLayout()
        grid.addLayout(hbox, 4, 2, 1, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)

        label = QtWidgets.QLabel()
        label.setPixmap(QtGui.QPixmap(':/shotSwapRight.png'))
        grid.addWidget(label, 4, 0, 1, 1)
        label = QtWidgets.QLabel('Swap Text: ')
        grid.addWidget(label, 4, 1, 1, 1)
        grid.setAlignment(label, QtCore.Qt.AlignRight)
        self.le_from_string = QtWidgets.QLineEdit()
        self.le_from_string.setPlaceholderText('Replace text in file name')
        hbox.addWidget(self.le_from_string)
        label = QtWidgets.QLabel()
        label.setPixmap(QtGui.QPixmap(':/UVTkArrowRight.png'))
        hbox.addWidget(label)
        self.le_to_string = QtWidgets.QLineEdit()
        hbox.addWidget(self.le_to_string)

        # anim files
        self.pg_src_anim = wd.AnimFileWidget()
        vbox.addWidget(self.pg_src_anim)
        self.pg_src_anim.set_line_edits(
            self.pg_output.le_path, self.le_from_string, self.le_to_string)

        self.btn_retarget = QtWidgets.QPushButton('Run')
        self.btn_retarget.setIcon(QtGui.QIcon(':/execute.png'))
        self.btn_retarget.setFixedHeight(40)
        self.btn_retarget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        vbox.addWidget(self.btn_retarget)

        # progress bar
        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        self.prog_bar = QtWidgets.QProgressBar()
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setAlignment(QtCore.Qt.AlignLeft)
        self.prog_bar.setFixedHeight(15)
        self.prog_bar.setFormat('')
        grid.addWidget(self.prog_bar, 0, 0, 1, 1)

        # a label used to display text over the progress bar
        # this is better than progressBar.setFormat() as it works in busy mode
        self.lb_prog_frame = QtWidgets.QLabel()
        self.lb_prog_frame.setAlignment(QtCore.Qt.AlignLeft)
        self.lb_prog_frame.setStyleSheet(
            'QLabel { background: transparent; margin-left: 10px;}')
        grid.addWidget(self.lb_prog_frame, 0, 0, 1, 1)

        self.lb_prog = QtWidgets.QLabel()
        self.lb_prog.setAlignment(QtCore.Qt.AlignRight)
        self.lb_prog.setStyleSheet(
            'QLabel { background: transparent; margin-right: 10px;}')
        grid.addWidget(self.lb_prog, 0, 0, 1, 1)

        self.resize(700, 800)
        main_splitter.setSizes([550, 250])

    def connect_signals(self):
        """ Connects signals to slots. """
        self.btn_retarget.clicked.connect(self.start_thread)

    def closeEvent(self, event):
        """Stop the current thread before closing."""
        self.stop_thread()
        return super(AnimRetargeterWindow, self).closeEvent(event)

    @QtCore.Slot(int)
    def clear_cache(self):
        bp.clear_cache()

    def set_progress(self, prog, frame=None):
        """Sets the progress bar."""
        m = self.prog_bar.maximum()
        if prog > m:
            self.prog_bar.setValue(0)
            self.btn_retarget.setEnabled(True)
            self.lb_prog_frame.setText('')
            self.lb_prog.setText('')
        else:
            self.prog_bar.setValue(prog)
            if frame:
                self.lb_prog_frame.setText(
                    'Processing frame {} ...'.format(frame))
            else:
                self.lb_prog_frame.setText('')
            self.lb_prog.setText('{} / {}'.format(prog, m))

    @QtCore.Slot(int)
    def increment_progress(self, frame):
        """++ progress bar value."""
        self.set_progress(self.prog_bar.value() + 1, frame=frame)

    @QtCore.Slot(int)
    def set_progress_count(self, count):
        """Sets the progress count."""
        if count == 0:
            self.prog_bar.setMaximum(1)
            self.set_progress(2)
        else:
            self.prog_bar.setMaximum(count)

    @QtCore.Slot()
    def set_progress_start(self):
        """Sets the progress count."""
        self.lb_prog_frame.setText('Preparing ...')
        self.lb_prog.setText('')

    def get_project_data(self, validate=True):
        """Serializes and returns the project data.

        Args:
            validate (bool): If True, validates all file pathes.

        Returns:
            dict: The project data.
        """
        data = {}

        src_rig = self.pg_src_rig.file_path
        if validate and src_rig and not os.path.isfile(src_rig):
            cmds.warning('Source rig not found...')
            return
        data['src_rig'] = src_rig

        tgt_rig = self.pg_tgt_rig.file_path
        if validate and not os.path.isfile(tgt_rig):
            cmds.warning('Target rig not found...')
            return
        data['tgt_rig'] = tgt_rig

        src_files = self.pg_src_anim.get_files()
        if validate and not src_files:
            cmds.warning('No source animation listed...')
            return
        data['src_files'] = OrderedDict()
        for i, each in enumerate(src_files):
            data['src_files'][each] = self.pg_src_anim.get_status(i)

        config_file = self.pg_config.file_path
        if validate and config_file and \
           not os.path.isfile(config_file):
            cmds.warning('Invalid mapping file...')
            return
        data['config_file'] = config_file

        output_path = self.pg_output.file_path
        if validate and not os.path.isdir(output_path):
            cmds.warning('Output path not found...')
            return
        data['output_path'] = output_path

        data['from_string'] = self.le_from_string.text()
        data['to_string'] = self.le_to_string.text()

        if validate and not config_file:
            cmds.warning('No retarget config file provided...')
            return

        return data

    @QtCore.Slot()
    def save_project(self):
        """Saves this retarget project on disk."""
        path = self.__save_path if self.__save_path else wd.DEFAULT_PATH
        result = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save Retarget Project',
            path, 'Anim Retarget Project (*.json)')[0]

        if result:
            data = self.get_project_data(validate=False)
            path = os.path.split(result)[0]
            self.__save_path = path
            if not os.path.exists(path):
                os.makedirs(path)
            with open(result, 'w+') as f:
                json.dump(data, f, indent=2)

            OpenMaya.MGlobal.displayInfo('Saved retarget project to: ' + result)

    @QtCore.Slot()
    def load_project(self, data=None):
        """Loads a retarget project.

        Args:
            data (dict): The project data. If None, opens a file browser and let the user
                pick the project file.
        """
        path = self.__save_path if self.__save_path else wd.DEFAULT_PATH
        result = None
        if not data:
            path = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Load Retarget Project',
                path, 'Anim Retarget Project (*.json)')[0]

            if path:
                if not data:
                    data = {}
                    with open(path, 'r') as f:
                        data = json.load(f)
                    if not data:
                        cmds.warning(
                            'Failed loading retarget project: ' + result)
                        return
            else:
                return

        if not data or 'src_rig' not in data or 'tgt_rig' not in data:
            cmds.warning('Invalid retarget project file: {}'.format(path))
            return

        self.pg_src_rig.file_path = data.get('src_rig', data.get('oldRig', ''))
        self.pg_tgt_rig.file_path = data.get('tgt_rig', data.get('newRig', ''))
        self.pg_output.file_path = data.get('output_path', '')
        self.pg_config.file_path = data.get('config_file', '')
        src_files = data.get('src_files', [])
        if isinstance(src_files, dict):
            src_files = sorted(src_files.keys())
        self.pg_src_anim.set_files(src_files)

        self.le_from_string.setText(data.get('from_string', ''))
        self.le_to_string.setText(data.get('to_string', ''))

        if result:
            OpenMaya.MGlobal.displayInfo(
                'Loaded retarget project from: ' + result)

    @QtCore.Slot()
    def start_thread(self):
        """Main func to execute a batch retarget."""
        if self.thread_running():
            self.writeMessage(
                'An retargeting is in progress... Please try again later.', 'w')
            return

        kwargs = self.get_project_data(validate=True)
        if not kwargs:
            return

        # Bypass already finished retargets
        src_files = []
        for src_file, status in kwargs['src_files'].items():
            if not status:
                src_files.append(src_file)
        if not src_files:
            cmds.warning('All animations are already retargeted!')
            return
        kwargs['src_files'] = src_files

        thread = thd.RetargetThread(parent=self, **kwargs)
        thread.progress_started.connect(self.set_progress_start)
        thread.frame_count_changed.connect(self.set_progress_count)
        thread.current_frame_changed.connect(self.increment_progress)
        thread.status_changed.connect(self.pg_src_anim.set_status)

        self.set_progress_count(len(kwargs['src_files']))
        self.set_progress(0)

        self.__thread = thread
        self.__thread.run()

    def thread_running(self):
        """ Checks if a transfer thread is running at the moment. """
        if self.__thread is not None and self.__thread.isRunning():
            return True
        return False

    @QtCore.Slot()
    def stop_thread(self):
        """Stops the current retarget thread."""
        if self.__thread is not None and self.__thread.isRunning():
            self.__thread.terminate()
        self.set_progress(0)
