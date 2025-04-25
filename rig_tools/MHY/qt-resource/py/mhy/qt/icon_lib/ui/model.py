from mhy.qt.core import QtCore, QtGui
import math


class IconItem(object):
    def __init__(self, container):
        self.container = container
        self.icon = None
        child = container.find_biggest_png_if_any()
        path = child.full_path
        pix_map = QtGui.QPixmap(path)
        scaled_map = pix_map.scaled(QtCore.QSize(40, 40))
        self.p = path
        self.icon = scaled_map
        self.name = container.name

    def find_child(self, format, size=None):
        return self.container.find_child(format, size)


class IconTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(IconTableModel, self).__init__(parent=parent)
        self.__items = list()
        self.num_items = 0
        self.num_row = 0

    @property
    def items(self):
        return self.__items

    def populate_items(self, items):
        self.clear()
        self.insertRows(items, 0)

    def insertRows(self, items, row, parent=QtCore.QModelIndex()):
        self.num_row = math.ceil((float(len(items))/self.columnCount()))
        self.num_items = len(items)
        self.beginInsertRows(parent, row, row + self.num_row-1)
        self.__items = [IconItem(item) for item in items]
        self.endInsertRows()

    def data(self, index, role):
        """
        Override the virtual method to return the data from a given role
        Args:
            index(QtCore.QModelIndex): The index the data is associated with
            role(QtCore.Qt.ItemDataRole): The role used to associate data

        Returns:
            data for index with specific role
        """
        row = index.row()
        column = index.column()
        idx = row*self.columnCount() + column
        if idx >= self.num_items:
            return
        icon_item = self.__items[idx]
        if role == QtCore.Qt.DecorationRole:
            return icon_item.icon

        if role == QtCore.Qt.ToolTipRole:
            return icon_item.p

        if role == QtCore.Qt.UserRole:
            return icon_item

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        The number to rows
        Args:
            parent(QtCore.QModelIndex): The parent index

        Returns:
            int: number of row
        """
        return self.num_row

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        The number of columns: 1 for influence column + number of attributes
        Args:
            parent(QtCore.QModelIndex): The parent index

        Returns:
            (int): number of column

        """
        return 10

    def clear(self):
        """
        Clear the rows and attribute columns

        """
        self.removeRows(0, self.rowCount())

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        self.__items = []
        self.endRemoveRows()
        return True

    def add_icon(self, icon_container):
        item = IconItem(icon_container)
        self.items.append(item)
        if len(self.items) > self.rowCount():
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount()+1)
            self.endInsertRows()
