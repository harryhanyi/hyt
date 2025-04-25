"""
This widget display the parameters of selected action in the node view

"""
from mhy.qt.core.Qt import QtWidgets
from mhy.qt.core.widgets.collapsible_box import CollapsibleBox

import mhy.protostar.constants as const
import mhy.protostar.ui.widget.attribute_widgets as aw
from mhy.protostar.ui.view.node import Node
from mhy.protostar.ui.manager import SignalManager


__all__ = ['ParameterWidget', 'ParameterList', 'ParameterGroup']


class ParameterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        main_layout = QtWidgets.QGridLayout()
        self.__nodes = None

        name_label = QtWidgets.QLabel("Name:", self)
        self.action_name_line = QtWidgets.QLineEdit(self)

        self.type_label = QtWidgets.QLabel("Type:", self)

        self.param_list = ParameterList(
            exclude_parameters=[const.EXEC_PARAM_NAME, const.SELF_PARAM_NAME],
            parent=self)

        main_layout.addWidget(name_label, 0, 0)
        main_layout.addWidget(self.action_name_line, 0, 1)
        main_layout.addWidget(self.type_label, 1, 0, 1, 2)
        main_layout.addWidget(self.param_list, 2, 0, 1, 2)

        self.action_name_line.editingFinished.connect(self.rename_action_cb)

        self.setLayout(main_layout)

    def refresh_param_widgets(self, items):
        self.__nodes = [i for i in items if isinstance(i, Node)]
        actions = [node.instance for node in self.__nodes]
        node_types = [i.node_type for i in self.__nodes]
        node_types = list(set(node_types))

        self.action_name_line.blockSignals(True)
        num_sel = len(self.__nodes)

        if num_sel == 1:
            self.action_name_line.setText(self.__nodes[0].name)
            self.action_name_line.setEnabled(True)
        else:
            self.action_name_line.setText("{} items...".format(num_sel))
            self.action_name_line.setEnabled(False)

        if len(node_types) == 1:
            self.type_label.setText(
                'Type: {}'.format(node_types[0])
            )
        else:
            self.type_label.setText(
                'Type: '
            )

        self.set_actions(actions)
        self.action_name_line.blockSignals(False)

    def rename_action_cb(self):
        text = self.action_name_line.text()
        for node in self.__nodes:
            node.update_action_name(text)

    def set_actions(self, actions):
        self.param_list.set_actions(actions)


class GraphParameterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.__graph = None
        name_label = QtWidgets.QLabel("Name:", self)
        self.graph_name_line = QtWidgets.QLineEdit(self)

        box = QtWidgets.QGroupBox("Graph Parameters: ")
        grid_layout = QtWidgets.QGridLayout()
        box.setLayout(grid_layout)
        self.param_list = ParameterList(
            exclude_parameters=['execution'], draggable=True, parent=self)

        grid_layout.addWidget(name_label, 0, 0)
        grid_layout.addWidget(self.graph_name_line, 0, 1)
        grid_layout.addWidget(self.param_list, 1, 0, 1, 2)

        self.graph_name_line.editingFinished.connect(self.rename_graph_cb)

        main_layout.addWidget(box)
        SignalManager.reload_graph_parameters_signal.connect(self.update_graph)

    def update_graph(self, graph):
        self.__graph = graph
        self.graph_name_line.blockSignals(True)
        self.graph_name_line.setText(graph.name)
        self.set_actions([graph])
        self.graph_name_line.blockSignals(False)

    def set_actions(self, actions):
        self.param_list.set_actions(actions)

    def rename_graph_cb(self):
        """
        Called when user finishes editing graph name using
        line editor

        """
        text = self.graph_name_line.text()
        if text and self.__graph:
            self.__graph.name = text
            SignalManager.graph_updated_signal.emit(self.__graph)

        # Refresh the edit line with the current resolved graph name
        self.graph_name_line.blockSignals(True)
        self.graph_name_line.setText(self.__graph.name)
        self.graph_name_line.blockSignals(False)


class ParameterList(QtWidgets.QScrollArea):
    def __init__(self, exclude_parameters=None, draggable=False, parent=None):
        super(ParameterList, self).__init__(parent=parent)
        self.actions = []
        self.exclude_parameters = exclude_parameters
        self.draggable = draggable
        self.main_widget = QtWidgets.QWidget(self)

        self.param_layout = QtWidgets.QVBoxLayout()
        self.param_layout.setContentsMargins(0, 0, 0, 0)

        self.main_widget.setLayout(self.param_layout)
        self.setWidget(self.main_widget)
        self.setWidgetResizable(True)

    def set_actions(self, actions):
        row_count = self.param_layout.count()
        # Skip the last two items, first two are spacer item
        # and add dynamic parameter push button
        for row in reversed(range(row_count)):
            item = self.param_layout.itemAt(row)
            if item:
                widget = item.widget()
                if widget:
                    self.param_layout.removeWidget(widget)
                    widget.deleteLater()
                    del widget
                else:
                    spacer = item.spacerItem()
                    if spacer:
                        self.param_layout.removeItem(item)
                        del item

        if not actions or len(actions) > 1:
            return

        action_item = actions[0]
        params = action_item.get_params(sort=True)
        params.sort(key=lambda a: a.is_output)

        param_widget_map = {}
        group_names = []
        for param in params:
            if not param.ui_visible:
                continue
            if param.name in self.exclude_parameters:
                # Skip builtin message parameter
                continue

            group_name = param.group or 'Basic'
            if group_name not in group_names:
                group_names.append(group_name)
                param_widget_map[group_name] = []

            param_type = param.param_type
            widget_class = aw.parameter_type_widget_map.get(param_type)
            if not widget_class:
                widget_class = aw.NullAttributeEditor
            widget = widget_class(
                parameters=[param],
                attr_name=param.ui_label,
                draggable=self.draggable,
                parent=self
            )
            widget.init_parameters([param])
            param_widget_map[group_name].append(widget)

        for grp_name in group_names:
            parameter_bundle = param_widget_map.get(grp_name)
            if not grp_name.endswith(':'):
                grp_name = grp_name + ':'
            box = ParameterGroup(title=grp_name, parent=self)
            box.add_parameter_widgets(parameter_bundle)
            self.param_layout.addWidget(box)

        if group_names:
            self.add_dynamic_attrition_pb()

        spacer = QtWidgets.QSpacerItem(
            100,
            100,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        self.param_layout.addItem(spacer)

    def add_dynamic_attrition_pb(self):
        add_button_widget = QtWidgets.QWidget(self)
        add_button_layout = QtWidgets.QHBoxLayout()
        add_button_widget.setLayout(add_button_layout)
        add_button_layout.addStretch()
        add_dynamic_parameter_pb = QtWidgets.QPushButton('+', self)
        add_dynamic_parameter_pb.setToolTip("Add a dynamic parameter")
        add_dynamic_parameter_pb.setFixedSize(30, 30)
        add_button_layout.addWidget(add_dynamic_parameter_pb)
        add_button_layout.addStretch()
        self.param_layout.addWidget(add_button_widget)


class ParameterGroup(CollapsibleBox):
    """
    Override CollapsibleBox to add a method add a list
    of parameter widgets with a grid layout
    """
    def add_parameter_widgets(self, parameter_bundle):
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setSpacing(0)
        count = 0
        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 10)

        for i in parameter_bundle:
            grid_layout.addWidget(
                i.name_widget,
                count,
                0)
            grid_layout.addWidget(
                i.detailed_widget,
                count,
                1)
            count = count + 1
        self.set_content_layout(grid_layout)
