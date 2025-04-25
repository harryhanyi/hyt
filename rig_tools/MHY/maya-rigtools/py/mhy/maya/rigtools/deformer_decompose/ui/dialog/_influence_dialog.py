from mhy.qt.core import QtWidgets, QtCore, QtGui
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya


class InfluenceDialog(QtWidgets.QDialog):
    def __init__(self, node, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        mainLayout = QtWidgets.QVBoxLayout()
        self.node = node
        self.setWindowTitle('Influence of: {}'.format(self.node.name))
        self.setLayout(mainLayout)
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.showContextMenu)
        self.listWidget.doubleClicked.connect(self.doubleClickedTriggered)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listWidget.setMinimumWidth(400)
        mainLayout.addWidget(self.listWidget)
        selButton = QtWidgets.QPushButton("Select In The Scene")
        selButton.clicked.connect(self.selectInfluences)
        selAllButton = QtWidgets.QPushButton("Select All In The Scene")
        selAllButton.clicked.connect(self.selectAllInfluences)
        mainLayout.addWidget(selButton)
        mainLayout.addWidget(selAllButton)

        self.refresh()

    def refresh(self):
        self.clear()
        influences = self.node.influences
        self.addItems(influences)

    def clear(self):
        self.listWidget.clear()

    def addItems(self, items):
        self.listWidget.addItems(items)

    def selectInfluences(self):
        sel = self.listWidget.selectedIndexes()
        objToSelect = []
        for i in sel:
            name = i.data(QtCore.Qt.DisplayRole)
            if cmds.objExists(name):
                objToSelect.append(name)
            else:
                OpenMaya.MGlobal.displayWarning('{} does not exists'.format(name))
        cmds.select(objToSelect)

    def selectAllInfluences(self):
        self.listWidget.selectAll()
        self.selectInfluences()

    def showContextMenu(self, point):
        menu = QtWidgets.QMenu(self)
        selAllAction = QtWidgets.QAction("Select All", self)
        selAllAction.triggered.connect(self.listWidget.selectAll)
        menu.addAction(selAllAction)
        delSelAllAction = QtWidgets.QAction("Deselect All", self)
        delSelAllAction.triggered.connect(self.listWidget.clearSelection)
        menu.addAction(delSelAllAction)
        menu.exec_(QtGui.QCursor.pos())

    def doubleClickedTriggered(self, index):
        item = index.data(QtCore.Qt.DisplayRole)
        if cmds.objExists(item):
            cmds.select(item)
        else:
            OpenMaya.MGlobal.displayWarning('{} does not exists in the scene'.format(item))
