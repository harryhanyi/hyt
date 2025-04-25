"""

This dialog will prompt when user promote parameters of an action to its graph

"""

from mhy.qt.core.Qt import QtWidgets
import mhy.protostar.ui.manager as manager


class PromptDialog(QtWidgets.QDialog):
    def __init__(self, parameter, graph, parent=None):
        super(PromptDialog, self).__init__(parent=parent)
        self.setWindowTitle(
            "Promote {} to {}?".format(parameter.name, graph.name)
        )

        self.parameter = parameter
        self.graph = graph
        name_label = QtWidgets.QLabel("Name: ")
        self.name_line = QtWidgets.QLineEdit()
        self.name_line.setText(parameter.name)
        self.is_output = QtWidgets.QCheckBox("Output", self)

        is_output = self.parameter.is_output
        if is_output:
            self.is_output.setChecked(self.parameter.is_output)
            self.is_output.setEnabled(False)

        grid_layout = QtWidgets.QGridLayout()

        self.warning_line = QtWidgets.QLabel(self)
        self.warning_line.setStyleSheet("color: red")
        self.warning_line.hide()

        self.setMinimumWidth(450)
        self.setLayout(grid_layout)

        grid_layout.addWidget(name_label, 0, 0)
        grid_layout.addWidget(self.name_line, 0, 1)

        grid_layout.addWidget(self.is_output, 1, 0, 1, 2)
        grid_layout.addWidget(self.warning_line, 2, 0, 1, 2)

        accept_pb = QtWidgets.QPushButton("Apply", self)
        grid_layout.addWidget(accept_pb, 3, 0, 1, 2)
        accept_pb.clicked.connect(self.apply_cb)

    def apply_cb(self):
        """
        Called when apply button clicked. Check validation of arguments before
        promote the parameter to graph

        """
        owner = self.parameter.owner
        name = self.name_line.text()
        if not name:
            self.warning_line.show()
            self.warning_line.setText(
                'Please set a name for promoted parameter'
            )
            return

        if self.graph.has_param(name):
            self.warning_line.show()
            self.warning_line.setText(
                'Graph {} already has a '
                'parameter named {}.'.format(self.graph, name))
            return
        is_output = self.is_output.isChecked()

        # Emit signal so if owner is in any active node view,
        # refresh the owner node
        owner.promote(self.parameter, name=name, output=is_output)

        # Once a parameter has been prompt
        # 1. Refresh node scene for parent graph
        # 2. Refresh the state of promoted parameter

        manager.SignalManager.graph_updated_signal.emit(self.graph)

        # Reload the graph parameter panel
        manager.SignalManager.reload_graph_parameters_signal.emit(
            self.graph
        )

        manager.SignalManager.parameter_connection_changed_signal.emit(
            self.parameter
        )

        self.close()


