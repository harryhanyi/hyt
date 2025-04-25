"""
to import and export attributes of controls in the scene
"""
import os
from PySide2 import QtWidgets, QtCore
from PySide2 import QtGui
from mhy.maya.rig.node.ctrl_attrs_controller import CtrlAttrsController



class CtrlAttrsIoView(QtWidgets.QDialog):
    """
    the panel contains buttons for import/export control attributes
    """
    def __init__(self, parent=None):
        super(CtrlAttrsIoView, self).__init__(parent=parent)
        self.controller = CtrlAttrsController()
        self.setWindowTitle("Controller Attr I/O")
        self.setMinimumWidth(340)
        self.create_widgets()
        self.create_layouts()

    def create_widgets(self):
        """
        create all widgets required in this panel
        """
        cwd = os.path.dirname(os.path.realpath(__file__))
        go_up = os.path.join(*[os.pardir]*4)
        pwd = os.path.abspath(os.path.join(cwd, go_up))
        icons_path = pwd + "/resource/maya/icons/"

        self.import_button = QtWidgets.QPushButton('Import')
        self.import_button.setMinimumSize(100, 50)
        self.import_button.setIcon(QtGui.QIcon(icons_path + "import.png"))
        self.import_button.clicked.connect(self.import_attrs)

        self.export_button = QtWidgets.QPushButton('Export')
        self.export_button.setMinimumSize(100, 50)
        self.export_button.setIcon(QtGui.QIcon(icons_path + "export.png"))
        self.export_button.clicked.connect(self.export_attrs)

    def create_layouts(self):
        """
        arrange all widgets in right place
        """
        self.resize(200, 100)
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(self.import_button)
        main_layout.addWidget(self.export_button)

    def import_attrs(self):
        """
        read all control attributs from json file
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption='Import from', dir='.', filter='Json Files (*.json)')[0]
        if filename:
            print("all import attrs: ")
            imported_attr_dict = self.controller.get_all_import_attrs(filename)
            selected_ctrl_list = imported_attr_dict.keys()
            print(selected_ctrl_list)
            CtrlSelectedListView(selected_ctrl_list, self, False, imported_attr_dict, parent=self)

    def on_import_signal_ctrl_selected(self, ctrl_list, attr_dict):
        """
        after choosing controls we want to import, execute the actual import
        """
        print("selected import ctrls: ")
        print(ctrl_list)
        self.controller.import_attrs(ctrl_list, attr_dict)

    def export_attrs(self):
        """
        get all controls in the scene and pop-up list view for selection
        """
        # print("export attrs")
        print("all ctrls: ")
        selected_ctrl_list = self.controller.get_all_ctrls()
        print(selected_ctrl_list)
        CtrlSelectedListView(selected_ctrl_list, self, True, None, parent=self)

    def on_export_signal_ctrl_selected(self, ctrl_list):
        """
        after choosing ctrl we want to export, pop up the window to select file to write in
        """
        print("selected export ctrls: ")
        print(ctrl_list)
        filename = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption='Export to', dir='.', filter='Json Files (*.json)')[0]
        if filename:
            self.controller.export_attrs(ctrl_list, filename)


class CtrlSelectedListView(QtWidgets.QDialog):
    """
    a list to select controls in a list
    """
    signal_export_ctrl_selected = QtCore.Signal(list)
    signal_import_ctrl_selected = QtCore.Signal(list, dict)

    def __init__(self, selected_ctrl_list, main_dialog, is_export, attr_dict, *args, **kwargs):
        super(CtrlSelectedListView, self).__init__(*args, **kwargs)
        self.signal_export_ctrl_selected.connect(main_dialog.on_export_signal_ctrl_selected)
        self.signal_import_ctrl_selected.connect(main_dialog.on_import_signal_ctrl_selected)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemChanged.connect(self.item_changed)

        for ctrl_name in selected_ctrl_list:
            item = QtWidgets.QListWidgetItem(ctrl_name)
            item.setCheckState(QtCore.Qt.Checked)
            self.list_widget.addItem(item)

        run_btn = QtWidgets.QPushButton("Confirm")
        if is_export:
            run_btn.clicked.connect(self.confirm_ctrls)
        else:
            run_btn.clicked.connect(lambda: self.confirm_ctrls_with_dict(attr_dict))

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_ctrls)

        self.select_all_btn = QtWidgets.QCheckBox('Select All', self)
        self.select_all_btn.toggle()
        self.select_all_btn.stateChanged.connect(self.select_all_ctrls)

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.addWidget(self.list_widget, 1)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(run_btn)
        buttons_layout.addWidget(cancel_btn)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.select_all_btn)
        main_layout.addLayout(horizontal_layout)
        main_layout.addSpacing(12)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Selected Ctrl List")
        self.show()

    def get_all_selected_items(self):
        """
        get all checked item in self.list_widget
        """
        items_selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                items_selected.append(item.text())
        return items_selected

    def confirm_ctrls(self):
        """
        check the list widget and collect all selected items
        """

        items_selected = self.get_all_selected_items()
        self.close()
        # return items_selected
        self.signal_export_ctrl_selected.emit(items_selected)

    def confirm_ctrls_with_dict(self, attr_dict):
        """
        check the list widget and collect all selected items,
        because it's for import attrs, we need provide ctrl-value dictionary as well
        """

        items_selected = self.get_all_selected_items()
        self.close()
        # return items_selected
        self.signal_import_ctrl_selected.emit(items_selected, attr_dict)

    def cancel_ctrls(self):
        """
        do nothing and return to parent window
        """
        self.close()

    def select_all_ctrls(self, state):
        """
        perform select/unselect on all items
        """
        if state == QtCore.Qt.Checked:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item.setCheckState(QtCore.Qt.Checked)
        elif state == QtCore.Qt.Unchecked:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item.setCheckState(QtCore.Qt.Unchecked)

    def item_changed(self, item):
        """
        once we changed one item's select status, we need to update total selection status
        """
        # print("refresh " + item.text())

        check_cnt = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                check_cnt = check_cnt + 1

        if check_cnt == self.list_widget.count():
            self.select_all_btn.setCheckState(QtCore.Qt.Checked)
        elif check_cnt == 0:
            self.select_all_btn.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.select_all_btn.setCheckState(QtCore.Qt.PartiallyChecked)


UI = None


def run():
    global UI
    UI = CtrlAttrsIoView(parent=None)
    UI.show()
