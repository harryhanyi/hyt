import importlib
import weight_tools
importlib.reload(weight_tools)
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds

class HYTWeightToolsWindow(QtWidgets.QDialog):
    def __init__(self):
        super(HYTWeightToolsWindow, self).__init__()

        self.setWindowTitle("HYT_WeightTools")
        self.setMinimumSize(250, 100)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.create_ui()

    def create_ui(self):
        """Create UI layout and buttons."""
        layout = QtWidgets.QVBoxLayout(self)

        self.local_assign_btn = QtWidgets.QPushButton("Local assign")
        self.local_assign_btn.clicked.connect(self.local_assigning)
        
        self.partial_copy_btn = QtWidgets.QPushButton("Partial copy")
        self.partial_copy_btn.clicked.connect(self.partial_copying)

        self.transfer_skin_btn = QtWidgets.QPushButton("Transfer skin")
        self.transfer_skin_btn.clicked.connect(self.transfer_skin)

        layout.addWidget(self.local_assign_btn)
        layout.addWidget(self.partial_copy_btn)
        layout.addWidget(self.transfer_skin_btn)

    def local_assigning(self):
        wt = weight_tools.WeightTools()
        wt.local_assign()

    def partial_copying(self):
        wt = weight_tools.WeightTools()
        wt.partial_copy()

    def transfer_skin(self):
        wt = weight_tools.WeightTools()
        wt.transfer_skin()