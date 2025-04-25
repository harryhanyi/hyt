from PySide2 import QtCore, QtGui, QtWidgets
from mhy.protostar.ui.manager import action_lib
from mhy.qt.core.layout.flow_layout import FlowLayout


class LibraryWidget(QtWidgets.QWidget):
    """
    This widget serve for display all the actions in the library
    """
    tag_filter_state = []

    def __init__(self, *args, **kwargs):
        super(LibraryWidget, self).__init__(*args, **kwargs)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        label = QtWidgets.QLabel("Click to create selected action"
                                 " under current graph", self)

        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("Search")
        self.action_lib_view = QtWidgets.QListWidget(self)
        self.actions = action_lib.list_actions()
        self.graphs = action_lib.list_graphs()
        self.tag_widget = TagWidget(self)

        main_layout.addWidget(label)
        main_layout.addWidget(self.search_line)
        main_layout.addWidget(self.action_lib_view)
        main_layout.addWidget(self.tag_widget)

        self.tag_widget.load_tags(action_lib.get_tags())
        self.update_filter_cb(self.search_line.text())
        self.search_line.textChanged.connect(self.update_filter_cb)
        self.tag_widget.check_toggled_signal.connect(self.update_filter_cb)
        self.update_filter_cb()

    @QtCore.Slot()
    def update_filter_cb(self, *args, **kwargs):
        """
        Update the library list widget according to a filter text
        Args:

        """
        filter_text = self.search_line.text()
        self.action_lib_view.clear()
        LibraryWidget.tag_filter_state = self.tag_widget.get_tag_filter()
        for name in action_lib.iter_actions(
                tag=LibraryWidget.tag_filter_state,
                name_match_str=filter_text
        ):
            item = QtWidgets.QListWidgetItem()
            cls_ = action_lib.get_action(name)
            item.setData(QtCore.Qt.ToolTipRole, str(cls_.doc))
            item.setData(QtCore.Qt.DisplayRole, name)
            item.setIcon(QtGui.QIcon(cls_.icon_path))
            item.setData(QtCore.Qt.UserRole, ["action"])
            self.action_lib_view.addItem(item)

        for name in action_lib.iter_graphs(
                name_match_str=filter_text
        ):
            item = QtWidgets.QListWidgetItem()
            team_name, path = action_lib.get_graph(name)
            item.setData(QtCore.Qt.ToolTipRole, path)
            item.setData(QtCore.Qt.DisplayRole, name)
            item.setData(QtCore.Qt.UserRole, ["graph", team_name, path])
            self.action_lib_view.addItem(item)


class TagWidget(QtWidgets.QWidget):
    check_toggled_signal = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(TagWidget, self).__init__(parent=parent)
        self.tag_items = dict()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        box = QtWidgets.QGroupBox("Tags: ")
        self.layout = FlowLayout()
        box.setLayout(self.layout)
        main_layout.addWidget(box)
        self.setLayout(main_layout)

    def load_tags(self, tags):
        for tag in tags:
            tag_item = TagChecker(tag)
            if tag in LibraryWidget.tag_filter_state:
                tag_item.setChecked(True)
            self.tag_items[tag] = tag_item
            tag_item.toggled.connect(self.check_toggled_signal.emit)
            self.layout.addWidget(tag_item)

    def get_tag_filter(self):
        filters = []
        for tag, widget in self.tag_items.items():
            if widget.isChecked():
                filters.append(tag)

        return filters


class TagChecker(QtWidgets.QCheckBox):
    def __init__(self, text):
        super(TagChecker, self).__init__(text)
        self.setFixedWidth(self.sizeHint().width())

