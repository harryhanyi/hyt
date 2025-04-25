import os
import json
import logging
import random
from six import string_types

from mhy.qt.core.widgets.node_graph import NodeGraphView, NodeGraphScene

from mhy.protostar.ui.view.parameter_item import ParameterNode
from mhy.protostar.ui.manager import action_lib
from mhy.protostar.ui.widget.library_browser import LibraryWidget

from mhy.qt.core.Qt import QtCore, QtGui, QtWidgets
from mhy.protostar.ui.view.node import Node
import mhy.protostar.ui.manager as manager

logger = logging.getLogger(__name__)


class GraphicView(NodeGraphView):
    minimum_pixel = 420

    def __init__(self, scene, parent):
        super(GraphicView, self).__init__(scene=scene, parent=parent)
        self.setAcceptDrops(True)

        self.view_zoom_changed.connect(manager.scale_pix_map)
        manager.SignalManager.repaint_lines_signal.connect(
            self.refresh_line_items_cb
        )

    def contextMenuEvent(self, event):
        """
        Popup menu action for browsing and create action or
        graph from library

        """
        super(GraphicView, self).contextMenuEvent(event)
        global_pos = event.globalPos()
        scene_pos = self.mapToScene(self.mapFromGlobal(global_pos))
        items = self.scene().items(scene_pos)
        for i in items:
            if i.type_name == 'node':
                menu = QtWidgets.QMenu(self)
                action = menu.addAction("Toggle Break point")
                action.triggered.connect(self.toggle_bp_for_selected)
                menu.exec_(QtGui.QCursor.pos())
                return

        self.menu = QtWidgets.QMenu(self)
        lib_action = QtWidgets.QWidgetAction(self)
        self.lib_widget = LibraryWidget(self)
        lib_action.setDefaultWidget(self.lib_widget)
        self.menu.addAction(lib_action)
        self.lib_widget.action_lib_view.currentItemChanged.connect(
            self.__create_item_from_library)
        self.menu.exec_(QtGui.QCursor.pos())

    @QtCore.Slot()
    def __create_item_from_library(self):
        """
        Called to create selected item in the LibraryWidget to the
        active view

        """
        current_items = self.lib_widget.action_lib_view.currentItem()
        self.scene().clearSelection()
        if current_items:
            user_data = current_items.data(QtCore.Qt.UserRole)
            name = current_items.data(QtCore.Qt.DisplayRole)
            if user_data[0] == 'action':
                self.create_action_cb(name)
            elif user_data[0] == 'graph':
                self.create_graph_cb(
                    source=name,
                    team=user_data[1],
                    name=name.split(':')[-1])
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Failed",
                    "Failed to create {}".format(name))
                return
        self.menu.close()

    @property
    def graph(self):
        scene = self.scene()
        if scene:
            return scene.graph

    def find_item(self, name):
        """
        Convenient method looking for item from graphic scene associated
        with this view
        Args:
            name(str): The name of the item. Use full name for parameter item

        Returns:
            Node or ParameterNode
        """
        scene = self.scene()
        if scene:
            return scene.find_item(name)

    def load_data(self, data):
        scene = self.scene()
        if not scene:
            return
        data = scene.load_data(data)
        self.populate_internal_parameter_connections()
        self.__load_parameter_node_positions()
        return data

    def __load_parameter_node_positions(self):
        parameter_ui_data = self.graph.ui_data.get('parameter_node')
        if not parameter_ui_data:
            return
        for par_name, pos in parameter_ui_data.items():
            item = self.find_item(par_name)
            if not item:
                item = self.create_parameter_node(par_name)
            if item:
                item.setPos(*pos)
            else:
                logging.warning("Failed to get"
                                " parameter node {}".format(par_name))

    def populate_internal_parameter_connections(self):
        for par in self.graph.iter_params():
            inputs = list()
            if par.has_direct_input:
                inputs = par.input_params

            for src in inputs:
                src_owner = src.owner
                src_graph = src_owner.graph
                if src_graph == self.graph:
                    # If the owner of source parameter is the graph of this
                    # scene. Try to build connection from parameter node to
                    # the input socket of this parameter
                    param_item = self.find_item(par.full_name)

                    if not param_item:
                        # Create parameter node if necessary
                        param_item = self.create_parameter_node(par)

                    if not param_item:
                        logging.warning("Failed to create parameter"
                                        " node for {}".format(par))
                        continue

                    source_action = self.find_item(src_owner.name)
                    if not source_action:
                        logging.warning("Failed to find node "
                                        "of {}".format(source_action))
                        continue

                    source_para_item = source_action.get_param_item(src.name)
                    if not source_para_item:
                        logging.warning(
                            "Failed to find parameter item named {} "
                            "from the action item".format(
                                src.name,
                                source_action)
                        )
                        continue

                    if not source_para_item.output_socket.is_connected_to(
                            param_item.input_socket):
                        source_para_item.output_socket.create_connection_line_to(
                            param_item.input_socket)

    # ==========================================================
    # Create item methods
    # ==========================================================

    def create_action_cb(self, action_type):
        item = self.scene().add_action(action_type=action_type)
        self.__post_item_creation(item)
        return item

    def create_graph_cb(self, source=None, team=None, name=None):
        item = self.scene().add_graph(source=source, team=team, name=name)
        self.__post_item_creation(item)
        return item

    def create_parameter_node(self, parameter):
        item = self.scene().add_parameter_node(parameter=parameter)
        self.__post_item_creation(item)
        return item

    def __post_item_creation(self, item):
        if not item:
            return
        current_center = self.get_center()
        view_rect = self.viewport().rect()
        width = view_rect.width()
        height = view_rect.height()

        self.scene().clearSelection()

        item.setPos(current_center.x() + random.uniform(-width/3, width/3),
                    current_center.y() + random.uniform(-height/3, height/3))
        item.setSelected(True)
        self.scene().selection_changed.emit([item])

    def copy_selected(self):
        copy_items = self.scene().copy_selected()

    def get_center(self):
        """
        Get the center of the viewport
        Returns:
            QPoint:
        """
        return self.mapToScene(self.viewport().rect().center())

    def keyPressEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier and \
                event.key() == QtCore.Qt.Key_D:
            self.copy_selected()

        if event.key() == QtCore.Qt.Key_Delete or \
                event.key() == QtCore.Qt.Key_Backspace:
            self.scene().delete_selected()

        if event.key() == QtCore.Qt.Key_F:
            self.frame_items()

        elif event.key() == QtCore.Qt.Key_1:
            self.scene().set_selected_collapsed(True)

        elif event.key() == QtCore.Qt.Key_2:
            self.scene().set_selected_collapsed(False)

        elif event.key() == QtCore.Qt.Key_Up:
            self.scene().increase_priority_level()

        elif event.key() == QtCore.Qt.Key_Down:
            self.scene().decrease_priority_level()

    def dropEvent(self, event):
        """
        Override drop event to support 2 mimeData drop:
        1. Parameter creation drop: Create parameter node dragged from graph
        attribute panel

        2. File open drop: Open a data file dragged from explorer

        Args:
            event:

        """
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            local_file = str(mime_data.urls()[0].toLocalFile())
            manager.SignalManager.file_to_open_signal.emit(local_file)
        else:
            par_name = event.mimeData().text()
            if par_name:
                par = self.scene().graph.param(par_name)

                if par:
                    par_item = self.scene().find_item(par.full_name)
                    if par_item:
                        self.frame_items(items=[par_item])
                    else:
                        par_item = ParameterNode(par)
                        self.scene().addItem(par_item)
                        par_item.setPos(self.mapToScene(event.pos()))

    def dragMoveEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        elif mime_data.hasFormat('text/plain'):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            super(GraphicView, self).dragMoveEvent(event)

    @QtCore.Slot()
    def refresh_line_items_cb(self):
        """ Force updating viewport """
        self.viewport().update()

    def toggle_bp_for_selected(self):
        self.scene().toggle_bp_for_selected()


class GraphicScene(NodeGraphScene):
    selection_changed = QtCore.Signal(list)

    def __init__(self, graph):
        super(GraphicScene, self).__init__()
        self.__graph = graph
        self.pending_line = None
        self.connected_lines = list()
        self.hovered_items = list()

    @property
    def graph(self):
        return self.__graph

    @property
    def parameter_nodes(self):
        return [i for i in self.items() if i.type_name == 'parameter']

    def add_action(self, action_type):
        """
        Add action to the graph view
        Args:
            action_type:

        Returns:

        """
        type_name = action_type.split(':')[-1]
        action = action_lib.create_action(
            action_type,
            name=type_name,
            graph=self.__graph)

        if not action:
            return
        item = Node(action)
        self.addItem(item)
        return item

    def add_graph(self, source=None, name=None, team=None):
        """
        Add a graph item to this scene
        Args:
            source (string or None): Source name of a graph in the library.
                if a team prefix exists (e.g. "team:graph"), create an instance
                of this exact graph. Otherwise, search this graph under all
                teams and create an instance of the first one found.
                If None, create an empty graph.
            name(str): The name of graph
            team (None or string): If specified, only search under this team.
                If None, search all teams.
                Ignored if name contains a team prefix (e.g. team:object).

        Returns:
            QGraphicsItem: Created graph item
        """
        if name is None:
            name = 'Graph'
        graph = action_lib.create_graph(
            source=source,
            name=name,
            team=team,
            graph=self.__graph)
        if not graph:
            return
        item = Node(graph)
        self.addItem(item)
        return item

    def add_parameter_node(self, parameter):
        if isinstance(parameter, string_types):
            parameter = parameter.replace(self.graph.name + '.', "", 1)
            parameter = self.graph.param(parameter)
        if not parameter:
            return

        node = ParameterNode(parameter)
        self.addItem(node)
        return node

    def update_hovered_items(self, sockets):
        """
        This method will replace hovered items and force refresh
        all the items before and after this replacement.
        Args:
            sockets:

        """
        current_sockets = self.hovered_items
        self.hovered_items = sockets
        for socket in list(set(sockets + current_sockets)):
            socket.update()

    def delete_selected(self):
        """
        Delete selected items
        """
        sel = self.selectedItems()
        for item in sel:
            if item.type_name == 'node':
                item.break_connections()
                self.__graph.remove_object(item.instance, force=True)
            elif item.type_name == 'line':
                if item.source and item.target:
                    item.disconnect_target()
            elif item.type_name == 'parameter':
                item.break_connections()
            item.destruct()
        self.selection_changed.emit(list())

    def set_selected_collapsed(self, state):
        sel = self.selectedItems()
        for item in sel:
            if isinstance(item, Node):
                item.set_collapsed(state)

    def increase_priority_level(self):
        sel = self.selectedItems()
        for item in sel:
            if isinstance(item, Node):
                item.increase_priority_level()

    def decrease_priority_level(self):
        sel = self.selectedItems()
        for item in sel:
            if isinstance(item, Node):
                item.decrease_priority_level()

    def find_item(self, item):
        """
        Find item from this view
        Args:
            item(str or Node or ParameterNode): Accept name of the
            item(full name for parameter node) or item instance

        Returns:
            Node or ParameterNode: Found item
            None: No item found
        """
        for i in self.items():
            if isinstance(item, string_types):
                if i.type_name == 'node' and i.name == item:
                    return i
                if i.type_name == 'parameter' and i.full_name == item:
                    return i
            elif item == i:
                return i

    def load_data(self, data):
        self.clear()
        new_graph = True
        if data:
            if isinstance(data, string_types) and os.path.isfile(data):
                with open(data, 'r') as f:
                    data = json.load(f)

            graph_name = data.get('name')
            new_graph = False
            if not graph_name:
                logger.critical("Failed to find the name of the graph object")
                return
        else:
            data = {}
            graph_name = 'main'

        self.__graph = action_lib.create_graph(name=graph_name)
        if not new_graph:
            self.graph._set_data(data)
        self.populate_graph()
        return data

    def sync_ui_data(self):
        """
        This method will fetch ui data and cache it in each
        item in the current scene

        """
        parameter_node_pos = {}
        for item in self.items():
            if item.type_name == 'node':
                item.instance.ui_data['pos'] = [
                    item.pos().x(),
                    item.pos().y()
                ]
                item.instance.ui_data['LOD'] = item.current_priority
            elif item.type_name == 'parameter':
                parameter_node_pos[item.full_name] = [
                    item.pos().x(),
                    item.pos().y()
                ]
        self.graph.ui_data['parameter_node'] = parameter_node_pos

    def populate_graph(self):
        for node in self.__graph.iter_objects():
            obj = Node(node)
            self.addItem(obj)
            ui_data = obj.instance.ui_data
            if ui_data:
                pos = ui_data.get('pos')
                obj.setPos(*pos)
                lod = ui_data.get('LOD', 0)
                obj.update_priority_level(lod)
        self.init_connection_lines()

    def clear(self):
        super(NodeGraphScene, self).clear()
        self.pending_line = None
        self.connected_lines = list()
        self.hovered_items = list()

    def init_connection_lines(self):
        for item in self.items():
            if item.type_name == 'node':
                item.create_connection_lines()

    def copy_selected(self):
        selection = self.selectedItems()
        for i in selection:
            pass

    def toggle_bp_for_selected(self):
        items = self.selectedItems()
        for item in items:
            if item.type_name == 'node':
                item.toggle_pb()

    def node_items(self):
        """
        This method should return the top level items that determines the
         bounding box of the existing items in the graph view
        Returns:
            list: All the node items in this view
        """
        return [item for item in self.items() if item.type_name == 'node']

    # ============================================
    # Execution methods
    # ============================================

    def execute(self):
        manager.force_refreshing_view = True
        try:
            self.__graph.execute()
        except Exception as e:
            pass
        finally:
            manager.force_refreshing_view = False

    def step(self):
        self.__graph.execute(mode='step')

    def resume(self):
        manager.force_refreshing_view = True
        try:
            self.__graph.execute(mode='resume')
        except Exception as e:
            pass
        finally:
            manager.force_refreshing_view = False

    def reset_execution(self):
        self.__graph.reset_status('main')

    # =========================================
    # Override mouse events for line connection
    # =========================================
    def mouseMoveEvent(self, event):
        super(GraphicScene, self).mouseMoveEvent(event)
        if self.pending_line:
            self.pending_line.dragged(event)

    def mousePressEvent(self, event):
        self.hovered_items = list()
        if self.pending_line:
            self.pending_line.dropped()
        super(GraphicScene, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.hovered_items = list()
        if self.pending_line:
            self.pending_line.dropped()
        super(GraphicScene, self).mouseReleaseEvent(event)


