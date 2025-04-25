import logging
import collections
from mhy.maya.anim_lib.utils import list_leaves, open_path, move_pose_file, delete_pose_and_footage

import os
import six
import shutil
from PySide2 import QtCore, QtWidgets
from mhy.maya.anim_lib.file_browser.file_item import SidebarWidgetItem
import mhy.maya.anim_lib.manager as manager
from mhy.maya.anim_lib.signal_manager import SignalManager

from mhy.maya.anim_lib.widgets.line_edit import LineEdit
from mhy.maya.anim_lib.utils import norm_path, norm_paths

logger = logging.getLogger(__name__)

DEFAULT_SEPARATOR = "/"


class Package(object):
    def __init__(self, root=None):
        self.__root = None
        self.folders = list()
        self.data_files = list()

        self.set_path_root(root)

    def set_path_root(self, path_root):
        self.folders = [path_root]
        self.data_files = list()
        self.__root = path_root
        if path_root:
            dirs, files = list_leaves(path_root)

            self.folders.extend(dirs)
            self.data_files.extend(files)

    def export_data(self):
        data = dict()
        for i in (self.folders + self.data_files):
            data[i] = {}
        return data


class Library(object):
    def __init__(self):
        self.data = dict()

    def add_root(self, root_path):
        self.data[root_path] = Package(root_path)

    def export_data(self):
        data = dict()
        for root, data in self.data.items():
            data[root] = data.export_data()

        return data

    def refresh_path(self, dir_path):
        """
        Refresh the content under a given directory path
        Args:
            dir_path(str):

        """
        dirs, files = list_leaves(dir_path)
        dir_path = norm_path(dir_path)

        for root, pack in self.data.items():
            root = norm_path(root)
            if not dir_path.startswith(root):
                continue

            pack.folders = [i for i in pack.folders if not i.startswith(dir_path)]
            pack.data_files = [i for i in pack.data_files if not i.startswith(dir_path)]
            pack.folders.extend(dirs)
            pack.data_files.extend(files)
            pack.folders.sort()
            pack.data_files.sort()

    def list_pose_files(self):
        """
        List all pose files in all the package instances
        Returns:
            list: Iterate all the pack and list all the pose data files
        """
        files = []
        for root, pack in self.data.items():
            files.extend(pack.data_files)

        files = list(set(files))
        return files


def paths_to_dict(paths, root="", separator=None):
    """

    Return the given paths as a nested dict.

    Example:
        paths = ["/fruit/apple", "/fruit/orange"]
        print pathsToDict(paths)
        # Result: {"fruit" : {"apple":{}}, {"orange":{}}}

    Args:
        paths:
        root:
        separator:

    Returns:

    """
    separator = separator or DEFAULT_SEPARATOR
    results = collections.OrderedDict()
    paths = norm_paths(paths)

    for path in paths:
        p = results

        # This is to add support for grouping by the given root path.
        if root and root in path:
            path = path.replace(root, "")
            p = p.setdefault(root, collections.OrderedDict())

        keys = path.split(separator)[0:]

        for key in keys:
            if key:
                p = p.setdefault(key, collections.OrderedDict())
    return results


def find_root(paths, separator=None):
    """
    Find the common path for the given paths.

    Example:
        paths = [
            '/fruit/apple',
            '/fruit/orange',
            '/fruit/banana'
        ]
        print(findRoot(paths))
        # '/fruit'

    Args:
        paths:
        separator:

    Returns:

    """

    if paths:
        path = list(paths)[0]  # Only need one from the list to verify the common path.
    else:
        path = ""

    result = None
    separator = separator or DEFAULT_SEPARATOR

    tokens = path.split(separator)

    for i, token in enumerate(tokens):
        root = separator.join(tokens[:i + 1])
        match = True

        for path in paths:
            if not path.startswith(root + separator):
                match = False
                break

        if not match:
            break

        result = root

    return result


class FileTreeWidget(QtWidgets.QWidget):
    itemDropped = QtCore.Signal(object)
    itemRenamed = QtCore.Signal(str, str)
    itemSelectionChanged = QtCore.Signal()
    settingsMenuRequested = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(FileTreeWidget, self).__init__(parent=parent)
        self.filter_line = None
        self._previousFilterText = ""

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)
        self.setMinimumWidth(230)

        self._treeWidget = TreeWidget(self)

        self._treeWidget.itemSelectionChanged.connect(self._item_selection_changed)

        self._titleWidget = self.create_title_widget()

        layout.addWidget(self._titleWidget)
        layout.addWidget(self._treeWidget)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu_cb)

        self._treeWidget.installEventFilter(self)
        SignalManager.pose_files_changed.connect(self._treeWidget.search)

    def show_context_menu_cb(self, pos):
        selected = self.selectedPaths()
        if not selected:
            return
        menu = QtWidgets.QMenu()
        if os.path.isdir(selected[0]):
            create_folder_action = QtWidgets.QAction('Create Folder', self)
            create_folder_action.triggered.connect(self.create_folder_cb)
            menu.addAction(create_folder_action)

        del_action = QtWidgets.QAction('Delete', self)
        del_action.triggered.connect(self.delete_cb)
        menu.addAction(del_action)
        menu.addSeparator()

        show_action = QtWidgets.QAction('Show In Explorer', self)
        show_action.triggered.connect(self.show_in_explorer_cb)
        menu.addAction(show_action)
        menu.exec_(self.mapToGlobal(pos))

    def delete_cb(self):
        sel = self.selectedPath()
        result = QtWidgets.QMessageBox.question(self, "Delete", "Deletion is non-revertible. Are you sure?")
        if result != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        base_dir = os.path.dirname(sel)
        if os.path.isfile(sel):
            delete_pose_and_footage(sel)
        elif os.path.isdir(sel):
            shutil.rmtree(sel)

        self.update_paths([base_dir])

    def create_folder_cb(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Create Folder Dialog', 'Enter folder name:')
        if not ok:
            return
        sel = self.selectedPath()
        folder_path = os.path.join(sel, text)
        try:
            os.mkdir(folder_path)
        except BaseException as e:
            logger.error(str(e))

        self.update_paths([sel])

    def show_in_explorer_cb(self):
        selected = self.selectedPaths()
        if selected:
            open_path(selected[0])

    def _item_selection_changed(self, *args):
        self.itemSelectionChanged.emit()

    def eventFilter(self, obj, event):
        """Using an event filter to show the search widget on key press."""
        if event.type() == QtCore.QEvent.KeyPress:
            self._key_press_event(event)

        return super(FileTreeWidget, self).eventFilter(obj, event)

    def _key_press_event(self, event):
        """
        Triggered from the tree widget key press event.

        :type event: QKeyEvent
        """
        text = event.text().strip()

        if not text.isalpha() and not text.isdigit():
            return

        if text and not self._titleWidget.ui.filterEdit.hasFocus():
            self._titleWidget.ui.filterEdit.setText(text)

        self.set_filter_visible(True)

        self._previousFilterText = text

    def _filter_visible_trigger(self, visible):
        """
        Triggered by the filter visible action.

        :type visible: bool
        """
        self.set_filter_visible(visible)
        self._titleWidget.ui.filterEdit.selectAll()

    def create_title_widget(self):
        """
        Create a new instance of the title bar widget.

        :rtype: QtWidgets.QFrame
        """

        class UI(object):
            """Proxy class for attaching ui widgets as properties."""
            pass

        title_widget = QtWidgets.QFrame(self)
        title_widget.setObjectName("titleWidget")
        title_widget.ui = UI()

        h_layout = QtWidgets.QHBoxLayout(self)
        h_layout.setSpacing(0)
        h_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_line = LineEdit(self)
        self.filter_line.hide()
        self.filter_line.setObjectName("filterEdit")
        self.filter_line.setText(self.treeWidget().filterText())
        self.filter_line.textChanged.connect(self.search_changed)
        title_widget.ui.filterEdit = self.filter_line

        h_layout.addWidget(self.filter_line)
        title_widget.setLayout(h_layout)

        return title_widget

    def set_library(self, lib):
        self.treeWidget().set_library(lib)

    def search_changed(self, text):
        """
        Triggered when the search filter has changed.

        :type text: str
        """
        self.refreshFilter()
        if text:
            self.set_filter_visible(True)
        else:
            self.treeWidget().setFocus()
            self.set_filter_visible(False)

    def set_filter_visible(self, visible):
        """
        Set the filter widget visible

        Args:
            visible:

        Returns:

        """
        self._titleWidget.ui.filterEdit.setVisible(visible)
        self._titleWidget.ui.filterEdit.setFocus()

        if not visible and bool(self.treeWidget().filterText()):
            self.treeWidget().setFilterText("")
        else:
            self.refreshFilter()

    def set_settings(self, settings):
        """
        Set the settings for the widget.

        :type settings: dict
        """
        self.treeWidget().set_settings(settings)

        value = settings.get("filterText")
        if value is not None:
            self.set_filter_text(value)

    def settings(self):
        """
        Get the settings for the widget.

        :rtype: dict
        """
        settings = self.treeWidget().settings()

        settings["filterText"] = self.filter_text()

        return settings

    # --------------------------------
    # convenience methods
    # --------------------------------

    def filter_text(self):
        return self.treeWidget().filterText()

    def set_filter_text(self, text):
        self._titleWidget.ui.filterEdit.setText(text)

    def refreshFilter(self):
        self.treeWidget().setFilterText(self._titleWidget.ui.filterEdit.text())

    def isFilterVisible(self):
        return bool(self.treeWidget().filterText()) or self._titleWidget.ui.filterEdit.isVisible()

    def setIconsVisible(self, visible):
        self.treeWidget().setIconsVisible(visible)

    def icons_visible(self):
        return self.treeWidget().icons_visible()

    def setRootVisible(self, visible):
        self.treeWidget().setRootVisible(visible)

    def isRootVisible(self):
        return self.treeWidget().isRootVisible()

    def treeWidget(self):
        return self._treeWidget

    def setDpi(self, dpi):
        self.treeWidget().setDpi(dpi)

    def setRecursive(self, enabled):
        self.treeWidget().setRecursive(enabled)

    def isRecursive(self):
        return self.treeWidget().isRecursive()

    def setItemData(self, id, data):
        self.treeWidget().setPathSettings(id, data)

    def selectedPath(self):
        return self.treeWidget().selectedPath()

    def selectPaths(self, paths):
        self.treeWidget().selectPaths(paths)

    def selectedPaths(self):
        return self.treeWidget().selected_paths()

    def clearSelection(self):
        self.treeWidget().clearSelection()

    def update_paths(self, paths):
        self.treeWidget().update_paths(paths)


class TreeWidget(QtWidgets.QTreeWidget):
    itemDropped = QtCore.Signal(object)
    itemRenamed = QtCore.Signal(str, str)
    itemSelectionChanged = QtCore.Signal()
    Mimedata_Type = "application/x-move-anim-file.list"

    def __init__(self, *args, **kwargs):
        super(TreeWidget, self).__init__(*args, **kwargs)
        self.library = None
        self._dpi = 1
        self._data = []
        self._items = []
        self._index = {}
        self._locked = False
        self._recursive = True
        self._filterText = ""
        self._iconsVisible = True

        self._options = {
            'field': 'path',
            'separator': '/',
            'recursive': True,
            'autoRootPath': True,
            'rootText': 'FOLDERS',
            'sortBy': None,
            'queries': [{'filters': [('type', 'is', 'Folder')]}]
        }

        self.setDpi(1)

        self.setHeaderHidden(True)

        # self.setDragDropMode(self.InternalMove)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)

        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setSelectionMode(QtWidgets.QTreeWidget.SingleSelection)
        SignalManager.pose_files_changed.connect(self.update_paths)

    def filterText(self):
        """
        Get the current filter text.

        :rtype: bool
        """
        return self._filterText

    def setFilterText(self, text):
        """
        Triggered when the search filter has changed.

        :type text: str
        """
        self._filterText = text.strip()
        self.refreshFilter()

    def refreshFilter(self):
        """Refresh the current item filter."""
        items = self.items()

        for item in items:
            if self._filterText.lower() in item.text(0).lower():
                item.setHidden(False)
                for parent in item.parents():
                    parent.setHidden(False)
            else:
                item.setHidden(True)

    def clear(self):
        """Clear all the items from the tree widget."""
        self._items = []
        self._index = {}
        super(TreeWidget, self).clear()

    def selectionChanged(self, *args):
        """Triggered the current selection has changed."""
        self.search()

    def setRecursive(self, enable):
        """
        Set the search query on the dataset to be recursive.

        :type enable: bool
        """
        self._recursive = enable
        self.search()

    def isRecursive(self):
        """
        Get the recursive query enable state.

        :rtype: bool
        """
        return self._recursive

    def sortBy(self):
        """
        Get the sortby field.

        :rtype: str
        """
        return self._options.get('sortBy', [self.field()])

    def field(self):
        """
        Get the field.

        :rtype: str
        """
        return self._options.get('field', '')

    def rootText(self):
        """
        Get the root text.

        :rtype: str
        """
        return self._options.get('rootText')

    def separator(self):
        """
        Get the separator used in the fields to separate level values.

        :rtype: str
        """
        return self._options.get('separator', DEFAULT_SEPARATOR)

    def isLocked(self):
        """
        Return True if the items are in read only mode

        :rtype: bool
        """
        return self._locked

    def itemAt(self, pos):
        """
        :type pos: QtGui.QPoint
        :rtype: None or Folder
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        item = self.itemFromIndex(index)
        return item

    def dropEvent(self, event):
        """
        Override drop event to move pose files to another group
        Args:
            event:

        Returns:

        """
        sel = self.selectedItem()
        if not sel:
            return

        dst = self.itemAt(event.pos())
        src_path = sel.path()
        dst_path = dst.path()
        if not os.path.isfile(src_path):
            return
        if not os.path.isdir(dst_path):
            return
        dst_pose_file = move_pose_file(sel.path(), dst.path())
        origin_dir = os.path.dirname(src_path)
        self.update_paths([origin_dir, dst_path])

        if dst_pose_file:
            self.selectPaths([dst_pose_file])

        self.itemDropped.emit(event)

    def selectItem(self, item):
        """
        :type item: NavigationWidgetItem
        :rtype: None
        """
        self.selectPaths([item.path()])

    def dpi(self):
        """
        Return the dots per inch multiplier.

        :rtype: float
        """
        return self._dpi

    def setDpi(self, dpi):
        """
        Set the dots per inch multiplier.

        :type dpi: float
        :rtype: None
        """
        self._dpi = dpi

        width = 20 * dpi
        height = 18 * dpi

        self.setIndentation(9 * dpi)
        self.setMinimumWidth(20 * dpi)
        self.setIconSize(QtCore.QSize(width, height))
        self.setStyleSheet("height: {height}px;".format(height=height))

    def update(self, *args):
        """
        :rtype: None
        """
        for item in self.items():
            item.update()

    def items(self):
        """
        Return a list of all the items in the tree widget.

        :rtype: list[NavigationWidgetItem]
        """
        items = self.findItems(
            "*",
            QtCore.Qt.MatchWildcard | QtCore.Qt.MatchRecursive
        )

        return items

    def itemFromPath(self, path):
        """
        Return the item for the given path.

        :type path: str
        :rtype: NavigationWidgetItem
        """
        return self._index.get(path)

    def settings(self):
        """
        Return a dictionary of the settings for this widget.

        :rtype: dict
        """
        settings = {}

        scroll_bar = self.verticalScrollBar()
        settings["verticalScrollBar"] = {
            "value": scroll_bar.value()
        }

        scroll_bar = self.horizontalScrollBar()
        settings["horizontalScrollBar"] = {
            "value": scroll_bar.value()
        }

        for item in self.items():
            item_settings = item.settings()
            if item_settings:
                settings[item.path()] = item.settings()

        return settings

    def set_settings(self, settings):
        """
        Set the settings for this widget

        :type settings: dict
        """
        for path in sorted(settings.keys()):
            s = settings.get(path, None)
            self.setPathSettings(path, s)

        scroll_bar_settings = settings.get("verticalScrollBar", {})
        value = scroll_bar_settings.get("value")
        if value:
            self.verticalScrollBar().setValue(value)

        scroll_bar_settings = settings.get("horizontalScrollBar", {})
        value = scroll_bar_settings.get("value")
        if value:
            self.horizontalScrollBar().setValue(value)

        self.setDpi(self.dpi())

    def setPathSettings(self, path, settings):
        """
        Show the context menu at the given position.

        :type path: str
        :type settings: dict
        :rtype: None
        """
        item = self.itemFromPath(path)
        if item and settings:
            item.set_settings(settings)

    def showContextMenu(self, position):
        """
        Show the context menu at the given position.

        :type position: QtCore.QPoint
        :rtype: None
        """
        menu = self.createContextMenu()
        menu.exec_(self.viewport().mapToGlobal(position))

    def expandedItems(self):
        """
        Return all the expanded items.

        :rtype:  list[NavigationWidgetItem]
        """
        for item in self.items():
            if self.isItemExpanded(item):
                yield item

    def expandedPaths(self):
        """
        Return all the expanded paths.

        :rtype:  list[NavigationWidgetItem]
        """
        for item in self.expandedItems():
            yield item.url()

    def setExpandedPaths(self, paths):
        """
        Set the given paths to expanded.

        :type paths: list[str]
        """
        for item in self.items():
            if item.url() in paths:
                item.setExpanded(True)

    def selectedItem(self):
        """
        Return the last selected item

        :rtype: SidebarWidgetItem
        """
        path = self.selectedPath()
        return self.itemFromPath(path)

    def selectedPath(self):
        """
        Return the last selected path

        :rtype: str or None
        """
        paths = self.selected_paths()
        if paths:
            return paths[-1]

    def selected_paths(self):
        """
        Get the paths that are selected.

        Returns:
            list:
        """
        paths = []
        items = self.selectedItems()
        for item in items:
            path = item.path()
            paths.append(path)
        return norm_paths(paths)

    def selectPath(self, path):
        """
        Select the given path

        :type: str
        :rtype: None
        """
        self.selectPaths([path])

    def selectPaths(self, paths):
        """
        Select the items with the given paths.

        :type paths: list[str]
        :rtype: None
        """
        paths = norm_paths(paths)
        items = self.items()
        for item in items:
            if norm_path(item.path()) in paths:
                item.setSelected(True)
            else:
                item.setSelected(False)

    def refresh_data(self):
        self.set_library(self.library)

    def set_library(self, lib, split=None):
        self.library = lib

        settings = self.settings()

        self.blockSignals(True)

        self.clear()
        if self.library:
            for root, pak in self.library.data.items():
                data = pak.export_data()
                self.add_paths(data, root=root, split=split)

            self.set_settings(settings)

        self.blockSignals(False)

        self.search()

    def search(self, *args, **kwargs):
        """
        Run the pose file search from the selected path
        Args:
            *args:
            **kwargs:

        Returns:

        """
        if not self.library:
            return
        selected = self.selected_paths()
        if selected:
            selection = selected[0]
            if os.path.isfile(selection):
                selection = os.path.dirname(selection)
            manager.current_path = selection
        else:
            manager.current_path = None
        valid_poses = []
        for i in self.library.list_pose_files():
            for sel in selected:
                if i.startswith(sel):
                    valid_poses.append(i)
                    break
        SignalManager.refresh_active_items.emit(valid_poses)

    def add_paths(self, paths, root="", split=None):
        """
        Set the given items as a flat list.

        Args:
            paths:
            root:
            split:

        Returns:

        """

        data = paths_to_dict(paths, root=root, separator=split)
        self.create_items(data, root_path=root, split=split)

        if isinstance(paths, dict):
            self.set_settings(paths)

    def create_items(self, data, root_path=None, split=None):
        """
        Create the items from the given data dict

        :type data: dict
        :type split: str or None

        :rtype: None
        """
        split = split or DEFAULT_SEPARATOR
        root_path = norm_path(root_path)
        self._index = {}
        for key in data:
            root = split.join([key])
            item = None
            if not root_path or not root_path.startswith(root):
                text = key.split(split)
                if text:
                    text = text[-1]
                else:
                    text = key

                item = SidebarWidgetItem(self)
                item.setText(0, six.text_type(text))
                item.set_path(root)
                item.setExpanded(True)

                self._index[root] = item

            def _recursive(parent, children, split=None, root="", root_path=root_path):
                for text, val in sorted(children.items()):
                    if not parent:
                        parent = self
                    path = split.join([root, text])
                    child = None
                    if not root_path or not root_path.startswith(path):
                        path = norm_path(path)
                        child = SidebarWidgetItem(parent)
                        child.setText(0, six.text_type(text))
                        child.set_path(path)

                        self._index[path] = child

                    _recursive(child, val, split=split, root=path)

            _recursive(item, data[key], split=split, root=root)

        self.update()
        self.refreshFilter()

    def update_paths(self, dir_paths=None):
        if not self.library:
            return
        dir_paths = dir_paths or [manager.current_path]
        if not dir_paths:
            return

        for d in dir_paths:
            self.library.refresh_path(d)
        self.refresh_data()

