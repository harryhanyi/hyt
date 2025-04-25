from mhy.qt.core import QtWidgets
import mhy.maya.rigtools.deformer_decompose.ui.manager as manager


class ExportConfig(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle("Export Configuration")
        self.setMinimumWidth(350)

        grid_layout = QtWidgets.QGridLayout()
        self.weightsOnlyCheckBox = QtWidgets.QCheckBox("Weights Only")
        self.weightsOnlyCheckBox.setToolTip("If only export weights information. \nThis will "
                                            "disable exporting connection and creation data.\n"
                                            "Exported data can't be used to create node or build "
                                            "connections")
        self.connectionCheckBox = QtWidgets.QCheckBox("Connections")
        self.connectionCheckBox.setToolTip("If export node connection information. \n"
                                           "Connection data is required if need to make connection"
                                           "when import data")

        self.weightsOnlyCheckBox.toggled.connect(self.only_weight_changed)
        self.multipleFileCheckBox = QtWidgets.QCheckBox('Multiple files', self)
        self.multipleFileCheckBox.setToolTip("If export each node as a separate file")

        self.compressFileCheckBox = QtWidgets.QCheckBox('Compress files', self)
        self.compressFileCheckBox.setToolTip("If compress file before writing to disk")

        grid_layout.addWidget(self.weightsOnlyCheckBox, 0, 0)
        grid_layout.addWidget(self.connectionCheckBox, 1, 0)
        grid_layout.addWidget(self.multipleFileCheckBox, 2, 0)
        grid_layout.addWidget(self.compressFileCheckBox, 2, 1)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

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

        main_layout.addLayout(grid_layout)
        main_layout.addWidget(line)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.read_config()

    def reset_config(self):
        default_config = manager.Default_Config
        manager.Current_Config['export'] = default_config['export']
        self.read_config()

    def read_config(self):
        current_config = manager.Current_Config
        default_config = manager.Default_Config
        export_config = current_config.get('export',
                                           default_config.get('export'))
        weights_only = export_config.get('weightsOnly', False)
        self.weightsOnlyCheckBox.setChecked(weights_only)
        if weights_only:
            self.connectionCheckBox.setChecked(False)
        else:
            self.connectionCheckBox.setChecked(export_config.get("connection", True))

        self.compressFileCheckBox.setChecked(export_config.get('compress', False))
        self.multipleFileCheckBox.setChecked(export_config.get('multipleFiles', False))

    def save_config(self):
        export_config = {"weightsOnly": self.weightsOnlyCheckBox.isChecked(),
                         "connection": self.connectionCheckBox.isChecked(),
                         "compress": self.compressFileCheckBox.isChecked(),
                         "multipleFiles": self.multipleFileCheckBox.isChecked()
                         }
        manager.Current_Config['export'] = export_config
        manager.write_config(manager.Current_Config)

    def save_cb(self):
        self.save_config()
        self.close()

    def only_weight_changed(self, state):
        if state:
            self.connectionCheckBox.setChecked(False)
            self.connectionCheckBox.setDisabled(True)
        else:
            self.connectionCheckBox.setChecked(True)
            self.connectionCheckBox.setEnabled(True)
