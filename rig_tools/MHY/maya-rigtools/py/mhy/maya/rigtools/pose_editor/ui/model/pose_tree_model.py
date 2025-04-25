"""
Model module controls the backend data of pose tree
"""


import six
import json

import sys
from mhy.python.core.compatible import gzip_export

if sys.version_info[0] == 3:
    import pickle as cPickle
else:
    import cPickle

from PySide2 import QtCore, QtGui, QtWidgets
import maya.OpenMaya as OpenMaya

import mhy.maya.rigtools.pose_editor.api.utils as utils
import mhy.maya.rigtools.pose_editor.api.pose_controller as pose_controller
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
from mhy.maya.rigtools.pose_editor.settings import Settings
from mhy.maya.rigtools.pose_editor.api.pose import Pose
from mhy.maya.rigtools.pose_editor.ui.signalManager import SignalManager


class ItemBase(object):
    """
    The Base class for pose item and group item
    """
    type_str = None

    def __init__(self, name):
        self.__parent = None
        self.__children = []
        self.__name = name
        self.free_to_rename = True

    def __repr__(self):
        return "<0>.{1}: '{2}'> at <{3}>".format(
            self.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self))
        )

    def __eq__(self, other):
        if not isinstance(other, ItemBase):
            return False
        else:
            return self.full_path() == other.full_path()

    @property
    def name(self):
        """
        get the name of this item

        """
        return str(self.__name)

    @name.setter
    def name(self, val):
        """
        Set the cahced name variable. It won't make any difference of pose attributes
        Args:
            val(str):

        Returns:

        """
        self.__name = val

    @property
    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, p):
        self.__parent = p

    def child(self, row):
        return self.__children[row]

    @property
    def children(self):
        return self.__children

    def child_count(self):
        """
        Get the number of children directly under this item
        Returns:
            int: The number of children
        """
        return len(self.__children)

    def append_child(self, child):
        """
        Append a child item to this
        Args:
            child(PoseItem or GroupItem):

        """

        self.__children.append(child)
        child.parent = self

    def remove_child(self, position):
        """
        Remove the child item at given row position
        Args:
            position(int): The row number to be removed

        """
        child = self.child(position)
        child.parent = None
        self.__children.pop(position)

    def insert_child(self, position, child):
        if position < 0 or position > len(self.__children):
            return False
        self.__children.insert(position, child)
        child.parent = self
        return True

    def full_path(self):
        path = self.name
        if self.parent and self.parent.name:
            path = '{}|{}'.format(self.parent.full_path(), self.name)
        return path

    def parent_full_path(self):
        if self.parent:
            return self.parent.full_path()
        else:
            return ''


class PoseItem(ItemBase):
    type_str = 'pose'

    def __init__(self, name):
        super(PoseItem, self).__init__(name=name)
        self.pose = None
        self.input_attribute_full_name = None
        self.__influence_number = None
        self.__target_number = None
        self.is_corrective = False

        # Weight related variables
        self.step = 1.0
        self.high = 10.0
        self.low = 0.0

    @property
    def weight(self):
        return self.pose.weight

    @weight.setter
    def weight(self, value):
        self.pose.weight = value

    @property
    def influence_number(self):
        return self.__influence_number

    @influence_number.setter
    def influence_number(self, value):
        self.__influence_number = value

    @property
    def target_number(self):
        return self.__target_number

    @target_number.setter
    def target_number(self, value):
        self.__target_number = value

    def init_from_pose(self, pose):
        self.pose = pose
        if pose.has_influence_cache():
            self.__influence_number = len(pose.influences)
        if pose.has_target_cache():
            self.__target_number = len(pose.targets)
        self.is_corrective = pose.is_corrective
        self.input_attribute_full_name = self.pose.input_attribute_full_name

    def rename(self, new_name):
        self.name = new_name
        return new_name

    def get_side_name(self, new_name):
        split = new_name.split('_')
        if len(split) > 1 and split[-1] in set(Settings.mid_poses_group + Symmetry.suffix):
            new_name = '_'.join(split[:-1])
        parent_full_path = self.parent_full_path()
        ancestors = parent_full_path.split('|')[::-1]
        side_info = 'M'
        for parent in ancestors:
            if parent in Symmetry.suffix:
                side_info = parent
                break
            elif parent in Settings.mid_poses_group:
                break
        new_name = "{}_{}".format(new_name, side_info)
        return new_name

    def export(self):
        data = {'name': self.name,
                'type': 'pose'}
        return data

    def find_leaves(self):
        return [self]

    def get_pose_data(self):
        return self.pose.get_data()


class GroupItem(ItemBase):
    type_str = 'group'

    class GroupType(object):
        Empty = 0
        Pose_Group = 1
        Level_Group = 2

    def find_child_by_name(self, name):
        for child in self.children:
            if child.name == name:
                return child

    def export_(self):
        data = None
        for child in self.children:
            if child.type_str == 'group':
                if data is None:
                    data = dict()
                data[child.name] = child.export()
            else:
                if data is None:
                    data = list()
                data.append(child.name)
        return data

    def export(self):
        data = {'type': 'group'}
        if self.name:
            data['name'] = self.name

        children_data = []
        for i in self.children:
            child_data = i.export()
            if child_data:
                children_data.append(child_data)
        if children_data:
            data['children'] = children_data
        return data

    def rename(self, new_name):
        self.name = new_name
        return new_name

    def find_leaves(self):
        """
        Get all poses under this group's hierarchy
        Returns:
            list: A list of leaf pose items
        """
        leaves = []
        for child in self.children:
            leaves.extend(child.find_leaves())
        return leaves


class PoseTreeModel(QtCore.QAbstractItemModel):
    """

    A drag and drop enabled, editable, hierarchical item model

    """
    Update_Select_Signal = QtCore.Signal(object)
    Mimedata_Type = "application/x-move-pose.list"

    Column_Headers = ['Pose', 'Weight', 'Influences', 'Targets']
    Pose_Index = Column_Headers.index('Pose')
    Weight_Index = Column_Headers.index('Weight')
    Influences_Index = Column_Headers.index('Influences')
    Targets_Index = Column_Headers.index('Targets')

    @property
    def maya_node_obj_handle(self):
        if self.ctrl_node:
            return self.ctrl_node.maya_handle

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self.root_item = GroupItem('')
        self.__target_is_enabled = True
        self.__controller = None
        SignalManager.influence_cache_finished_signal.connect(self.update_pose_cb)
        SignalManager.target_cache_finished_signal.connect(self.update_pose_cb)

    @property
    def controller(self):
        return self.__controller

    @controller.setter
    def controller(self, val):
        """
        Called when updating controller instance associated with this model.
        If the pose tree is old format, this method will convert it to new format.
        Args:
            val(None or PoseController):

        """
        assert val is None or isinstance(val, pose_controller.PoseController), \
            "{} is not a valid pose controller instance".format(val)

        self.__controller = val
        if val:
            val.refresh_poses()
            pose_tree = val.pose_tree
            # Check the data format and populate items using the corresponding method
            pose_tree = self.refresh_pose_tree(pose_tree, val.poses)
            val.pose_tree = pose_tree
        else:
            self.clear()
        self.update_target_status()

    def refresh_pose_tree(self, pose_tree, poses=None):
        if 'type' in pose_tree:
            self.populate(pose_tree, poses)
        else:
            self.populate_(pose_tree)
            pose_tree = self.root_item.export()
            # Converted old data to new data format
        return pose_tree

    def rowCount(self, index=QtCore.QModelIndex()):
        item = self.item_from_index(index)
        return item.child_count()

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(PoseTreeModel.Column_Headers)

    def data(self, index, role):
        """

        Args:
            index:
            role:

        Returns:

        """
        if not index.isValid():
            return None

        item = self.item_from_index(index)
        row = index.row()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == PoseTreeModel.Pose_Index:
                return item.name

            if isinstance(item, PoseItem):
                if index.column() == PoseTreeModel.Weight_Index:
                    return utils.round_to_str(item.weight)
                elif index.column() == PoseTreeModel.Influences_Index:
                    if item.influence_number is None:  # The data is still in caching process
                        return "..."
                    else:
                        return str(item.influence_number)
                elif index.column() == PoseTreeModel.Targets_Index:
                    if item.target_number is None:
                        return "..."  # The data is still in caching process
                    else:
                        return str(item.target_number)

        elif role == QtCore.Qt.BackgroundRole:
            color = QtGui.QColor(QtCore.Qt.transparent)
            if item.type_str == "pose":
                if index.column() == PoseTreeModel.Influences_Index:
                    if item.influence_number is None:
                        color = QtGui.QColor(99, 80, 58, 220)
                    elif item.influence_number:
                        if row % 2:
                            color = QtGui.QColor(58, 99, 81, 220)
                        else:
                            color = QtGui.QColor(58, 99, 81, 255)
                elif index.column() == PoseTreeModel.Targets_Index:
                    if item.target_number is None:
                        color = QtGui.QColor(99, 80, 58, 220)

                    if not self.__target_is_enabled:
                        color = QtGui.QColor(133, 50, 63, 100)

                    elif item.target_number:
                        if row % 2:
                            color = QtGui.QColor(58, 99, 81, 220)
                        else:
                            color = QtGui.QColor(58, 99, 81, 255)

                elif index.column() == PoseTreeModel.Weight_Index:
                    if row % 2:
                        color = QtGui.QColor(217, 167, 28, 130)
                    else:
                        color = QtGui.QColor(217, 167, 28, 100)

            return QtGui.QBrush(color)

        elif role == QtCore.Qt.ForegroundRole:
            if item.type_str == 'group':
                return QtGui.QColor(QtCore.Qt.white)
            elif item.type_str == 'pose' and item.is_corrective:
                return QtGui.QColor('#a0d7f2')
            return QtGui.QColor('#b4cfae')

        elif role == QtCore.Qt.ToolTipRole:
            if item.type_str == 'pose':
                if index.column() == PoseTreeModel.Targets_Index:
                    return "Clicked target header section to turn on/off blend shape"
                else:
                    return str(item.input_attribute_full_name)

        elif role == QtCore.Qt.UserRole:
            if item.type_str == "pose" and \
                    index.column() == PoseTreeModel.Weight_Index:
                return item.weight

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Override setData to update data of index at specific role
        Args:
            index(QModelIndex):
            value(str or float):
            role(int):

        Returns:

        """
        if not index.isValid():
            return False
        column = index.column()

        item = self.item_from_index(index)
        if column == PoseTreeModel.Pose_Index:
            if not value:
                return False
            if item.type_str == "pose":
                value = self.controller.rename_pose(item.pose, value)
            if value:
                item.rename(value)
                self.sync_pose_tree()

        elif column == PoseTreeModel.Weight_Index:
            item.weight = value
        elif column == PoseTreeModel.Influences_Index:
            item.influence_number = value
        elif column == PoseTreeModel.Targets_Index:
            item.target_number = value
        self.dataChanged.emit(index, index)
        return True

    def clear(self, root_index=None):
        if root_index is None:
            root_index = self.index_of(self.root_item)
        index = self.index(0, 0, root_index)
        while index.isValid():
            self.deleteRow(0, root_index)
            index = self.index(0, 0, root_index)

    def reset_weights(self, exclude=None):
        need_update_poses = dict()
        for pose_item in self.root_item.find_leaves():
            if exclude and pose_item.name in exclude:
                continue
            pose = pose_item.pose
            if pose:
                current_weight = pose.weight
                if current_weight != 0.0:
                    index = self.index_of(pose_item)
                    row = index.row()
                    index = index.sibling(row, PoseTreeModel.Weight_Index)
                    self.setData(index, 0.0)
                    need_update_poses[pose.name] = pose.weight
        return need_update_poses

    def reset_pose(self, pose_name, remove_influence=False):
        """
        set the controller from IO
        """
        pose = self.controller.poses.get(pose_name)
        if not pose:
            return
        self.do_at_neutral_pose(pose.reset, remove_influence)

    @property
    def pose_tree(self):
        return self.root_item.export_()

    def deleteRow(self, row, parent_index=None):
        if parent_index is None:
            parent_index = self.root_item
        self.beginRemoveRows(parent_index, row, row)

        parent_item = self.item_from_index(parent_index)
        parent_item.remove_child(row)

        self.endRemoveRows()

    def find_item_from_full_path(self, full_path):
        """
        Return the item from the full path to the item you want to find

        Args:
            full_path(str): The full path of the target item

        Returns:
            GroupItem or PoseItem: Return the found item if exists

        """
        path_parts = full_path.split('|')
        parent = self.root_item
        return self._recursive_find_item(parent, path_parts)

    def _recursive_find_item(self, parent, path):
        """
        Recursively find the item under a parent with a given hierarchy path
        Args:
            parent(GroupItem):
            path(list): A list of each hierarchy name in an order
            from top to down

        Returns:


        """
        name = path[0]
        if parent.type_str == 'group':
            for child in parent.children:
                if child.name == name:
                    if not path[1:]:
                        return child
                    elif child.type_str == 'pose':
                        # We don't have any way to keep searching for the
                        # remaining path
                        return None
                    else:
                        return self._recursive_find_item(child, path[1:])
            return None

    def mimeTypes(self):
        """

        Returns:

        """
        return [PoseTreeModel.Mimedata_Type]

    def mimeData(self, indexes):
        """

        Args:
            indexes:

        Returns:

        """
        data = []
        for idx in indexes:
            item = self.item_from_index(idx)
            data.append(item.full_path())
        binary_str = cPickle.dumps(data)
        mime_data = QtCore.QMimeData()
        mime_data.setData(PoseTreeModel.Mimedata_Type, binary_str)
        return mime_data

    def canDropMimeData(self, data, action, row, column, parent):
        """
        Check if drop mime data is valid so user can see the indicator

        Args:
            data(QMimeData): The data trying to be dropped
            action(QtCore.Qt.DropAction):
            row(int):
            column(int):
            parent(QModelIndex):

        Returns:
            bool: If accept drop mime data
        """
        parent_item = self.item_from_index(parent)
        if parent_item.type_str == 'pose':
            return False
        return True

    def dropMimeData(self, data, action, row, column, parent):
        """
        Drop the mime data to the given position
        Args:
            data(QMimeData): The data trying to be dropped
            action(QtCore.Qt.DropAction):
            row(int):
            column(int):
            parent(QModelIndex):

        Returns:
            bool: If succeed

        """
        byte_str = data.retrieveData(PoseTreeModel.Mimedata_Type, str)
        paths = cPickle.loads(str(byte_str))
        parent_item = self.item_from_index(parent)

        for path in paths:
            item = self.find_item_from_full_path(path)
            if item:
                for child in parent_item.children:
                    if child == item:
                        if row > item.row:
                            row = row - 1
                index = self.index_of(item)
                self.__remove_index(index)

                self.insertRow(item, row, parent)
                new_index = self.index_of(item)
                self.Update_Select_Signal.emit(new_index)
                self.sync_pose_tree()

        return True

    def flags(self, index):
        """
        Valid items are selectable, editable, and drag and drop enabled
        Invalid indices (open space in the view) are also drop enabled,
        so you can drop items onto the top level
        """
        default_flag = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        item = self.item_from_index(index)
        if item.type_str == 'pose' and index.column() == PoseTreeModel.Weight_Index:
            return QtCore.Qt.ItemIsEditable
        return default_flag | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.Column_Headers[section]

    def index(self, row, column, parentIndex):
        """
        Args:
            row(int):The row of the index to return.
            column(int): The column of the index to return.
            parentIndex: The index of the parent of the index to return.

        Returns:
            (QtCore.QModelIndex)
        """

        if not self.hasIndex(row, column, parentIndex):
            return QtCore.QModelIndex()
        parent = self.item_from_index(parentIndex)

        return self.createIndex(row, column, parent.child(row))

    def index_of(self, item, column=0):
        """
        Return the QModelIndex for the given item.
        :param item:
        :param column:
        :return:
        """
        if item.parent is None:
            return QtCore.QModelIndex()

        for row, childItem in enumerate(item.parent.children):
            if childItem is item:
                return self.index(row, column, self.index_of(item.parent))

        return QtCore.QModelIndex()

    def parent(self, index):
        item = self.item_from_index(index)
        parent = item.parent
        if not parent:
            return QtCore.QModelIndex()

        if parent == self.root_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent.row, 0, parent)

    def __remove_index(self, index):
        """
        This method only modify the data inside of this ui model.
        It won't make any change to the associated data. User is responsible to
        do it if it is necessary.
        Args:
            index(QModelIndex):

        """
        parent = self.parent(index)
        item = self.item_from_index(index)
        self.deleteRow(item.row, parent)

    def insertRow(self, item, row, parent_index):
        parent = self.item_from_index(parent_index)
        if row == -1:
            row = parent.child_count()
            self.beginInsertRows(
                parent_index,
                parent.child_count(),
                parent.child_count())
            parent.insert_child(parent.child_count(), item)
            self.endInsertRows()
        else:
            self.beginInsertRows(parent_index, row, row)
            parent.insert_child(row, item)
            self.endInsertRows()
        insert_index = self.index(row, 0, parent_index)
        return insert_index

    def item_from_index(self, index=None):
        if not index:
            return self.root_item
        return index.internalPointer() if index.isValid() else self.root_item

    def populate_(self, pose_name_tree):
        self.clear()
        self.populate_item_recurse_(self.root_item, pose_name_tree)

    def populate(self, pose_tree, poses=None):
        """
        Populate pose tree into the model
        Args:
            pose_tree:
            poses(dict): Added arbitrary poses to the tree model. If any of them are
            not nested in the tree hierarchy, they will be added under the root
        Returns:

        """
        print('Populate pose tree data...')
        self.clear()
        pose_trees = pose_tree.get('children', [])
        added_poses = self.populate_item_recurse(self.root_item, pose_trees)
        if poses:
            for name, inst in poses.items():
                parent_index = self.index_of(self.root_item)
                if name not in added_poses:
                    child_item = PoseItem(name)
                    child_item.init_from_pose(inst)
                    row = self.root_item.child_count()
                    self.insertRow(child_item, row, parent_index)
                    inst.start_cache_job(using_threading=True)

    def populate_item_recurse(self, root, pose_trees, merge=False, filter_list=None):
        """

        Args:
            root(GroupItem):
            pose_trees:
            merge(bool): If in merge mode and there is existing item with the same name,
            this method will override existing item instead of adding a new one
            filter_list(list or None): Filter out poses not in the filter list if given

        Returns:
            list: Get a list of poses that are populated
        """
        poses = []
        parent_index = self.index_of(root)
        for pose_tree in pose_trees:
            item_type = pose_tree.get('type')
            name = pose_tree.get('name')
            existing_item = root.find_child_by_name(name)
            item_created = True
            if item_type == 'group':
                if merge and existing_item:
                    if existing_item.type_str == 'group':
                        child_item = existing_item
                        item_created = False
                    else:
                        continue
                else:
                    child_item = GroupItem(name)
                if item_created:
                    row = root.child_count()
                    self.insertRow(child_item, row, parent_index)

                children = pose_tree.get('children')
                if children:
                    poses.extend(
                        self.populate_item_recurse(
                            child_item,
                            children,
                            merge,
                            filter_list))

            elif item_type == 'pose':
                pose = self.controller.get_pose(name)
                if merge:
                    if filter_list is not None and name not in filter_list:
                        continue
                child_item = PoseItem(pose.name)
                if pose:
                    child_item.init_from_pose(pose)
                    row = root.child_count()
                    self.insertRow(child_item, row, parent_index)
                    pose.start_cache_job(using_threading=True)

                poses.append(pose.name)
        return poses

    def update_pose_cb(self, pose):
        """
        This call back method is a slot receiving signal from threading pose data
        updates. It will refresh influence and target number vars in the pose item
        end update index in the model
        Args:
            pose(Pose): The pose has updates

        """
        idx = self.get_index_by_pose_name(pose.name)
        if not idx:
            return
        item = self.item_from_index(idx)

        item.init_from_pose(pose)
        row = idx.row()
        if pose.has_influence_cache():
            idx = idx.sibling(row, PoseTreeModel.Influences_Index)
            self.setData(idx, len(pose.influences))
        if pose.has_target_cache():
            idx = idx.sibling(row, PoseTreeModel.Targets_Index)
            self.setData(idx, len(pose.targets))

    def populate_item_recurse_(self, parent_item, pose_name_tree):
        """
        create all necessary item line based on a tree structure
        """
        for parent, children in pose_name_tree.items():
            child_item = GroupItem(parent)
            if child_item.name in Symmetry.suffix:
                child_item.free_to_rename = False

            parent_item.append_child(child_item)
            # Recurse children and perform the same action
            if isinstance(children, dict):
                self.populate_item_recurse_(child_item, children)
            elif isinstance(children, list):
                for pose_name in children:
                    pose = self.controller.get_pose(pose_name)
                    pose_item = PoseItem(pose.name)
                    if pose:
                        pose_item.init_from_pose(pose)

                    child_item.append_child(pose_item)

    def create_pose(self, pose_name, parent=None, after_row=0):
        """
        Create a new pose under a given parent item after a given row
        Args:
            pose_name(str): Give a unique name
            parent(GroupItem): A group item the new pose will be pareted to
            after_row(int): The row new pose will be created after

        Returns:
            (QModelIndex): The newly created index
        """

        pose = self.controller.create_pose(pose_name)
        idx = self.insert_pose(pose, parent, after_row)
        return idx

    def insert_pose(self, pose, parent=None, after_row=0):
        """
        Insert a pose instance to the model under a parent item
        Args:
            pose(Pose):
            parent(GroupItem):
            after_row(int):

        Returns:

        """
        pose_item = PoseItem(pose.name)
        if pose:
            pose_item.init_from_pose(pose)

        parent_index = self.index_of(parent)
        idx = self.insertRow(pose_item, after_row, parent_index)
        self.sync_pose_tree()
        return idx

    def create_group(self, group_name, parent=None, after_row=0):
        """
        Creat an empty group item under a given parent item
        Args:
            group_name(str): Name of the group item
            parent(GroupItem):
            after_row(int): After which row will the new group item be inserted

        Returns:
            (QModelIndex): The new index created

        """
        group_item = GroupItem(group_name)
        parent_index = self.index_of(parent)
        idx = self.insertRow(group_item, after_row, parent_index)
        self.sync_pose_tree()
        return idx

    def delete_item(self, item):
        """
        Delete an pose item or group item from the model, also delete the all the poses under
        index hierarchy. This should be called to modify the scene and ui at the same time

        Args:
            item(PoseItem or GroupItem):

        """
        index = self.index_of(item)
        if not index.isValid():
            return
        self.__remove_index(index)
        if item.type_str == 'pose':
            self.controller.delete_pose(item.pose.name)
            OpenMaya.MGlobal.displayInfo("Removed pose {}".format(item.pose.name))
        elif item.type_str == 'group':
            pose_items = item.find_leaves()
            for pose_item in pose_items:
                self.controller.delete_pose(pose_item.pose.name)
                OpenMaya.MGlobal.displayInfo("Removed pose {}".format(pose_item.pose.name))
        self.sync_pose_tree()
        SignalManager.refresh_corrective_view_signal.emit()

    def get_mirror_pose(self, pose):
        """
        Get the mirrored pose item. If not exists, created one.
        This function will also create group hierarchy if necessary
        Args:
            pose(Pose):

        Returns:
            Pose: Mirror target pose

        """
        mirrored_pose = self.controller.get_mirror_pose(pose)
        if self.get_pose_item_by_pose_name(mirrored_pose.name):
            # If mirrored pose exists already
            return mirrored_pose
        pose_item = self.get_pose_item_by_pose_name(pose.name)
        full_path = pose_item.full_path()
        split_path = full_path.split('|')
        length = len(split_path)
        for idx, part in enumerate(split_path[::-1]):
            if part in Symmetry.suffix:
                if part == 'L':
                    mirrored_part = 'R'
                elif part == 'R':
                    mirrored_part = 'L'
                else:
                    mirrored_part = part
                split_path[length - 1 - idx] = mirrored_part
                break

        split_path[-1] = mirrored_pose.name

        current_item = self.root_item
        for part_name in split_path[:-1]:
            need_to_add_grp = True
            for child in current_item.children:
                if child.name == part_name:
                    current_item = child
                    need_to_add_grp = False
                    break
            if need_to_add_grp:
                group_item = GroupItem(part_name)
                parent_index = self.index_of(current_item)
                self.insertRow(group_item, 0, parent_index)
                current_item = group_item
        num_children = len(current_item.children)
        self.insert_pose(mirrored_pose, current_item, num_children)
        self.sync_pose_tree()
        return mirrored_pose

    @staticmethod
    def __delete_pose(item):
        """
        Delete pose data from a pose item. This action will reset pose,
        remove pose attributes and delete it from pose cache list in the
        controller
        Args:
            item(PoseItem):

        """
        pose = item.pose
        pose.reset(remove_influence=True)
        if pose.is_corrective:
            pose.delete_corrective()
        pose.remove_pose_attribute()

    def split_pose(self, item, fall_off=0.7, drivers=None, influence=True, target=True):
        """
        This method will populate new pose for split action and assign split data to new poses
        Args:
            item(PoseItem): The pose target
            fall_off(float): The fall off value when calculate weight map
            drivers(list): A list of driver objects
            influence(bool): If split influence data
            target(bool): If split target data

        """
        poses = self.controller.split_pose(
            item.pose,
            fall_off=fall_off,
            drivers=drivers,
            influence=influence,
            target=target)

        parent = item.parent
        row = item.row
        for pose in poses:
            self.insert_pose(pose, parent, row)
            row = row + 1
        self.sync_pose_tree()
        return poses

    def get_index_by_pose_name(self, pose_name):
        """
        Get the index from a pose name
        Args:
            pose_name(str): Pose name

        Returns:
            QModelIndex:
        """
        root = self.root_item
        index, _ = self.__recursive_find_pose(root, pose_name)
        return index

    def get_pose_item_by_pose_name(self, pose_name):
        """
        Get the pose item by a given pose name
        Args:
            pose_name(str): Pose name

        Returns:
            PoseItem: Get the pose item from a pose name
        """
        root = self.root_item
        _, item = self.__recursive_find_pose(root, pose_name)
        return item

    def __recursive_find_pose(self, parent_item, pose_name):
        for child in parent_item.children:
            if child.type_str == 'pose':
                if child.name == pose_name:
                    return self.index_of(child), child
            elif child.type_str == 'group':
                index, item = self.__recursive_find_pose(child, pose_name)
                if item:
                    return index, item
        return None, None

    def set_pose_weight(self, pose_name, weight):
        index = self.get_index_by_pose_name(pose_name)
        if index:
            row = index.row()
            index = index.sibling(row, self.Weight_Index)
            self.setData(index, weight)

    def update_pose_weight(self, pose_item, value):
        """
        Update a known pose property
        Args:
            pose_item(Pose):
            value(float)

        Returns:

        """
        index = None
        pose = None
        if isinstance(pose_item, Pose):
            index = self.get_index_by_pose_name(pose_item.name)
            pose = pose_item
        elif isinstance(pose_item, six.string_types):
            index = self.get_index_by_pose_name(pose_item)
            if index.isValid():
                pose_item = self.item_from_index(index)
                pose = pose_item.pose

        elif isinstance(pose_item, PoseItem):
            index = self.index_of(pose_item)
            pose = pose_item.pose
        if index is None or pose is None:
            return
        row = index.row()
        weight_index = index.sibling(row, PoseTreeModel.Weight_Index)
        self.setData(weight_index, value)

    def get_corrective_group(self):
        """
        Get the group item called CORRECTIVE under the root. If not exists, create it.
        Returns:
            item(GroupItem)
        """
        for child in self.root_item.children:
            if child.type_str == 'group' and child.name == 'CORRECTIVE':
                return child
        idx = self.create_group(
            'CORRECTIVE',
            parent=self.root_item,
            after_row=self.root_item.child_count())
        return self.item_from_index(idx)

    def sync_pose_tree(self):
        """
        Sync the pose tree information between the controller and model

        """
        pose_tree = self.root_item.export()
        self.controller.pose_tree = pose_tree
        return pose_tree

    def refresh_pose(self, pose):
        """
        Refresh the influence number and target number for model item associated with the given pose.
        Args:
            pose(Pose):

        Returns:

        """
        index = self.get_index_by_pose_name(pose.name)
        pose_item = self.item_from_index(index)

        pose_item.init_from_pose(pose)
        row = index.row()
        num_influence_index = index.sibling(row, PoseTreeModel.Influences_Index)
        self.setData(num_influence_index, pose_item.influence_number)
        num_target_index = index.sibling(row, PoseTreeModel.Targets_Index)
        self.setData(num_target_index, pose_item.target_number)

    def export_data(self,
                    file_path=None,
                    root=None,
                    progress_lambda=None,
                    compress=False):
        """
        This method will export data from selected item. The model will add pose tree information
        on top of data exported from pose controller
        Args:
            file_path:
            root:
            progress_lambda:
            compress:

        Returns:
            dict:

        """
        if root is None:
            root = self.root_item
        self.sync_pose_tree()
        pose_tree = root.export()
        pose_leaves = root.find_leaves()
        pose_list = [i.pose for i in pose_leaves]

        data = self.controller.export_data(
            file_path=None,
            pose_list=pose_list,
            progress_lambda=progress_lambda,
            compress=compress)

        data['UI'] = {'parent_path': root.parent_full_path(),
                      'pose_tree': pose_tree}
        if file_path:
            data_str = json.dumps(data,
                                  sort_keys=True,
                                  indent=4,
                                  separators=(',', ': '))
            if compress:
                gzip_export(data_str, file_path)
            else:
                with open(file_path, 'w') as out_file:
                    out_file.write(data_str)
        return data

    def load_data(self, file_path, progress_lambda=None):
        """
        Load data from a file to  current controller
        Args:
            file_path:
            progress_lambda:

        Returns:

        """
        self.reset_weights()
        if not self.controller:
            QtWidgets.QMessageBox.critical(self,
                                           "No Pose Controller",
                                           "Failed to find valid pose controller. "
                                           "Please check there's is pose controller node "
                                           "in the scene and it's controller type set to `PoseController`")
            return
        self.controller.load_data(file_path, progress_lambda)
        self.refresh_pose_tree(self.controller.pose_tree)
        self.sync_pose_tree()

    def import_data_to_item(self, file_path, item):
        index = self.index_of(item)
        if not index.isValid():
            return

        with open(file_path, 'r') as input_file:
            data_str = input_file.read()
            data = json.loads(data_str)
        if isinstance(data, list):
            data = data[0]
        pose_collect_data = data['pose']
        for _, data in pose_collect_data.items():
            pose = item.pose
            pose.reset(remove_influence=True)
            influence_data = data.get('influence')
            if influence_data:
                pose.set_neutral_pose(influence_data)
            pose.set_data(data, skip_driver=True)
            break

    def merge_data(self, file_path, progress_lambda=None):
        with open(file_path, 'r') as input_file:
            data_str = input_file.read()
            data = json.loads(data_str)
        if isinstance(data, list):
            data = data[0]
        ui_info = data.get('UI', {})
        parent_path = ui_info.get('parent_path', "")
        data_pose_tree = ui_info.get('pose_tree', {})
        if data_pose_tree.get('name'):
            # This is not from root
            data_pose_tree = [data_pose_tree]
        else:
            data_pose_tree = data_pose_tree.get('children', [])

        self.reset_weights()
        root = self.find_item_from_full_path(parent_path)
        if not root:
            root = self.root_item
        pose_list = get_pose_list_from_pose_tree_recurse(data_pose_tree)
        new_pose_created = list()
        if self.controller:
            new_pose_created = self.controller.merge_data(
                data=data,
                pose_list=pose_list,
                progress_lambda=progress_lambda)

        if data_pose_tree:
            self.populate_item_recurse(
                root,
                data_pose_tree,
                merge=True,
                filter_list=new_pose_created)

        self.sync_pose_tree()

    def update_target_status(self):
        """
        Update the target status indicator in this model
        Returns:

        """
        if not self.controller:
            self.__target_is_enabled = True
        else:
            self.__target_is_enabled = self.controller.target_is_enabled()
        root_index = QtCore.QModelIndex()
        self.refresh_column(root_index, PoseTreeModel.Targets_Index)

    def refresh_column(self, parent_index, column):
        """
        Recursively update all the index at a specific column
        Args:
            parent_index(ModelIndex):
            column(int): A column number

        """
        count = self.rowCount(parent_index)
        if count:
            tp_idx = self.index(0, column, parent_index)
            bt_idx = self.index(count, column, parent_index)
            self.dataChanged.emit(tp_idx, bt_idx)

            for i in range(count):
                child = self.index(i, column, parent_index)
                self.refresh_column(child, column)


def get_pose_list_from_pose_tree_recurse(pose_trees):
    """
    List all the leaf pose items from the tree dictionary
    Args:
        pose_trees(dict):

    Returns:
        list: Pose names in list

    """
    poses = []
    for pose_tree in pose_trees:
        item_type = pose_tree.get('type')
        name = pose_tree.get('name')
        if item_type == 'group':
            children = pose_tree.get('children')
            poses.extend(get_pose_list_from_pose_tree_recurse(children))
        elif item_type == 'pose':
            if name:
                poses.append(name)
        else:
            continue
    return poses
