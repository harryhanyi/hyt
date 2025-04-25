"""
Model module controls the backend data of influences
"""
from PySide2 import QtCore, QtGui
from mhy.maya.rigtools.pose_editor.api.utils import round_to_value

__all__ = ["InfluenceItem", "InfluenceTableModel"]


class InfluenceItem(object):
    """
    The class for data structure which model will be using
    to passed data from influence object to view
    TODO: Should work directly with data instead of influence instance

    """

    def __init__(self, influence):
        self.influence = influence
        self.name = influence.name
        self.attributes = {}
        self.init_data()

    def init_data(self):
        """
        Initialize attribute dictionary from influence instance

        """
        for attr, neutral in self.influence.attributes.items():
            neutral = neutral.get('neutral', 0.0)
            val = self.influence.get_attribute(attr)
            self.attributes[attr] = [val, neutral]


class InfluenceTableModel(QtCore.QAbstractTableModel):
    def __init__(self, items=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.show_attributes = False
        self.__pose = None
        self.attributes = []
        if items is None:
            items = []
        self.__items = items

    @property
    def influences(self):
        return self.__items

    @property
    def pose(self):
        return self.__pose

    @pose.setter
    def pose(self, val):
        self.__pose = val

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
        item = self.influences[row]
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return item.name
            else:
                attr_name = self.attributes[column-1]
                val_neutral = item.attributes.get(attr_name)
                if val_neutral is None:
                    # Influence's attribute named this
                    # is not added as influence
                    return ""
                return str(round_to_value(val_neutral[0], decimal=4))

        elif role == QtCore.Qt.BackgroundColorRole:
            color = QtGui.QColor(QtCore.Qt.transparent)
            if column > 0:
                attr_name = self.attributes[column - 1]
                val_neutral = item.attributes.get(attr_name)
                if val_neutral is not None:
                    val, neutral = val_neutral
                    if abs(val - neutral) > 0.0001:
                        if row % 2:
                            color = QtGui.QColor('#3a6351')
                        else:
                            color = QtGui.QColor('#385e4d')
            return QtGui.QBrush(color)

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
                if section == 0:
                    return 'Influence'
                else:
                    return self.attributes[section-1]
            else:
                return str(section+1)

    def insertRows(self, items, row, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row + len(items)-1)
        for item in items[::-1]:
            self.influences.insert(row, item)
        self.endInsertRows()

    def insertColumns(self, attributes, column, parent=QtCore.QModelIndex()):
        self.beginInsertColumns(parent, column, column+len(attributes)-1)
        for attr in attributes[::-1]:
            self.attributes.insert(column, attr)
        self.endInsertColumns()

    @property
    def influence_count(self):
        return len(self.influences)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            value = self.influences[row]
            self.influences.remove(value)
        self.endRemoveRows()
        return True

    def removeColumns(self, column, count, parent=QtCore.QModelIndex()):
        self.beginRemoveColumns(parent, column, column + count - 1)
        if self.show_attributes:
            for _ in range(count):
                attr = self.attributes[column]
                self.attributes.remove(attr)
        self.endRemoveColumns()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        The number to rows
        Args:
            parent(QtCore.QModelIndex): The parent index

        Returns:
            int: number of row
        """
        return len(self.influences)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        The number of columns: 1 for influence column + number of attributes
        Args:
            parent(QtCore.QModelIndex): The parent index

        Returns:
            (int): number of column

        """
        if self.show_attributes:
            return 1 + len(self.attributes)
        return 1

    def clear(self):
        """
        Clear the rows and attribute columns

        """
        self.removeRows(0, self.rowCount())
        self.removeColumns(0, len(self.attributes))
        self.attributes = []

    def refresh(self):
        influences = [i.influence for i in self.influences]
        self.populate(influences)

    def populate(self, influences):
        """
        This method clear existing data and populate
        influences items in the model
        Args:
            influences(list): A list of InfluenceItem

        """
        self.clear()
        attributes = []
        items = []
        for inf in influences:
            items.append(InfluenceItem(inf))
            attributes = attributes + list(inf.attributes.keys())
            attributes = sorted(list(set(attributes)))
        if self.show_attributes:
            self.insertColumns(attributes, 0)
        self.insertRows(items, 0)

    def find_index_from_influence_name(self, name):
        """
        Trying to find an index whose associated item's name
        is matching the argument
        Args:
            name(str): A name to search item with

        Returns:
            QtCore.QModelIndex
        """
        for row, inf in enumerate(self.influences):
            if inf.name == name:
                return self.index(row, 0)

        return QtCore.QModelIndex()

    def item_from_index(self, index):
        """
        Get the associated item from a given index
        Args:
            index(QtCore.QModelIndex):

        Returns:
            InfluenceItem

        """
        if not index.isValid():
            return
        row = index.row()
        if not row >= 0 and row < len(self.influences):
            return
        return self.influences[row]

    @staticmethod
    def delete_influences(pose, influence_names):
        """
        Remove influences to the active pose.
        """
        pose.delete_influences(influence_names)





