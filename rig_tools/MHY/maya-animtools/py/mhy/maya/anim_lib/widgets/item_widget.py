"""
This module is for creating a table view for animation clips and poses.

"""
import math
import os
import shutil
import json
import logging

from PySide2 import QtCore, QtGui, QtWidgets

# Studio package module imports
from mhy.maya.anim_lib.utils import open_path
import mhy.maya.anim_lib.delegate.pose_item_delegate as pid
from mhy.maya.anim_lib.signal_manager import SignalManager
from mhy.qt.icon_lib.api import get_icon
from mhy.maya.anim_lib.utils import get_unique_pose_name
from mhy.maya.anim_lib.widgets.pose_edit_dialog import PoseEditDialog
from mhy.maya.anim_lib.utils import open_source_file

logger = logging.getLogger(__name__)

icon_size = 250


class Item(object):
    def __new__(cls, data, path):
        is_static = data.get('static', False)
        if is_static:
            return super(Item, cls).__new__(PoseItem)
        else:
            return super(Item, cls).__new__(AnimItem)

    def __init__(self, data, path):
        self.path = path
        self.name = data.get('name', "")
        self.user_created = data.get('user_created', "")
        self.date_created = data.get('date_created', "")
        self.comment = data.get('comment', "")
        self.num_nodes = data.get('num_nodes', 0)
        self.name_spaces = data.get('name_spaces', [])
        self.thumbnails = self.get_thumbnails_from_path()
        self.source_file = data.get('source_file', "")

    def get_thumb_nail_dir(self):
        dir_name = os.path.dirname(self.path)
        base_name = os.path.splitext(os.path.basename(self.path))[0]
        footage_path = os.path.join(dir_name, base_name + '_footage')
        if os.path.isdir(footage_path):
            return footage_path

    def get_thumbnails_from_path(self):
        footage_path = self.get_thumb_nail_dir()
        images = []
        if footage_path:
            for f in os.listdir(footage_path):
                full_path = os.path.join(footage_path, f)
                pix_map = QtGui.QPixmap(full_path)
                scaled_map = pix_map.scaled(QtCore.QSize(icon_size, icon_size))
                images.append(scaled_map)
        return images

    def destruct(self):
        """
        Delete all the data related to this item from the disk

        """
        thumb_nail_path = self.get_thumb_nail_dir()
        if thumb_nail_path and os.path.isdir(thumb_nail_path):
            shutil.rmtree(thumb_nail_path)
        if os.path.isfile(self.path):
            os.remove(self.path)

    def open_source_file(self):
        if not os.path.isfile(self.source_file):
            logger.warning("{} is not a valid file. Failed to open".format(self.source_file))
        open_source_file(self.source_file)


class PoseItem(Item):
    is_static = True


class AnimItem(Item):
    is_static = False

    def __init__(self, data, path):
        super(AnimItem, self).__init__(data, path)
        self.start_frame = data.get('start_frame')
        self.end_frame = data.get('end_frame')


class IconTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(IconTableView, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.horizontalHeader().setDefaultSectionSize(icon_size)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(icon_size)
        self._items = []

    def __del__(self):
        del self._items[:]


class AnimItemsWidget(QtWidgets.QScrollArea):

    def __init__(self, parent=None):
        super(AnimItemsWidget, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)

        self.view = IconTableView(self)
        self.model = ItemTableModel(self)
        self.view.setModel(self.model)
        delegate = pid.PoseItemDelegate()
        self.view.setItemDelegate(delegate)

        layout.addWidget(self.view)
        self.setWidget(widget)
        sel_model = self.view.selectionModel()
        sel_model.selectionChanged.connect(self.sel_changed_cb)
        self.view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu_cb)

    def select_poses(self, poses):
        sel_model = self.view.selectionModel()
        for pose in poses:
            idx = self.model.get_index_from_pose_name(pose)
            sel_model.select(idx, QtCore.QItemSelectionModel.Select)

    def populate_items(self, icon_containers):
        self.model.populate_items(icon_containers)

    def sel_changed_cb(self, sel, desel):
        sel_mod = self.view.selectionModel()
        selected = sel_mod.selectedIndexes()
        sel_items = []
        for idx in selected:
            item = idx.data(QtCore.Qt.UserRole)
            sel_items.append(item)
        SignalManager.item_sel_changed.emit(sel_items)

    def show_context_menu_cb(self, pos):
        menu = QtWidgets.QMenu()
        icon = get_icon(sub_dir='/IOS/general/png/64/refresh.png', color=[160, 255, 187])

        refresh_action = QtWidgets.QAction(icon, 'Refresh', self)
        # refresh_action.triggered.connect(self.parent().refresh_items)
        del_action = QtWidgets.QAction("Delete", self)
        del_action.triggered.connect(self.del_pose_cb)

        rename_action = QtWidgets.QAction('Rename', self)
        rename_action.triggered.connect(self.rename_pose_cb)

        edit_action = QtWidgets.QAction('Edit', self)
        edit_action.triggered.connect(self.edit_pose_cb)

        open_source_file_action = QtWidgets.QAction('Open Source File', self)
        open_source_file_action .triggered.connect(self.open_source_file_cb)

        show_action = QtWidgets.QAction('Show In Explorer', self)
        show_action.triggered.connect(self.show_in_explorer_cb)

        menu.addAction(refresh_action)
        menu.addAction(rename_action)
        menu.addAction(del_action)
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(open_source_file_action)
        menu.addAction(show_action)
        menu.exec_(self.view.mapToGlobal(pos))

    def get_selected_item(self):
        sel_mod = self.view.selectionModel()
        selected = sel_mod.selectedIndexes()
        if selected:
            item = selected[0].data(QtCore.Qt.UserRole)
            return item

    def open_source_file_cb(self):
        item = self.get_selected_item()
        if not item:
            return
        item.open_source_file()

    def show_in_explorer_cb(self):

        item = self.get_selected_item()
        if item:
            path = item.path
            open_path(path)

    def rename_pose_cb(self):
        sel_mod = self.view.selectionModel()
        selected = sel_mod.selectedIndexes()
        if selected:
            item = selected[0].data(QtCore.Qt.UserRole)

            text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Dialog', 'Enter new name:')
            if not ok:
                return
            if text == item.name:
                return
            current_path = item.path
            dir_name = os.path.dirname(current_path)
            pose_name = get_unique_pose_name(dir_name, text)
            full_path = os.path.join(dir_name, item.name + '.apd')
            if os.path.isfile(full_path):
                with open(full_path, 'r') as f:
                    data = json.load(f)
                data['name'] = pose_name
                json_str = json.dumps(data)
                with open(full_path, 'w') as f:
                    f.write(json_str)

            new_path = os.path.join(dir_name, pose_name + '.apd')
            os.rename(full_path, new_path)

            thumb_nail_dir = os.path.join(dir_name, item.name + '_footage')
            if os.path.isdir(thumb_nail_dir):
                new_thumb_dir = os.path.join(dir_name, pose_name + '_footage')
                os.rename(thumb_nail_dir, new_thumb_dir)
            SignalManager.pose_files_changed.emit([dir_name])

    def del_pose_cb(self):
        result = QtWidgets.QMessageBox.question(self, "Delete", "Deletion is non-revertible. Are you sure?")
        if result != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        sel_mod = self.view.selectionModel()
        selected = sel_mod.selectedIndexes()
        updated_dirs = []
        for idx in selected:
            item = idx.data(QtCore.Qt.UserRole)
            dir_path = os.path.dirname(item.path)
            updated_dirs.append(dir_path)
            item.destruct()
        updated_dirs = list(set(updated_dirs))
        SignalManager.pose_files_changed.emit(updated_dirs)

    def edit_pose_cb(self):
        item = self.get_selected_item()
        if item:
            ui = PoseEditDialog(pose_item=item, parent=self)
            ui.show()


class ItemTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(ItemTableModel, self).__init__(parent=parent)
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
        self.__items = items
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
        item = self.__items[idx]
        if role == QtCore.Qt.DisplayRole:
            return item.name
        if role == QtCore.Qt.DecorationRole:
            if item.thumbnails:
                return item.thumbnails[0]
        if role == QtCore.Qt.ForegroundRole:
            if item.is_static:
                return QtGui.QColor(0, 255, 0)
            else:
                return QtGui.QColor(255, 0, 0)
        if role == QtCore.Qt.ToolTipRole:
            return item.path

        if role == QtCore.Qt.UserRole:
            return item

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
        return 3

    def clear(self):
        """
        Clear the rows and attribute columns

        """
        self.removeRows(0, self.rowCount())

    def flags(self, index):
        column = index.column()
        row = index.row()
        real_index = column + self.columnCount()*row
        if real_index >= self.num_items:
            return QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def get_index_from_pose_name(self, pose_name):
        for idx, item in enumerate(self.__items):
            if item.name == pose_name:
                row = idx/self.columnCount()
                column = idx % self.columnCount()
                return self.index(row, column, QtCore.QModelIndex())

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        self.__items = []
        self.endRemoveRows()
        return True

    def add_icon(self, icon_container):
        item = Item(icon_container)
        self.items.append(item)
        if len(self.items) > self.rowCount():
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount()+1)
            self.endInsertRows()


class ItemWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ItemWidget, self).__init__(parent=parent)
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setFixedWidth(805)
        self.item_widget = AnimItemsWidget(self)
        main_layout.addWidget(self.item_widget)
        SignalManager.refresh_active_items.connect(self.populate_poses)

    def populate_poses(self, paths):
        items = list()
        for p in paths:
            if not os.path.isfile(p):
                logger.warning("{} is not a valid pose file".format(p))
                continue
            with open(p, 'r') as f:
                data = json.load(f)
                try:
                    item = Item(data=data, path=p)
                    items.append(item)
                except Exception:
                    continue
        self.populate_items(items)

    def _populate_from_path(self, path):
        items = list()
        for p in os.listdir(path):
            if p.endswith('.apd'):
                full_path = os.path.join(path, p)
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    try:
                        item = Item(data=data, path=full_path)
                        items.append(item)
                    except Exception:
                        continue
        self.populate_items(items)

    def populate_items(self, items):
        self.item_widget.populate_items(items)


