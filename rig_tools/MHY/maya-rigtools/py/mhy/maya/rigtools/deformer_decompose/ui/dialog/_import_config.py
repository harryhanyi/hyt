from mhy.qt.core import QtWidgets, QtCore
import mhy.maya.rigtools.deformer_decompose.ui.manager as manager


class ImportConfig(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle("Import Configuration")
        self.setMinimumWidth(350)

        grid_layout = QtWidgets.QGridLayout()
        self.weightsOnlyCheckBox = QtWidgets.QCheckBox("Weights Only")
        self.weightsOnlyCheckBox.setToolTip("If only export weights information. \nThis will "
                                            "disable exporting connection and creation data.\n"
                                            "Exported data can't be used to create node or build "
                                            "connections")
        self.connectionCheckBox = QtWidgets.QCheckBox("Make Connections")
        self.connectionCheckBox.setToolTip("If export node connection information. \n"
                                           "Connection data is required if need to make connection"
                                           "when import data")
        self.creationDataCheckBox = QtWidgets.QCheckBox("Creation Nodes")
        self.creationDataCheckBox.setToolTip("If export creation information\n"
                                             "Creation data is required if need to "
                                             "creation node when import data")

        self.weightsOnlyCheckBox.toggled.connect(self.only_weight_changed)
        grid_layout.addWidget(self.weightsOnlyCheckBox, 0, 0)
        grid_layout.addWidget(self.connectionCheckBox, 1, 0)
        grid_layout.addWidget(self.creationDataCheckBox, 1, 1)

        map_layout = QtWidgets.QGridLayout()
        namespace_map_from_label = QtWidgets.QLabel("Namespace Map: From", self)
        namespace_map_from_label.setToolTip("Map string in the namespace of "
                                            "each node while looking for objects in the scene.")
        namespace_map_from_label.setAlignment(QtCore.Qt.AlignRight)
        self.namespaceMapFromText = QtWidgets.QLineEdit(self)
        namespace_map_to_label = QtWidgets.QLabel("To", self)
        self.namespaceMapToText = QtWidgets.QLineEdit(self)

        name_map_from_label = QtWidgets.QLabel("Name Map: From", self)
        name_map_from_label.setToolTip("Map string in the name of "
                                       "each node while looking for objects in the scene.")
        name_map_from_label.setAlignment(QtCore.Qt.AlignRight)

        self.nameMapFromText = QtWidgets.QLineEdit(self)
        name_map_to_label = QtWidgets.QLabel("To", self)
        self.nameMapToText = QtWidgets.QLineEdit(self)

        map_layout.addWidget(namespace_map_from_label, 0, 0)
        map_layout.addWidget(self.namespaceMapFromText, 0, 1)
        map_layout.addWidget(namespace_map_to_label, 0, 2)
        map_layout.addWidget(self.namespaceMapToText, 0, 3)

        map_layout.addWidget(name_map_from_label, 1, 0)
        map_layout.addWidget(self.nameMapFromText, 1, 1)
        map_layout.addWidget(name_map_to_label, 1, 2)
        map_layout.addWidget(self.nameMapToText, 1, 3)

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
        main_layout.addLayout(map_layout)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.read_config()

    def reset_config(self):
        default_config = manager.Default_Config
        manager.Current_Config['import'] = default_config['export']
        self.read_config()

    def read_config(self):
        current_config = manager.Current_Config
        default_config = manager.Default_Config
        import_config = current_config.get('import',
                                           default_config.get('import'))
        weights_only = import_config.get('weightsOnly', True)
        self.weightsOnlyCheckBox.setChecked(weights_only)
        if weights_only:
            self.connectionCheckBox.setChecked(False)
            self.creationDataCheckBox.setChecked(False)
        else:
            self.connectionCheckBox.setChecked(import_config.get("connection", True))
            self.creationDataCheckBox.setChecked(import_config.get("creationData", True))

        name_map = import_config.get('nameMap')
        if name_map:
            self.nameMapFromText.setText(";".join(name_map.keys()))
            self.nameMapToText.setText(";".join(name_map.values()))
        else:
            self.nameMapFromText.clear()
            self.nameMapToText.clear()

        namespace_map = import_config.get('namespaceMap')
        if namespace_map:
            self.namespaceMapFromText.setText(namespace_map[0])
            self.namespaceMapToText.setText(namespace_map[1])
        else:
            self.namespaceMapFromText.clear()
            self.namespaceMapToText.clear()

    def save_config(self):
        name_map_from = self.nameMapFromText.text()
        name_map_to = self.nameMapToText.text()
        name_map = None
        if name_map_from and name_map_to:
            name_map_from_split = name_map_from.split(';')
            name_map_to_split = name_map_to.split(';')
            name_map = {key: value for key, value in zip(name_map_from_split, name_map_to_split)}

        namespace_map_from = self.namespaceMapFromText.text()
        namespace_map_to = self.namespaceMapToText.text()
        namespace_map = None
        if namespace_map_from or namespace_map_to:
            namespace_map = (namespace_map_from, namespace_map_to)

        import_config = {
            "weightsOnly": self.weightsOnlyCheckBox.isChecked(),
            "connection": self.connectionCheckBox.isChecked(),
            "creationData": self.creationDataCheckBox.isChecked(),
            "nameMap": name_map,
            "namespaceMap": namespace_map
        }
        manager.Current_Config['import'] = import_config
        manager.write_config(manager.Current_Config)

    def save_cb(self):
        self.save_config()
        self.close()

    def only_weight_changed(self, state):
        if state:
            self.creationDataCheckBox.setChecked(False)
            self.creationDataCheckBox.setDisabled(True)
            self.connectionCheckBox.setChecked(False)
            self.connectionCheckBox.setDisabled(True)
        else:
            self.creationDataCheckBox.setChecked(True)
            self.creationDataCheckBox.setEnabled(True)
            self.connectionCheckBox.setChecked(True)
            self.connectionCheckBox.setEnabled(True)
