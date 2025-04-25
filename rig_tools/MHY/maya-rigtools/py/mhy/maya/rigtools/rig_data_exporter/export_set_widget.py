from functools import partial

from maya import cmds, OpenMaya

from mhy.qt.core import QtGui, QtCore, QtWidgets

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node

import mhy.qt.core.utils as qtutil
import mhy.maya.rig.node.export_set as es


EXPORT_COLOR = (90, 220, 90)
NON_EXPORT_COLOR = (250, 250, 250)
ERROR_COLOR = (250, 0, 0)


def get_closest_parent_in_set(node, node_set):
    """Returns the closest parent of a node in a given set.

    Args:
        node (DagNode or str): A node to work with.
        node_set (set): A set to search the closest parent.

    Returns:
        Transform or None: The closest parent.
    """
    node = Node(node)
    parent = node.get_parent()
    while parent:
        if parent in node_set:
            return parent
        parent = parent.get_parent()
    return


class NodeTree(QtWidgets.QTreeWidget):
    """
    Customized QTreeWidget for manager exportable nodes.
    """

    def __init__(self, *args, **kwargs):
        super(NodeTree, self).__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setExpandsOnDoubleClick(False)
        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True)
        self.setSortingEnabled(False)
        self.setColumnCount(2)
        self.setHeaderLabels(('Joint', 'Parent Override'))
        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setStretchLastSection(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setStyleSheet(
            ('QTreeWidget{font: 13px;}'
             'QTreeWidget::item {font: 13px; '
             'border-right: 1px solid rgb(100, 100, 100);}'))

        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.create_context_menu)
        self.itemDoubleClicked.connect(self.select)

        self.__exp_set = None
        self.__exp_node_type = None

    def set_export_set(self, export_set):
        """Sets the export set to work with."""
        if export_set:
            self.__exp_set = es.ExportSet(export_set)
        else:
            self.__exp_set = None

    def set_export_node_type(self, typ):
        """Sets the export node type to work with."""
        self.__exp_node_type = typ

    def create_context_menu(self):
        menu = QtWidgets.QMenu(self)

        is_ref = self.__exp_set and self.__exp_set.is_referenced
        if not is_ref and self.selectedItems():
            action = menu.addAction('Add to Set')
            action.setIcon(qtutil.get_icon(':/addClip.png'))
            action.triggered.connect(self.add_member)

            action = menu.addAction('Remove from Set')
            action.setIcon(qtutil.get_icon(':/stopClip.png'))
            action.triggered.connect(self.remove_member)

            action = menu.addAction('Remove Parent Override')
            action.setIcon(qtutil.get_icon(':/unparent.png'))
            action.triggered.connect(self.remove_parent_override)

            menu.addSeparator()

        action = menu.addAction('Expand All')
        action.setIcon(qtutil.get_icon(':/arrowDown.png'))
        action.triggered.connect(partial(self.set_expanded, True))

        action = menu.addAction('Collapse All')
        action.setIcon(qtutil.get_icon(':/arrowRight.png'))
        action.triggered.connect(partial(self.set_expanded, False))

        menu.popup(QtGui.QCursor.pos())

    def refresh(self, nonexportable=True, right_side=True):
        """Refreshes this tree.

        Args:
            nonexportable (bool): Show non-exportable nodes?
            right_side (bool): Show nodes on the right side?

        Returns:
            None
        """
        # get current selection, expanded, and scroll position info
        # we'll try to restore these after refreshing.
        cur_dict = {}
        for item in self.get_items():
            cur_dict[item.text(0)] = (item.isSelected(), item.isExpanded())
        top_item_text = self.itemAt(0, 0)
        if top_item_text:
            top_item_text = top_item_text.text(0)
        top_item = None

        # clear the tree
        self.clear()

        if not self.__exp_set:
            return

        # get export set members and export ready nodes.
        members = set(self.__exp_set.members)
        namespace = NodeName.namespace(self.__exp_set)
        data = es.get_export_ready_node_dict(namespace=namespace)

        item_dict = {}
        for node in data.get(self.__exp_node_type, []):
            # apply nonexportable filter
            if not nonexportable and not self.__exp_set.is_member(node):
                continue

            # apply right_side filter
            if not right_side and \
               NodeName.is_valid(node) and \
               NodeName(node).is_right:
                continue

            # find the parent item
            parent_item = None
            if self.__exp_node_type == 'joint':
                parent = get_closest_parent_in_set(node, item_dict)
                if parent:
                    parent_item = item_dict.get(parent)

            # create a tree item for this node
            item = QtWidgets.QTreeWidgetItem()
            if parent_item:
                item = QtWidgets.QTreeWidgetItem(parent_item)
            else:
                item = QtWidgets.QTreeWidgetItem()
                self.addTopLevelItem(item)
            if node.name == top_item_text:
                top_item = item

            # set item text and color
            item.setText(0, node.name)
            po = es.get_parent_override(node)
            if po:
                item.setText(1, po.name)
                if self.__exp_set.is_member(po):
                    item.setForeground(1, QtGui.QColor(*EXPORT_COLOR))
                else:
                    item.setForeground(1, QtGui.QColor(*ERROR_COLOR))
            if node.name in members:
                item.setForeground(0, QtGui.QColor(*EXPORT_COLOR))

            # restore previous selected and expanded states
            sel, exp = cur_dict.get(node.name, (False, False))
            item.setSelected(sel)
            item.setExpanded(exp)
            item_dict[node] = item

        # restore previous scroll position
        if top_item:
            self.scrollToItem(
                top_item, QtWidgets.QAbstractItemView.PositionAtTop)

        # adjust the parent override column size to context
        self.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def get_items(self, item=None):
        """Recursively finds and returns all items under a given root.

        Args:
            item (QTreeWidgetItem): The root item to work with.
                If None, returns all items in this tree.
        """
        all_items = []
        if not item:
            for i in range(self.topLevelItemCount()):
                it = self.topLevelItem(i)
                all_items.append(it)
                all_items += self.get_items(it)
        else:
            for i in range(item.childCount()):
                it = item.child(i)
                all_items.append(it)
                all_items += self.get_items(it)
        return all_items

    def set_expanded(self, state):
        """Sets the expanded state for all items."""
        for item in self.get_items():
            item.setExpanded(state)

    def add_member(self):
        """Adds the selected items as members in the associated export set."""
        if not self.__exp_set:
            cmds.warning('No export set specified.')
            return
        for item in self.selectedItems():
            self.__exp_set.add_member(item.text(0))
            item.setForeground(0, QtGui.QColor(*EXPORT_COLOR))

    def remove_member(self):
        """Removes the selected items from the associated export set."""
        if not self.__exp_set:
            cmds.warning('No export set specified.')
            return
        for item in self.selectedItems():
            self.__exp_set.remove_member(item.text(0))
            item.setForeground(0, QtGui.QColor(*NON_EXPORT_COLOR))

    def remove_parent_override(self):
        """Removes parent override for the selected items."""
        if not self.__exp_set:
            cmds.warning('No export set specified.')
            return
        for item in self.selectedItems():
            es.remove_parent_override(item.text(0))
            item.setText(1, '')

    def select(self, item, column):
        """Selects an item at a given column."""
        node = item.text(column)
        if cmds.objExists(node):
            cmds.select(node, replace=True)

    def dropEvent(self, event):
        """Apply parent override on drop."""
        source_items = self.selectedItems()
        if not source_items:
            return
        elif not self.__exp_set:
            cmds.warning('No export set specified.')
            return

        item = self.itemAt(event.pos())
        if item:
            parent = item.text(0)
            for source in source_items:
                source = source.text(0)
                if parent != source:
                    es.set_parent_override(source, parent)
                    if not self.__exp_set.is_member(parent):
                        self.__exp_set.add_member(parent)
                    item.setText(1, parent)
            self.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)


class ExportSetWidget(QtWidgets.QWidget):
    """
    A widget for managing export sets.
    """

    def __init__(self, *args, **kwargs):
        super(ExportSetWidget, self).__init__(*args, **kwargs)
        self.__edit_widgets = []

        central_layout = QtWidgets.QVBoxLayout()
        self.setLayout(central_layout)

        grid = QtWidgets.QGridLayout()
        central_layout.addLayout(grid)

        # export set drop down
        grid.addWidget(QtWidgets.QLabel('Export Set: '), 0, 0, 1, 1)
        self.cbx_set = QtWidgets.QComboBox()
        self.cbx_set.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        grid.addWidget(self.cbx_set, 0, 1, 1, 1)
        self.btn_add_set = QtWidgets.QPushButton()
        self.btn_add_set.setIcon(qtutil.get_icon(':/addClip.png'))
        self.btn_add_set.setFixedWidth(30)
        grid.addWidget(self.btn_add_set, 0, 2, 1, 1)
        self.__edit_widgets.append(self.btn_add_set)

        # node type drop down
        grid.addWidget(QtWidgets.QLabel('Node Type: '), 1, 0, 1, 1)
        self.cbx_type = QtWidgets.QComboBox()
        self.cbx_type.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.cbx_type.addItems(es.EXPORT_NODE_TYPES)
        grid.addWidget(self.cbx_type, 1, 1, 1, 2)

        hbox = QtWidgets.QHBoxLayout()
        central_layout.addLayout(hbox)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        self.cbx_nonexportable = QtWidgets.QCheckBox('Exportable Only')
        self.cbx_nonexportable.setChecked(True)
        hbox.addWidget(self.cbx_nonexportable)

        self.cbx_right = QtWidgets.QCheckBox('Right Side')
        self.cbx_right.setChecked(True)
        hbox.addWidget(self.cbx_right)

        self.cbx_parent_ovr = QtWidgets.QCheckBox('Enable Parent Override')
        self.cbx_parent_ovr.setChecked(False)
        hbox.addWidget(self.cbx_parent_ovr)
        self.__edit_widgets.append(self.cbx_parent_ovr)

        hbox.addStretch(10)

        self.btn_select = QtWidgets.QPushButton()
        self.btn_select.setIcon(qtutil.get_icon(':/selectObject.png'))
        self.btn_select.setToolTip(
            'Select exportable objects in the list below.')
        hbox.addWidget(self.btn_select)

        self.btn_mirror = QtWidgets.QPushButton()
        self.btn_mirror.setIcon(
            qtutil.get_icon(':/HIKmirrorSkelLeftToRight.png'))
        self.btn_mirror.setToolTip(
            'Mirror exportable data from left to right.')
        hbox.addWidget(self.btn_mirror)
        self.__edit_widgets.append(self.btn_mirror)

        self.btn_add_inf = QtWidgets.QPushButton()
        self.btn_add_inf.setIcon(
            qtutil.get_icon(':/p-add.png'))
        self.btn_add_inf.setToolTip(
            'Add the selected skinCluster influences to this set.')
        hbox.addWidget(self.btn_add_inf)
        self.__edit_widgets.append(self.btn_add_inf)

        self.btn_replace_inf = QtWidgets.QPushButton()
        self.btn_replace_inf.setIcon(
            qtutil.get_icon(':/p-head.png'))
        self.btn_replace_inf.setToolTip(
            ('Replace the set membership with '
             'the selected skinCluster influences'))
        hbox.addWidget(self.btn_replace_inf)
        self.__edit_widgets.append(self.btn_replace_inf)

        # expot-ready node tree
        self.tw_nodes = NodeTree()
        central_layout.addWidget(self.tw_nodes)

        hbox = QtWidgets.QHBoxLayout()
        central_layout.addLayout(hbox)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        self.cbx_build_type = QtWidgets.QComboBox()
        self.cbx_build_type.addItems(('actor', 'animation'))
        hbox.addWidget(self.cbx_build_type)

        # self.cbx_attach = QtWidgets.QCheckBox('Attach To Rig')
        # self.cbx_attach.setChecked(True)
        # hbox.addWidget(self.cbx_attach)

        # self.cbx_skel_only = QtWidgets.QCheckBox('Skeleton Only')
        # self.cbx_skel_only.setChecked(False)
        # hbox.addWidget(self.cbx_skel_only)

        # hbox.addStretch(10)

        self.btn_build_exp = QtWidgets.QPushButton('Build Export Asset')
        hbox.addWidget(self.btn_build_exp)
        self.btn_build_exp.setIcon(qtutil.get_icon(':/out_character.png'))
        self.btn_build_exp.setFixedHeight(35)
        self.btn_build_exp.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.connect_signals()
        self.refresh()

    def connect_signals(self):
        self.btn_add_set.clicked.connect(self.add_set)
        self.cbx_set.currentTextChanged.connect(self.export_set_changed)
        self.cbx_type.currentTextChanged.connect(self.export_node_type_changed)
        self.btn_build_exp.clicked.connect(self.build_asset)
        self.cbx_nonexportable.stateChanged.connect(self.refresh_tree)
        self.cbx_right.stateChanged.connect(self.refresh_tree)
        self.cbx_parent_ovr.stateChanged.connect(
            self.refresh_parent_override_enabled)
        self.btn_select.clicked.connect(self.select_exportable)
        self.btn_mirror.clicked.connect(self.mirror_exportable)
        self.btn_add_inf.clicked.connect(partial(self.add_influence, False))
        self.btn_replace_inf.clicked.connect(partial(self.add_influence, True))

    def enterEvent(self, event):
        """Refreshes this UI on cursor enter. This ensures the UI is
        in sync with any potential manual changes in the scene."""
        self.refresh()
        return super(ExportSetWidget, self).enterEvent(event)

    def refresh(self, *args, **kwargs):
        """Refresh the entire UI."""
        self.cbx_set.blockSignals(True)

        # remember the current export set
        sel = self.cbx_set.currentText()
        self.cbx_set.clear()

        # refresh the export set drop down
        sets = es.ExportSet.get_export_sets()
        if sets:
            self.cbx_set.addItems([x.name for x in sets])

        # try restore the previous export set.
        i = self.cbx_set.findText(sel)
        if i >= 0:
            self.cbx_set.setCurrentIndex(i)

        self.cbx_set.blockSignals(False)

        # update the node tree
        self.tw_nodes.set_export_set(self.cbx_set.currentText())
        export_node_type = self.cbx_type.currentText()
        self.tw_nodes.set_export_node_type(export_node_type)
        self.refresh_tree()

        # disable editing widgets if the current export set is referenced.
        export_set = self.current_export_set()
        if export_set and export_set.is_referenced:
            self.cbx_parent_ovr.setChecked(False)
            for widget in self.__edit_widgets:
                widget.setEnabled(False)
        else:
            for widget in self.__edit_widgets:
                widget.setEnabled(True)

    def export_set_changed(self, export_set):
        """On export set changed callback."""
        self.tw_nodes.set_export_set(export_set)
        self.refresh_tree()

    def export_node_type_changed(self, export_node_type):
        """On export node type changed callback."""
        self.tw_nodes.set_export_node_type(export_node_type)
        self.refresh_tree()
        if export_node_type == 'joint':
            self.btn_add_inf.show()
            self.btn_replace_inf.show()
        else:
            self.btn_add_inf.hide()
            self.btn_replace_inf.hide()

    def refresh_tree(self):
        """Refreshes the node tree."""
        nonexportable = self.cbx_nonexportable.isChecked()
        right_side = self.cbx_right.isChecked()
        self.tw_nodes.refresh(
            nonexportable=nonexportable, right_side=right_side)
        self.refresh_parent_override_enabled()

    def current_export_set(self):
        """Returns the current export set."""
        export_set = self.cbx_set.currentText()
        if not export_set:
            cmds.warning('No export set specified.')
            return
        return es.ExportSet(export_set)

    def refresh_parent_override_enabled(self):
        """Refreshes parent override enabled state."""
        if self.cbx_parent_ovr.isChecked():
            mode = QtWidgets.QAbstractItemView.DragDrop
        else:
            mode = QtWidgets.QAbstractItemView.NoDragDrop
        self.tw_nodes.setDragDropMode(mode)

    def add_set(self):
        """Adds a new export set in the scene."""
        text, status = QtWidgets.QInputDialog.getText(
            self, 'New Export Set', 'New Export Set Name')
        if status and text:
            if cmds.objExists(text):
                cmds.warning('{} already exists.'.format(text))
                return
            es.ExportSet.create(name=text)
            self.refresh()
            self.cbx_set.setCurrentText(text)

    def select_exportable(self):
        """Selects all exportable nodes of the current type."""
        export_set = self.current_export_set()
        if not export_set:
            return
        export_node_type = self.cbx_type.currentText()
        objects = export_set.get_member_dict().get(export_node_type)
        if objects:
            cmds.select(objects, replace=True)

    def mirror_exportable(self):
        """Mirrors export data from left to right."""
        export_set = self.current_export_set()
        if not export_set:
            return
        export_node_type = self.cbx_type.currentText()

        data = es.get_export_ready_node_dict()
        for node in data.get(export_node_type, []):
            if not NodeName.is_valid(node):
                continue
            other = NodeName(node).flip()
            if not cmds.objExists(other):
                continue

            # mirror export set membership
            if export_set.is_member(node):
                export_set.add_member(other)
            else:
                export_set.remove_member(other)

            # mirror parent override
            parent = es.get_parent_override(node)
            parent_set = False
            if parent and NodeName.is_valid(parent):
                other_parent = NodeName(parent).flip()
                if cmds.objExists(other_parent):
                    es.set_parent_override(other, other_parent)
                    parent_set = True
            if not parent_set:
                es.remove_parent_override(other)

        self.refresh()

    def add_influence(self, replace=False):
        """Adds or replaces selected skinCluster influences
        to the current set."""
        export_set = self.current_export_set()
        if not export_set:
            return
        skins = []
        for each in cmds.ls(selection=True, type=('transform', 'mesh')):
            skins.extend(Node(each).get_deformers(type_='skinCluster'))
        if not skins:
            cmds.warning('No skinCluster found on selected objects.')
            return

        if replace:
            result = QtWidgets.QMessageBox.question(
                self,
                'Warning',
                ('Are you sure you want to replace current exportable joints'
                 ' with the selected skinCluster influences?'))
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return
            for each in export_set.members:
                if cmds.nodeType(each) == 'joint':
                    export_set.remove_member(each)

        added_infs = set()
        skipped_infs = set()
        for skin in skins:
            for inf in skin.influences:
                if es.is_export_ready(inf):
                    export_set.add_member(inf)
                    added_infs.add(inf)
                else:
                    skipped_infs.add(inf)

        if added_infs:
            OpenMaya.MGlobal.displayInfo(
                'Added joints to set: {}'.format(added_infs))
        if skipped_infs:
            cmds.warning(
                'Skipped non-export ready joints: {}'.format(skipped_infs))

        self.refresh()

    def build_asset(self):
        """Builds a self-contained asset group."""
        export_set = self.current_export_set()
        if not export_set:
            return
        build_type = self.cbx_build_type.currentIndex()
        if build_type == 0:
            attach = False
            skel_only = False
        else:
            attach = True
            skel_only = True
        export_set.create_export_asset(
            attach=attach, skel_only=skel_only)
