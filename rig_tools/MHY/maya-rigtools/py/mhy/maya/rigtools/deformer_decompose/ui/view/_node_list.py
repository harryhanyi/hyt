from mhy.qt.core import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from mhy.maya.nodezoo.node import Node
from mhy.maya.rigtools.deformer_decompose.ui.dialog import InfluenceDialog


class NodeListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        QtWidgets.QListView.__init__(self, parent)
        self.nodeType = None
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.doubleClicked.connect(self.double_clicked_triggered)

    @staticmethod
    def double_clicked_triggered(index):
        item = index.data(QtCore.Qt.UserRole)
        if cmds.objExists(item.name):
            cmds.select(item.name)
        else:
            OpenMaya.MGlobal.displayWarning('{} does not exists in the scene'.format(item.name))

    def show_context_menu(self, point):
        menu = QtWidgets.QMenu(self)
        selAllAction = QtWidgets.QAction("Select All", self)
        selAllAction.triggered.connect(self.selectAll)
        menu.addAction(selAllAction)
        delSelAllAction = QtWidgets.QAction("Deselect All", self)
        delSelAllAction.triggered.connect(self.clearSelection)
        menu.addAction(delSelAllAction)

        menu.addSeparator()
        selectInSceneAction = QtWidgets.QAction("Select In Scene", self)
        selectInSceneAction.triggered.connect(self.selItemsInScene)
        selectInSceneAction.setToolTip("Select selected items in maya scene")
        menu.addAction(selectInSceneAction)
        # fixNameAction = QtWidgets.QAction("Fix Name", self)
        # fixNameAction.triggered.connect(self.fixNameForSelectedItems)
        # fixNameAction.setToolTip("Rename node based on the deformed object and node Type")
        # menu.addAction(fixNameAction)
        if self.nodeType == "skinCluster":
            showInfluenceAction = QtWidgets.QAction("Show Influences", self)
            showInfluenceAction.triggered.connect(self.showInfluenceDialog)
            showInfluenceAction.setToolTip("List the influence object of selected skin cluster")
            menu.addAction(showInfluenceAction)
        menu.addSeparator()

        refreshAction = QtWidgets.QAction("&Refresh", self)
        menu.addAction(refreshAction)
        refreshAction.triggered.connect(self.refresh)
        menu.addSeparator()

        menu.exec_(QtGui.QCursor.pos())

    def selectAll(self):
        QtWidgets.QListView.selectAll(self)
        self.selItemsInScene()

    def clearSelection(self):
        QtWidgets.QListView.clearSelection(self)
        cmds.select(clear=True)

    def selItemsInScene(self):
        """
        Select objects of selected items in the table view from the maya scene
        """
        selModel = self.selectionModel()
        sellectedRows = selModel.selectedRows()
        proxyModel = self.model()
        selList = []
        for row in sellectedRows:
            sourceIndex = proxyModel.mapToSource(row)
            item = sourceIndex.data(QtCore.Qt.UserRole)
            if cmds.objExists(item.name):
                selList.append(item.name)
            else:
                OpenMaya.MGlobal.displayWarning('{} does not exists in the scene'.format(item.name))
        selList = list(set(selList))
        cmds.select(selList)

    def fixNameForSelectedItems(self):
        """
        Rename node based on the deformed object and node Type
        """
        selModel = self.selectionModel()
        sellectedRows = selModel.selectedRows()
        proxyModel = self.model()
        selList = []
        for row in sellectedRows:
            sourceIndex = proxyModel.mapToSource(row)
            item = sourceIndex.data(QtCore.Qt.UserRole)
            if cmds.objExists(item.name):
                node = Node(item.name)

            else:
                OpenMaya.MGlobal.displayWarning('{} does not exists in the scene'.format(item.name))
        selList = list(set(selList))
        cmds.select(selList)

    def updateNodeType(self, nodeType):
        self.nodeType = nodeType
        self.refresh()

    def refresh(self):
        """
        Refresh the list view with all the objects of the selected
        type in the current scene
        Returns
        -------

        """
        self.model().refresh(self.nodeType)

    def showInfluenceDialog(self):
        selModel = self.selectionModel()
        sellectedRows = selModel.selectedRows()
        assert len(sellectedRows) == 1, "Please select only one skin cluster"
        proxyModel = self.model()
        row = sellectedRows[0]
        sourceIndex = proxyModel.mapToSource(row)
        item = sourceIndex.data(QtCore.Qt.UserRole)
        assert cmds.objExists(item.name), "{} does not exists".format(item.name)
        node = Node(item.name)
        dialog = InfluenceDialog(node, parent=self)
        dialog.refresh()
        dialog.show()
