from mhy.qt.core import QtWidgets, QtCore
import mhy.maya.rigtools.deformer_decompose.ui.widget as widget
import mhy.maya.rigtools.deformer_decompose.ui.config as config


class Window(QtWidgets.QDialog):
    NodeTypeChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle("Deformer Decompose Tool")
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        splitter = QtWidgets.QSplitter(self)

        # Widgets to list all objects in the scene
        object_type_sel_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Object Type: ")

        label.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                            QtWidgets.QSizePolicy.Maximum)
        self.nodeTypeCombo = QtWidgets.QComboBox(self)
        self.nodeTypeCombo.setStyleSheet("font-weight: bold; font-size: 32px")
        object_type_sel_layout.addWidget(label)
        object_type_sel_layout.addWidget(self.nodeTypeCombo)

        node_list_widget = widget.NodeWidget(self)

        items = [c.get('type') for c in config.NODECONFIG]
        self.nodeTypeCombo.addItems(items)

        # Edit widget
        edit_widget = QtWidgets.QWidget(self)
        edit_layout = QtWidgets.QVBoxLayout()
        edit_widget.setLayout(edit_layout)
        transfer_widget = widget.TransferWidget(self)
        transfer_widget.update_node_type(self.nodeTypeCombo.currentText())
        edit_layout.addWidget(transfer_widget)
        export_widget = widget.ExportImportWidget(self)
        edit_layout.addWidget(export_widget)
        edit_widget.setMinimumWidth(400)

        # Finish up splitter
        splitter.addWidget(node_list_widget)
        splitter.addWidget(edit_widget)
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addLayout(object_type_sel_layout)
        main_layout.addWidget(splitter)

        current_node_type = self.nodeTypeCombo.currentText()
        node_list_widget.update_node_type(current_node_type)
        self.nodeTypeCombo.currentTextChanged.connect(self.currentNodeTypeChanged)
        self.NodeTypeChanged.connect(node_list_widget.update_node_type)
        self.NodeTypeChanged.connect(transfer_widget.update_node_type)

    def currentNodeTypeChanged(self, typeStr):
        self.NodeTypeChanged.emit(typeStr)


