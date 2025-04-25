from mhy.qt.core import QtWidgets
import mhy.maya.rigtools.deformer_decompose.ui.manager as manager
import mhy.maya.rigtools.deformer_decompose.ui.widget


class ImportToSelConfig(QtWidgets.QDialog):
    def __init__(self, node_type, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle("Import To Selected Configuration")
        self.setMinimumWidth(350)
        self.node_type = node_type

        self.config_widget = mhy.maya.rigtools.deformer_decompose.ui.widget.SkinTransferConfig(self)

        button_layout = QtWidgets.QHBoxLayout()
        reset_button = QtWidgets.QPushButton("&Reset")
        save_button = QtWidgets.QPushButton("&Save")
        cancel_button = QtWidgets.QPushButton("&Cancel")
        button_layout.addWidget(reset_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        reset_button.clicked.connect(self.reset_config)
        save_button.clicked.connect(self.save_cb)
        cancel_button.clicked.connect(self.close)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        main_layout.addWidget(self.config_widget)
        main_layout.addWidget(line)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.read_config()

    def reset_config(self):
        default_config = manager.Default_Config
        manager.Current_Config['transfer'] = default_config['transfer']
        self.read_config()

    def read_config(self):
        current_config = manager.Current_Config
        self.config_widget.read_config(current_config['transfer'])

    def save_config(self):
        config = self.config_widget.get_config()
        manager.Current_Config['transfer'] = config
        manager.write_config(manager.Current_Config)

    def save_cb(self):
        self.save_config()
        self.close()
