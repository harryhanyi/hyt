from mhy.qt.core import QtWidgets, QtCore
import mhy.maya.rigtools.deformer_decompose.ui.view as view
import mhy.maya.rigtools.deformer_decompose.ui.model as model
from mhy.maya.rigtools.deformer_decompose.ui.widget._regex_completer import RegexCompleter
import mhy.maya.rigtools.deformer_decompose.ui.manager as manager


class NodeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NodeWidget, self).__init__(parent=parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.node_filter = QtWidgets.QLineEdit(self)
        self.node_filter.setPlaceholderText('Type Your Object Search Here')
        self.node_filter.setClearButtonEnabled(True)
        self.view = view.NodeListView(self)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        manager.Node_List_View = self.view
        main_layout.addWidget(self.node_filter)
        main_layout.addWidget(self.view)

        self.proxyModel = model.NodesSortFilterProxyModel()
        self.sourceModel = model.NodeListModel()
        self.proxyModel.setSourceModel(self.sourceModel)
        self.view.setModel(self.proxyModel)

        completer = RegexCompleter(self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setModel(self.sourceModel)
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.node_filter.setCompleter(completer)
        self.node_filter.textChanged.connect(self._filter_update_list)

    def _filter_update_list(self):
        filter = self.node_filter.text()
        self.proxyModel.setFilterWildcard(filter)

    def update_node_type(self, nodeType='skinCluster'):
        self.view.updateNodeType(nodeType=nodeType)


