from PySide2 import QtWidgets, QtGui, QtCore
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from mhy.maya.nodezoo.node import Node
import mhy.maya.rigtools.pose_editor.api.pose_controller as p_ctrl
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
from mhy.qt.core.utils import get_icon
from mhy.maya.standard.name import NodeName


class ControllerView(QtWidgets.QWidget):
    """
    The Widget Class to provide user basic function to switch, select, delete controller.
    """

    def __init__(self,  *args, **kwargs):
        super(ControllerView, self).__init__(*args, **kwargs)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(h_layout)
        self.controller_select_box = QtWidgets.QComboBox(parent=self)
        h_layout.addWidget(self.controller_select_box)

        icon = get_icon('add.png', QtGui.QColor(255, 255, 255))
        button = QtWidgets.QPushButton(icon, "", self)
        button.clicked.connect(self.add_controller_cb)
        button.setToolTip("Add a pose controller to this scene")
        button.setFixedSize(40, 40)
        h_layout.addWidget(button)

        icon = get_icon('refresh.png', QtGui.QColor(255, 255, 255))
        button = QtWidgets.QPushButton(icon, "", self)
        button.clicked.connect(self.refresh_controllers_deferred)
        button.setToolTip("Refresh the pose controller objects in the scene")
        button.setFixedSize(40, 40)
        h_layout.addWidget(button)

        icon = get_icon('arrowhead_right.png', QtGui.QColor(255, 255, 255))
        button = QtWidgets.QPushButton(icon, "", self)
        button.clicked.connect(self.select_pose_controller)
        button.setToolTip("Select the pose controller object in the scene")
        button.setFixedSize(40, 40)
        h_layout.addWidget(button)

        self.refresh_controllers()
        self.controller_select_box.currentTextChanged.connect(self._switch_controller)

    @property
    def current_controller(self):
        """
        Get current active controller's name
        Returns:
            str: controller name
        """
        return self.controller_select_box.currentText()

    def refresh_controllers_deferred(self):
        """
        The eval deferred version of refresh controllers to fight Maya insane UI update.
        """
        cmds.evalDeferred(self.refresh_controllers, low=True)

    def refresh_controllers(self, current_node=None):
        """
        refresh controllers of all widgets from Maya scene.
        """
        self.controller_select_box.blockSignals(True)
        p_ctrl.PoseController.clear_cached_controllers()
        rig_controller_nodes = p_ctrl.list_pose_controllers()
        current = self.current_controller
        self.controller_select_box.clear()
        if not rig_controller_nodes:
            self._switch_controller(self.current_controller)
            return
        for controller in rig_controller_nodes:
            self.controller_select_box.addItem(controller)
        if current not in rig_controller_nodes:
            self.controller_select_box.setCurrentText(rig_controller_nodes[0])
        else:
            self.controller_select_box.setCurrentText(current)
        self.controller_select_box.blockSignals(False)
        if current_node and current_node in rig_controller_nodes:
            self._switch_controller(current_node)
        else:
            self._switch_controller(self.current_controller)

    @staticmethod
    def _switch_controller(node_name):
        """
        Provide callback function to Widget, should never be called explicitly.
        """
        SignalManager.controller_selection_changed.emit(node_name)

    def select_pose_controller(self):
        """
        Provide the callback function for select pose controller button.
        Should never be called explicitly.
        """
        current_controller = self.current_controller
        if current_controller:
            if cmds.objExists(current_controller):
                cmds.select(current_controller)
            else:
                OpenMaya.MGlobal.displayWarning("{} does not exists in the scene".format(current_controller))

    def add_controller_cb(self):
        win = PoseControllerCreator(self)
        win.pose_controller_created.connect(self.refresh_controllers)
        win.show()


class PoseControllerCreator(QtWidgets.QDialog):
    pose_controller_created = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(PoseControllerCreator, self).__init__(parent=parent)
        self.setWindowTitle("Create Pose Controller")
        main_layout = QtWidgets.QGridLayout(self)
        label = QtWidgets.QLabel("Name:")
        self.name_text = QtWidgets.QLineEdit(self)
        main_layout.addWidget(label, 0, 0)
        main_layout.addWidget(self.name_text, 0, 1)

        mesh_pb = QtWidgets.QPushButton('Out Mesh>>', self)
        self.mesh_text = QtWidgets.QLineEdit(self)
        main_layout.addWidget(mesh_pb, 1, 0)
        main_layout.addWidget(self.mesh_text, 1, 1)
        apply_bt = QtWidgets.QPushButton('Apply')
        cancel_bt = QtWidgets.QPushButton('Cancel')
        main_layout.addWidget(apply_bt, 2, 0)
        main_layout.addWidget(cancel_bt, 2, 1)
        mesh_pb.clicked.connect(self.load_mesh)
        apply_bt.clicked.connect(self.accept)
        cancel_bt.clicked.connect(self.close)

    def accept(self, *args):
        name = self.name_text.text()
        if '_' not in name:
            name = name + '_POSENODE'
        try:
            NodeName(name)
        except ValueError as e:
            OpenMaya.MGlobal.displayError(str(e))
            return

        out_mesh = self.mesh_text.text()

        if not out_mesh or not Node.object_exist(out_mesh):
            OpenMaya.MGlobal.displayError("Invalid mesh object")
            return

        try:
            pc_node = p_ctrl.PoseController.create(name=name, out_mesh=out_mesh)
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return
        self.pose_controller_created.emit(str(pc_node.node_name))
        super(PoseControllerCreator, self).accept(*args)

    def load_mesh(self):
        sel = cmds.ls(sl=True)
        if len(sel) != 1:
            OpenMaya.MGlobal.displayError("Please select only one mesh object")
            return
        mesh = Node(sel[0])
        if mesh.type_name == 'transform':
            shapes = mesh.get_shapes()
            if len(shapes) != 1:
                OpenMaya.MGlobal.displayError("Please make sure selected object has only one shape node")
                return
            mesh = shapes[0]

        if mesh.type_name != 'mesh':
            OpenMaya.MGlobal.displayError("Please make sure mesh object is selected")
            return
        self.mesh_text.setText(mesh.name)











