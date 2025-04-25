"""
The ui to build rig from preset skeletons
"""
import os
import json
import sys
from os.path import expanduser
from PySide2 import QtWidgets


import maya.cmds as cmds


class RigBuilderSettingView(QtWidgets.QDialog):
    '''
    a simple panel to choose the path and project to build rig
    '''
    def __init__(self):
        super(RigBuilderSettingView, self).__init__()

        self.output_path = expanduser("~")

        self.create_widgets()
        self.create_layouts()
        # read default setting from saved config file and display on UI
        self.init_build_paths()

    def init_build_paths(self):
        '''
        read default paths from json file.
        it can be stored as user preference so that user can pick one default setting when they load the setting
        '''

        resource_path = os.environ.get('MHY_RIG_RESOURCE_PATH')
        resource_path = resource_path.split(';')[0]
        paths = {}
        try:
            with open(resource_path+'/rig_build_default_path.json', 'r') as paths_file:
                paths = json.load(paths_file)
        except IOError:
            print("can't read from rig_build_default_path.json under " + resource_path
                  + ", please check the folder to see if file exists")
        # Check if PROJECT_ROOT_PATH exists, if not, use maya default path instead
        if not os.path.exists(paths["PROJECT_ROOT_PATH"]):
            paths["PROJECT_ROOT_PATH"] = cmds.workspace( q=True, dir=True )
            print("project root path in default setting is not found, use maya default instead")

        # Set Local Path and Project Variables:
        self.set_env_line_text(
            paths["CHAR"],
            paths["PROJECT"],
            paths["TYPE"],
            paths["PROJECT_ROOT_PATH"]
        )

    def create_txt_param_line(self, param_name, line_width=60):
        '''
        create a text line for param
        '''
        lower_param_name = str.lower(param_name)
        # label to show what the param for
        setattr(self, lower_param_name + "_label", QtWidgets.QLabel(param_name))
        # text field to enter param value
        setattr(self, lower_param_name + "_line_edit", QtWidgets.QLineEdit())
        getattr(self, lower_param_name + "_line_edit").setFixedWidth(line_width)
        getattr(self, lower_param_name + "_line_edit").setText("default")

    def create_combox_param_line(self, param_name, line_width, types_info, activate_callback):
        '''
        create a dropdown menu
        '''
        lower_param_name = str.lower(param_name)
        # label to show what the param for
        setattr(self, lower_param_name + "_label", QtWidgets.QLabel(param_name))
        # text field to enter param value
        setattr(self, lower_param_name + "_combox", QtWidgets.QComboBox())
        getattr(self, lower_param_name + "_combox").setFixedWidth(line_width)
        getattr(self, lower_param_name + "_combox").addItems(types_info)
        # if activate_callback is not None:
        #     getattr(self, lower_param_name + "_combox").activated[str].connect(activate_callback)

    def select_path(self, line_edit):
        '''
        create a pop-up to select the path
        '''
        previous_path = line_edit.text()
        file_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            expanduser(previous_path),
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if(file_path == ""):
            file_path = previous_path
        print("set path to "+file_path)
        line_edit.setText(file_path)

    def create_path_param_line(self, param_name):
        '''
        create a line for path
        '''
        # label to show what the param for
        lower_param_name = str.lower(param_name)
        setattr(self, lower_param_name + "_label", QtWidgets.QLabel(param_name))
        # show what path it currently refers to
        setattr(self, lower_param_name + "_line_edit", QtWidgets.QLineEdit())
        getattr(self, lower_param_name + "_line_edit").setText(expanduser("~"))
        getattr(self, lower_param_name + "_line_edit").setReadOnly(True)
        # browse button to select desired path and display it in line_edit
        setattr(self, lower_param_name + "_button", QtWidgets.QPushButton('Browse'))
        getattr(self, lower_param_name + "_button").clicked.connect(\
            lambda: self.select_path(getattr(self, lower_param_name + "_line_edit")))

    def create_widgets(self):
        """
        create all widgets required in this panel
        """
        self.create_txt_param_line('PROJECT', 100)
        self.create_combox_param_line('CHAR', 120, ['XXX', 'SplineSpine', 'NeckHead', 'FKSpine', 'Face'], None)
        self.create_combox_param_line('TYPE', 120, ["bodyRig", "faceRig"], None)
        self.create_path_param_line('PROJECT_ROOT_PATH')

        self.build_button = QtWidgets.QPushButton('Build')
        self.build_button.clicked.connect(self.build_rig_from_ui_setting)

        self.save_button = QtWidgets.QPushButton('Save As Default')
        self.save_button.clicked.connect(self.save_default_setting)

    def create_layouts(self):
        """
        arrange all widgets in right place
        """
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setColumnMinimumWidth(0, 150)
        main_layout.setColumnMinimumWidth(1, 60)
        main_layout.setColumnMinimumWidth(2, 60)
        main_layout.setColumnMinimumWidth(3, 120)
        main_layout.setColumnMinimumWidth(4, 60)
        main_layout.setColumnMinimumWidth(5, 60)

        main_layout.addWidget(self.project_root_path_label, 0, 0)
        main_layout.addWidget(self.project_root_path_line_edit, 0, 1, 1, 3)
        main_layout.addWidget(self.project_root_path_button)

        main_layout.addWidget(self.project_label, 1, 0)
        main_layout.addWidget(self.project_line_edit, 1, 1)

        main_layout.addWidget(self.char_label, 2, 0)
        main_layout.addWidget(self.char_combox, 2, 1)

        main_layout.addWidget(self.type_label, 3, 0)
        main_layout.addWidget(self.type_combox, 3, 1)

        main_layout.addWidget(self.build_button, 4, 0, 1, 5)
        main_layout.addWidget(self.save_button, 5, 0, 1, 5)

    # utility function to add path
    @staticmethod
    def add_path_to_sys(pathlist=None):
        '''
        set all paths in list to sys, so that we can load libs from that
        '''
        if pathlist is not None:
            paths = [p for p in pathlist if p not in sys.path]
            # print paths
            for path in paths:
                sys.path.append(path)
                # print("#    Add to system path: "+path)

    def set_env_line_text(self, char_env, project_env, type_env, project_root_path_env):
        self.char_combox.setCurrentText(char_env)
        self.project_line_edit.setText(project_env)
        self.type_combox.setCurrentText(type_env)
        self.project_root_path_line_edit.setText(project_root_path_env)

    @staticmethod
    def add_sys_pathes(code_path):
        pathlist = [
            code_path,
            "{}/build".format(code_path),
            "{}/lib".format(code_path),
            "{}/core".format(code_path),
            "{}/core/limb".format(code_path),
            "{}/core/limb/limbLib".format(code_path)]
        RigBuilderSettingView.add_path_to_sys(pathlist)

    def build_rig_from_ui_setting(self):
        '''
        first grab settings from ui,
        then run the build command
        '''
        RigBuilderSettingView.add_sys_pathes(os.environ.get('MODULE_PATH')+"/scripts/mhy")
        RigBuilderSettingView.build_command(
            self.char_combox.currentText(),
            self.project_line_edit.text(),
            self.type_combox.currentText(),
            self.project_root_path_line_edit.text())

    @staticmethod
    def build_command(char_type, project_name, rig_type, work_area_root):
        '''
        select the right class from name string to build the rig
        '''
        # import mhy.core.limb.LimbBase as limbBase
        import importlib

        resource_path = os.environ.get('MHY_RIG_RESOURCE_PATH')

        # import specific build script
        char_to_scripts = {}
        try:
            with open(resource_path+'/char_to_scripts.json', 'r') as char_to_scripts_file:
                char_to_scripts = json.load(char_to_scripts_file)
        except IOError:
            print("can't read from char_to_scripts.json under " + resource_path
                  + ", please check the folder to see if file exists")
        builder = importlib.import_module(char_to_scripts[char_type]+"_build")
        #reload(limbBase)
        #reload(builder)

        # import class structor from build script
        char_to_class = {}
        try:
            with open(resource_path+'/char_to_class.json', 'r') as char_to_class_file:
                char_to_class = json.load(char_to_class_file)
        except IOError:
            print("can't read from char_to_class.json under " + resource_path
                  + ", please check the folder to see if file exists")
        rig_class = getattr(builder, char_to_class[char_type]+"Rig")
        target = rig_class(char=char_type, project=project_name, rigType=rig_type, workAreaRoot=work_area_root)
        target.create()

    def save_default_setting(self):
        '''
        save the current setting from UI to json file
        '''
        resource_path = os.environ.get('MHY_RIG_RESOURCE_PATH')

        pathlist = {
            'PROJECT'             : self.project_line_edit.text(),
            'CHAR'                : self.char_combox.currentText(),
            'TYPE'                : self.type_combox.currentText(),
            'PROJECT_ROOT_PATH'   : self.project_root_path_line_edit.text()
        }
        try:
            with open(resource_path+'/rig_build_default_path.json', 'w') as paths_file:
                json.dump(pathlist, paths_file, indent=4)
        except IOError:
            print("can't read from rig_build_default_path.json under " + resource_path
                  + ", please check the folder to see if file exists")


def run():
    ui = RigBuilderSettingView()
    ui.show()

