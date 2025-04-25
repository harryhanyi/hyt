from mhy.qt.core import QtWidgets, QtCore
from mhy.qt.icon_lib.ui.model import IconTableModel


class IconTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(IconTableView, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.horizontalHeader().setDefaultSectionSize(42)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(42)
        self._items = []

    def __del__(self):
        del self._items[:]


class IconLayoutWidget(QtWidgets.QScrollArea):
    sel_changed_signal = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(IconLayoutWidget, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)

        self.view = IconTableView(self)
        self.model = IconTableModel(self)
        self.view.setModel(self.model)
        layout.addWidget(self.view)
        self.setWidget(widget)
        sel_model = self.view.selectionModel()
        sel_model.selectionChanged.connect(self.sel_changed_cb)

    def populate_items(self, icon_containers):
        self.model.populate_items(icon_containers)

    def sel_changed_cb(self, sel, desel):
        sel_mod = self.view.selectionModel()
        selected = sel_mod.selectedIndexes()
        for idx in selected:
            obj = idx.data(QtCore.Qt.UserRole)
            self.sel_changed_signal.emit(obj)
            break
