from mhy.qt.core import QtCore


class NodesSortFilterProxyModel(QtCore.QSortFilterProxyModel):

    def insertRow(self, item, row, parentIndex=QtCore.QModelIndex()):
        sourceParentIndex = self.mapToSource(parentIndex)
        self.sourceModel().insertRow(item, row, sourceParentIndex)

    @property
    def items(self):
        return self.sourceModel().items()

    @property
    def itemCount(self):
        return self.sourceModel().itemCount

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        sourceParentIndex =self.mapToSource(parent)
        self.sourceModel().removeRows(position, rows, sourceParentIndex)

    def setSelected(self, index, state):
        sourceIndex = self.mapToSource(index)
        self.sourceModel().set_selected(sourceIndex, state)

    def refresh(self, nodeType):
        self.sourceModel().refresh(nodeType)
