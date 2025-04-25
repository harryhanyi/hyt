from mhy.qt.core import QtGui, QtCore, QtWidgets


class RegexCompleter(QtWidgets.QCompleter):
    def __init__(self, *args):
        QtWidgets.QCompleter.__init__(self, *args)
        self.sourceModel = None
        self.filterProxyModel = QtCore.QSortFilterProxyModel()
        self.usingOriginalModel = False

    def setModel(self, model):
        self.sourceModel = model
        self.filterProxyModel = QtCore.QSortFilterProxyModel()
        self.filterProxyModel.setSourceModel(self.sourceModel)
        QtWidgets.QCompleter.setModel(self, self.filterProxyModel)
