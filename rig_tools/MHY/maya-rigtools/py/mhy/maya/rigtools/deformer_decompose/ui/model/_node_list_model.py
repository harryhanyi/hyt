from mhy.qt.core import QtCore, QtGui
import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node


class NodeItem(object):
    class FontColor(object):
        kMesh = QtGui.QColor('#00af91')
        kNurbsSurface = QtGui.QColor("#f58634")
        kNurbsCurve = QtGui.QColor("#ffcc29")
        kLattice = QtGui.QColor("#845ec2")
        kMultiple = QtGui.QColor("#ff9292")
        kUnknown = QtGui.QColor("#e40017")

    def __init__(self, node):
        self._node = Node(node)
        self.name = self._node.name
        self._internalData = {}
        self.init_data()

    def init_data(self):
        if hasattr(self._node, "output_objects"):
            output = self._node.output_objects
            if not output:
                self._internalData['fontColor'] = NodeItem.FontColor.kUnknown
                self._internalData['outputType'] = 5
            else:
                output_type = None
                for i in output:
                    if output_type is None:
                        output_type = i.type_name
                    elif output_type != i.type_name:
                        self._internalData['fontColor'] = NodeItem.FontColor.kMultiple
                        self._internalData['outputType'] = 4
                        break
                if output_type == 'mesh':
                    self._internalData['fontColor'] = NodeItem.FontColor.kMesh
                    self._internalData['outputType'] = 0
                elif output_type == "nurbsSurface":
                    self._internalData['fontColor'] = NodeItem.FontColor.kNurbsSurface
                    self._internalData['outputType'] = 1
                elif output_type == "nurbsCurve":
                    self._internalData['fontColor'] = NodeItem.FontColor.kNurbsCurve
                    self._internalData['outputType'] = 2
                elif output_type == "lattice":
                    self._internalData['fontColor'] = NodeItem.FontColor.kLattice
                    self._internalData['outputType'] = 3

        else:
            self._internalData['fontColor'] = NodeItem.FontColor.kUnknown
            self._internalData['outputType'] = 5

    @property
    def node(self):
        return self._node

    @property
    def font_color(self):
        return self._internalData['fontColor']

    @property
    def output_type(self):
        return self._internalData['outputType']


class NodeListModel(QtCore.QAbstractListModel):
    def __init__(self, items=None, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        if items is None:
            items = []
        self._items = items

    def data(self, index, role):
        """
        Return the data fro a given role
        Args:
            index:
            role:

        Returns:

        """
        item = self._items[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return item.name
        elif role == QtCore.Qt.EditRole:
            return item.name
        elif role == QtCore.Qt.UserRole:
            return item
        elif role == QtCore.Qt.ForegroundRole:
            return item.font_color

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        """

        Args:
            section:
            orientation:
            role:

        Returns:

        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return 'Nodes'
            else:
                return 'Item {0}'.format(section)

    def insertRow(self, item, row, parentIndex=QtCore.QModelIndex()):
        self.beginInsertRows(parentIndex, self.itemCount, self.itemCount)
        self._items.insert(row, item)
        self.endInsertRows()

    @property
    def items(self):
        return self._items

    @property
    def itemCount(self):
        return len(self._items)

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for _ in range(rows):
            value = self._items[position]
            self._items.remove(value)
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def set_selected(self, index, state):
        assert isinstance(state, bool)
        item = self._items[index.row()]
        item.selected = state

    def clear(self):
        self.removeRows(0, self.rowCount(), parent=QtCore.QModelIndex())

    def refresh(self, nodeType='skinCluster'):
        self.clear()
        sel = cmds.ls(type=nodeType)
        nodes = sorted([NodeItem(i) for i in sel], key=lambda k: k.output_type)

        for node in nodes:
            self.insertRow(node, self.itemCount)



