from PySide2 import QtWidgets, QtCore
from mhy.maya.anim_lib.signal_manager import SignalManager
import mhy.maya.anim_lib.widgets.sequence_widget as sw
import maya.cmds as cmds
from mhy.maya.anim.lib.collection import Collection
from mhy.maya.utils import undoable
import logging
from mhy.maya.anim_lib.utils import list_all_reference_namespaces

logger = logging.getLogger(__name__)


class AttibuteWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AttibuteWidget, self).__init__(parent=parent)
        self.item = None
        self.current_namespaces = [""]
        self.name_space_map = {}

        main_layout = QtWidgets.QVBoxLayout(self)
        self.image_widget = sw.ThumbNailIcon(
            static=False,
            parent=self,
            editable=False)
        main_layout.addWidget(self.image_widget)

        self.scroll_area = QtWidgets.QScrollArea(self)
        info_widget = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout()
        info_widget.setLayout(info_layout)
        self.scroll_area.setWidget(info_widget)

        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        self.name_label = QtWidgets.QLabel('Name: ')
        self.name_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.num_objects = QtWidgets.QLabel('Number Of Objects: ')
        self.num_objects.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.type_label = QtWidgets.QLabel('Type: ')
        self.type_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.user_label = QtWidgets.QLabel('User Created: ')
        self.user_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.comment_label = QtWidgets.QLabel('Comment: ')
        self.comment_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.date_label = QtWidgets.QLabel('Date Created: ')
        self.date_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.start_frame_label = QtWidgets.QLabel('Start Frame: ')
        self.start_frame_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.end_frame_label = QtWidgets.QLabel('End Frame: ')
        self.end_frame_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.source_file_label = QtWidgets.QLabel('Source File: ')
        self.source_file_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.num_objects)
        info_layout.addWidget(self.type_label)
        info_layout.addWidget(self.user_label)
        info_layout.addWidget(self.date_label)
        info_layout.addWidget(self.start_frame_label)
        info_layout.addWidget(self.end_frame_label)
        info_layout.addWidget(self.comment_label)
        info_layout.addWidget(self.source_file_label)

        main_layout.addWidget(self.scroll_area)

        ns_map_group = QtWidgets.QGroupBox("Namespace:")
        ns_map_layout = QtWidgets.QHBoxLayout(ns_map_group)
        self.ns_from_list = QtWidgets.QListWidget()
        ns_to_label = QtWidgets.QLabel('->')
        self.ns_to_list = QtWidgets.QListWidget()
        ns_map_layout.addWidget(self.ns_from_list)
        ns_map_layout.addWidget(ns_to_label)
        ns_map_layout.addWidget(self.ns_to_list)

        ns_from_sel_mod = self.ns_from_list.selectionModel()
        ns_to_sel_mod = self.ns_to_list.selectionModel()
        ns_from_sel_mod.selectionChanged.connect(self.from_ns_sel_changed_cb)
        ns_to_sel_mod.selectionChanged.connect(self.to_ns_sel_changed_cb)

        main_layout.addWidget(ns_map_group)

        options_group = QtWidgets.QGroupBox("Options:")
        option_layout = QtWidgets.QGridLayout(options_group)
        self.replace_radio = QtWidgets.QRadioButton("Replace")
        self.merge_radio = QtWidgets.QRadioButton("Merge")
        self.replace_radio.setChecked(True)
        option_layout.addWidget(self.replace_radio, 0, 0)
        option_layout.addWidget(self.merge_radio, 0, 1)

        start_frame_label = QtWidgets.QLabel("Start frame")
        self.start_frame_line = QtWidgets.QLineEdit(self)
        option_layout.addWidget(start_frame_label, 1, 0)
        option_layout.addWidget(self.start_frame_line, 1, 1)

        main_layout.addWidget(options_group)

        apply_pb = QtWidgets.QPushButton("Apply")
        apply_pb.clicked.connect(self.apply_pose_cb)
        main_layout.addWidget(apply_pb)

        SignalManager.item_sel_changed.connect(self.update_widgets)

    def from_ns_sel_changed_cb(self, sel, dsel):
        current = self.ns_from_list.currentItem()

        sel_model = self.ns_to_list.selectionModel()
        sel_model.blockSignals(True)
        sel_model.clearSelection()
        from_ns = current.data(QtCore.Qt.DisplayRole)
        if from_ns is None:
            return
        if from_ns in self.name_space_map:
            dst_ns = self.name_space_map[from_ns]
            found = False
            for x in range(self.ns_to_list.count()):
                item = self.ns_to_list.item(x)
                item_ns = item.data(QtCore.Qt.DisplayRole)
                if item_ns == dst_ns:
                    item.setSelected(True)
                    found = True
                    break

            if not found:
                self.name_space_map[from_ns] = None
        sel_model.blockSignals(False)
        self.ns_to_list.viewport().update()

    def to_ns_sel_changed_cb(self, sel, dsel):
        current = self.ns_from_list.currentItem()
        if not current:
            return
        from_ns = current.data(QtCore.Qt.DisplayRole)

        current_to_ns = self.ns_to_list.currentItem()
        if not current_to_ns:
            return
        to_ns = current_to_ns.data(QtCore.Qt.DisplayRole)

        self.name_space_map[from_ns] = to_ns

    def update_widgets(self, item):
        self.ns_from_list.clear()
        self.item = item
        if not self.item:
            self.num_objects.setText('Number of Objects: 0')
            self.name_label.setText('Name:')
            self.type_label.setText('Type:')
            self.start_frame_label.setText('Start Frame: ')
            self.end_frame_label.setText('End Frame: ')
            self.user_label.setText('User Created: ')
            self.date_label.setText('Date Created: ')
            self.comment_label.setText('Comment: ')
            self.source_file_label.setText('Source File:')
            self.image_widget.update_thumb_nail_cb(None)
        else:
            if isinstance(self.item, list):
                self.item = self.item[0]
            self.num_objects.setText('Number of Objects: {}'.format(self.item.num_nodes))
            self.name_label.setText('Name: {}'.format(self.item.name))
            self.user_label.setText('User Created: {}'.format(self.item.user_created))
            self.date_label.setText('Date Created: {}'.format(self.item.date_created))
            self.comment_label.setText('Comment: {}'.format(self.item.comment))
            self.source_file_label.setText('Source File: {}'.format(self.item.source_file))
            image_root = self.item.get_thumb_nail_dir()
            self.image_widget.update_thumb_nail_cb(image_root)

            self.ns_from_list.addItems(self.item.name_spaces)

            if self.item.is_static:
                self.type_label.setText('Type: Pose')
                self.start_frame_label.setText('Start Frame: ')
                self.end_frame_label.setText('End Frame: ')
                self.start_frame_line.setText('')
            else:
                self.type_label.setText('Type: Animation')
                self.start_frame_label.setText('Start Frame: {}'.format(self.item.start_frame))
                self.end_frame_label.setText('End Frame: {}'.format(self.item.end_frame))
                self.start_frame_line.setText(str(self.item.start_frame))

    def enterEvent(self, event):
        """
        Override the enter event to refresh the namespace
        Args:
            event:

        Returns:

        """
        namespaces = list_all_reference_namespaces()
        if namespaces != self.current_namespaces:
            self.current_namespaces = namespaces
            self.ns_to_list.clear()
            self.ns_to_list.addItems(namespaces)

        source_name_spaces = []
        default_ns = None
        if len(namespaces) == 1:
            default_ns = ""

        if len(namespaces) == 2:
            # Since default there's an
            # empty namespace in the list, if the length
            # is 2 which means only one reference rig in
            # the scene, we use it as default target
            # namespace, so that user doesn't need to manually set
            # it in the ui every time
            default_ns = namespaces[-1]

        for x in range(self.ns_from_list.count()):
            item = self.ns_from_list.item(x)
            item_ns = item.data(QtCore.Qt.DisplayRole)
            if item_ns not in self.name_space_map:
                self.name_space_map[item_ns] = default_ns
            source_name_spaces.append(item_ns)

    @undoable
    def apply_pose_cb(self):
        """
        Apply selected pose item data to objects in the scene.

        Namespace mapping is initialized in half auto mechanism.

        1. If no target objects selected, cached name space map will be used

        2. If selected target objects are under the same namespace ns1,
        and only one namespace in the pose data let's say ns2, the namespace
         mapping will be {ns1 : ns2}

        2. Else, we will rely on the namespace map variable

        Returns:

        """
        if not self.item:
            logger.info("No Pose Item Selected")
            return

        # Default parameters values
        merge = False
        offset_frames = 0

        if self.merge_radio.isChecked():
            merge = True

        if not self.item.is_static:
            start_frame = float(self.start_frame_line.text())
            offset_frames = 0
            if start_frame != self.item.start_frame:
                offset_frames = start_frame - self.item.start_frame

        sel = cmds.ls(sl=True)

        if sel:
            sel_ns = self.get_selection_namespaces(sel)

            if len(self.item.name_spaces) == 1 and len(sel_ns):
                # Only if there only one namespace in the data and user
                # select target objects
                # We can by pass the cached namespace
                # map and generate namespace map on the fly
                namespace_map = {self.item.name_spaces[0]: sel_ns[0]}

            else:
                namespace_map = {k: v for k, v in self.name_space_map.items()
                                 if k in sel_ns}
        else:
            namespace_map = self.name_space_map

        logger.info("Applying pose data with namespace map: {}".format(
            namespace_map))

        if sel:
            Collection.load(
                data=self.item.path,
                namespace_map=namespace_map,
                target_objects=sel,
                merge=merge,
                offset_frames=offset_frames)
        else:
            Collection.load(
                data=self.item.path,
                namespace_map=namespace_map,
                merge=merge,
                offset_frames=offset_frames)

    @staticmethod
    def get_selection_namespaces(sel):
        ns_list = []
        for i in sel:
            if ':' in i:
                ns = i.split(':')[0]
                ns_list.append(ns)
            else:
                ns_list.append('')
        ns_list = list(set(ns_list))
        return ns_list
