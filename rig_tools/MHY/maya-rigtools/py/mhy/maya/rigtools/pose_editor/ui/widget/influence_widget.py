"""

Influence list widget

"""
from PySide2 import QtWidgets, QtCore
import mhy.maya.rigtools.pose_editor.ui.view.influence_table_view as itv
import mhy.maya.rigtools.pose_editor.ui.delegate.influence_table_delegate as itd
import mhy.maya.rigtools.pose_editor.ui.model.influence_table_model as itm
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager
import mhy.maya.rigtools.pose_editor.ui.manager as manager


class InfluenceWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InfluenceWidget, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.show_attribute_switch = QtWidgets.QCheckBox("Show Attributes: ")
        self.filter_text = QtWidgets.QLineEdit(self)
        self.filter_text.setPlaceholderText("Search Influences")

        self.toolbar = QtWidgets.QToolBar("My main toolbar")

        self.view = itv.InfluenceListView(parent=self)
        self.view.setSortingEnabled(True)
        self.model = itm.InfluenceTableModel()
        self.proxy_model = QtCore.QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(QtCore.Qt.DisplayRole)
        manager.Influence_Model = self.model
        delegate = itd.InfluenceItemDelegate()

        self.view.setModel(self.proxy_model)
        self.view.setItemDelegate(delegate)

        self.view.selectionModel().selectionChanged.connect(
            self.influence_selection_changed)

        layout.addWidget(self.show_attribute_switch)
        layout.addWidget(self.filter_text)
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show_attribute_switch.stateChanged.connect(self.update_show_attribute_stat)
        self.filter_text.editingFinished.connect(self.update_search_cb)
        SignalManager.update_influence_attribute_signal.connect(self.update_ui)
        SignalManager.influence_update.connect(self.refresh_selection)
        self.update_header()

    def update_search_cb(self):
        txt = self.filter_text.text()
        self.proxy_model.setFilterRegExp(txt)

    def update_show_attribute_stat(self, stat):
        self.model.show_attributes = stat
        self.model.refresh()
        self.update_header()
        self.refresh_selection()

    def populate(self, influences):
        """
        Populated influences objects in model

        Args:
            influences(list): A list of
            `Influence <mhy.maya.rigtools.pose_editor.api.influence.Influence>`

        Returns:

        """
        self.model.populate(influences)

    def refresh_selection(self):
        """
        Refresh influence table model based on selected influences cached in pose controller

        """
        self.view.selectionModel().blockSignals(True)
        selected_influences = set()
        if manager.pose_controller:
            selected_influences = manager.pose_controller.selected_influences or set()
        selection_model = self.view.selectionModel()
        selection_model.clearSelection()
        for influence in selected_influences:
            index = self.model.find_index_from_influence_name(influence)
            index = self.proxy_model.mapFromSource(index)
            selection_model.select(
                index,
                QtCore.QItemSelectionModel.Rows |
                QtCore.QItemSelectionModel.Select)

        self.view.selectionModel().blockSignals(False)
        self.view.repaint()

    def update_ui(self, pose=None):
        """
        update the the influence list.
        """
        influence_instances = []
        if pose:
            influence_instances = pose.influences.values()
        self.populate(influence_instances)
        self.update_header()
        self.refresh_selection()

    def influence_selection_changed(self, selected, deselected):
        """
        The callback when selection changed.

        It will try to select selected objects in maya scene
        Args:
            selected(QItemSelection): Selected items
            deselected(QItemSelection): Deselected items

        """
        sel_indexes = [self.proxy_model.mapToSource(index) for index in selected.indexes() if index.column() == 0]

        selected_names = [self.model.item_from_index(index).name for index in sel_indexes]

        desel_indexes = [self.proxy_model.mapToSource(index) for index in deselected.indexes() if index.column() == 0]
        deselected_names = [self.model.item_from_index(index).name for index in desel_indexes]
        manager.influences_select_changed(selected_names, deselected_names)

    def update_header(self):
        header = self.view.horizontalHeader()
        header.setDefaultSectionSize(100)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
