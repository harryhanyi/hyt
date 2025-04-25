"""
Parameter socket class
"""

from mhy.qt.core.Qt import QtWidgets,  QtCore, QtGui

from mhy.protostar.ui.config import Config
from mhy.protostar.ui.view.line import Line
import mhy.protostar.ui.manager as manager


class SocketBase(QtWidgets.QGraphicsWidget):
    type_name = 'socket'
    is_main_socket = False
    __radius = 4.5
    __diameter = 2 * __radius
    __color = QtGui.QColor(171, 170, 160, 255)

    # Brush.
    brush = QtGui.QBrush()
    brush.setStyle(QtCore.Qt.SolidPattern)

    # Pen.
    pen = QtGui.QPen()
    pen.setColor(QtGui.QColor(20, 20, 20, 0))

    # Color
    pending_color = QtGui.QColor(*Config.Color.pending_line_color)
    connected_color = QtGui.QColor(*Config.Color.direct_connected_param)
    expression_color = QtGui.QColor(*Config.Color.expression_override_param)
    in_use_color = QtGui.QColor(*Config.Color.in_use_socket_color)

    def __init__(self, rect, parent, is_output):
        super(SocketBase, self).__init__(parent=parent)
        self.rect = rect
        self.is_output = is_output
        self.setAcceptHoverEvents(True)
        self.hovered = False

    def get_center(self):
        """
        Get the center point of this socket item
        Returns:
            QtCore.QPointF
        """
        rect = self.boundingRect()
        center = QtCore.QPointF(
            rect.x() + rect.width() / 2,
            rect.y() + rect.height() / 2
        )

        center = self.mapToScene(center)
        return center

    def boundingRect(self):
        return QtCore.QRectF(self.rect)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def update_rect(self, rect):
        self.rect = rect

    def start_pending_line(self, parameter, mouse_pos):
        manager.accepted_socket_type = parameter.param_type
        manager.is_execution_type = (parameter.name == 'execution')
        if self.is_output:
            rect = self.boundingRect()
            point_a = QtCore.QPointF(
                rect.x() + rect.width() / 2, rect.y() + rect.height() / 2)
            point_a = self.mapToScene(point_a)
            point_b = self.mapToScene(mouse_pos)
            self.new_line = Line(
                point_a,
                point_b,
                self.scene(),
                source=self,
                target=None)
            self.scene().addItem(self.new_line)
            self.scene().pending_line = self.new_line
        else:
            rect = self.boundingRect()
            point_a = self.mapToScene(mouse_pos)
            point_b = QtCore.QPointF(
                rect.x() + rect.width() / 2,
                rect.y() + rect.height() / 2)
            point_b = self.mapToScene(point_b)

            self.new_line = Line(
                point_a,
                point_b,
                self.scene(),
                source=None,
                target=self)
            self.scene().addItem(self.new_line)
            self.scene().pending_line = self.new_line
        self.update()


class Socket(SocketBase):

    def __init__(self, param, rect, parent, is_output):
        super(Socket, self).__init__(
            rect=rect,
            parent=parent,
            is_output=is_output
        )
        self.__param = param
        self.expression_override = False
        self.execution_path = QtGui.QPainterPath()
        self.update_rect(rect)

        # Lines.
        self.new_line = None
        self.out_lines = []
        self.in_lines = []

        self.refresh_tool_tip()

    def __repr__(self):
        if self.is_output:
            socket_name = "OutputSocket"
        else:
            socket_name = "InputSocket"
        return "<Protostar.{0} {1}: '{2}' at <{3}>>".format(
            socket_name,
            self.__class__.__name__,
            self.__param.full_name,
            hex(id(self)))

    def update_rect(self, rect):
        super(Socket, self).update_rect(rect)
        if self.is_execution_socket:
            self.execution_path = QtGui.QPainterPath()

            if self.is_output:
                self.execution_path.moveTo(rect.x(), rect.y())
                self.execution_path.lineTo(rect.x(), rect.y()+rect.height())
                self.execution_path.lineTo(
                    rect.x() + rect.width(),
                    rect.y() + rect.height()/2)
                self.execution_path.lineTo(rect.x(), rect.y())
            else:
                self.execution_path.moveTo(rect.x()+rect.width(), rect.y())
                self.execution_path.lineTo(
                    rect.x() + rect.width(),
                    rect.y() + rect.height())
                self.execution_path.lineTo(
                    rect.x(),
                    rect.y() + rect.height() / 2)
                self.execution_path.lineTo(rect.x()+rect.width(), rect.y())
        self.prepareGeometryChange()
        self.update()

    def refresh_tool_tip(self):
        value = ""
        # Just make sure any error happens in parameter value query,
        # the ui won't crash
        try:
            value = self.__param.value
        except Exception:
            pass

        tool_tip = "<b>{}Value:</b> {}".format(
            self.parameter,
            value)
        self.setToolTip(tool_tip)

    def to_node(self):
        return self.parentItem().parentItem()

    def shape(self):
        path = QtGui.QPainterPath()
        if self.is_execution_socket:
            return self.execution_path
        else:
            path.addEllipse(self.boundingRect())
        return path

    @property
    def is_connected(self):
        return bool(self.out_lines or self.in_lines)

    @property
    def is_execution_socket(self):
        return self.__param.name == 'execution'

    @property
    def parameter(self):
        return self.__param

    @property
    def parameter_item(self):
        """
        Return to the parent parameter item of this socket
        Returns:

        """
        return self.parentItem()

    def is_supported(self):
        if manager.is_execution_type and self.is_execution_socket:
            return True
        if manager.accepted_socket_type == self.parameter.param_type:
            return True
        return False

    def destruct(self):
        for line in self.out_lines:
            line.destruct()
        for line in self.in_lines:
            line.destruct()

    def break_connections(self):
        for line in self.out_lines:
            line.disconnect_target()
            line.destruct()
        for line in self.in_lines:
            line.disconnect_source()
            line.destruct()

    def is_connected_to(self, socket):
        """
        Check if this socket is connect to another socket
        Args:
            socket:

        Returns:

        """
        for line in self.out_lines:
            if line.target == socket:
                return True
        for line in self.in_lines:
            if line.source == socket:
                return True
        return False

    def mousePressEvent(self, event):
        self.start_pending_line(self.__param, event.pos())

    def paint(self, painter, option, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        if self.is_output:
            if self.is_connected:
                color = self.in_use_color
            else:
                color = self.pending_color
        else:
            if not self.is_connected:
                color = self.pending_color
            elif self.expression_override:
                color = self.expression_color
            else:
                color = self.connected_color

        if self.scene().pending_line and not self.is_supported() \
                and self in self.scene().hovered_items:
            color = QtGui.QColor(color.red(), color.green(), color.blue(), 80)
        elif self.hovered or self in self.scene().hovered_items:
            color = color.lighter(180)

        self.brush.setColor(color)
        painter.setBrush(self.brush)

        painter.setPen(self.pen)

        if not self.is_execution_socket:
            painter.drawEllipse(self.rect)
        else:
            painter.fillPath(self.execution_path, color)

    def get_center(self):
        """
        Get the center point of this socket item
        Returns:
            QtCore.QPointF
        """
        parameter_item = self.parentItem()
        node = self.to_node()
        if node and parameter_item and parameter_item.collapsed:
            if self.is_output:
                return node.output_socket.get_center()
            else:
                return node.input_socket.get_center()
        else:
            rect = self.boundingRect()
            center = QtCore.QPointF(
                rect.x() + rect.width() / 2,
                rect.y() + rect.height() / 2
            )

            center = self.mapToScene(center)
            return center

    # =======
    # Colors
    # =======
    def get_color(self):
        return self.__color

    def set_color(self, color):
        self.__color = color
        self.update()

    def create_connection_line_to(self, target_socket, is_exp_line=False):
        """
        This method will create a line between this socket
         and target socket. This method only affect ui items,
         it won't change status of the protosar parameter
        on the backend
        Args:
            target_socket:
            is_exp_line: If connection line indicating expression dependency

        Returns:

        """
        if not target_socket:
            return
        new_line = Line(
            self.get_center(),
            target_socket.get_center(),
            self.scene(),
            source=self,
            target=target_socket,
            is_exp_line=is_exp_line
        )

        self.scene().connected_lines.append(new_line)
        self.scene().addItem(new_line)


class MainSocket(SocketBase):
    is_main_socket = True

    pending_color = QtGui.QColor(*Config.Color.main_socket_color)

    def __init__(self, instance, rect, parent, is_output):
        super(MainSocket, self).__init__(
            rect=rect,
            parent=parent,
            is_output=is_output
        )
        self.__instance = instance
        self.menu = None

    @property
    def instance(self):
        return self.__instance

    def paint(self, painter, option, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        color = QtGui.QColor(self.pending_color)
        if self.hovered or self in self.scene().hovered_items:
            color = color.lighter(180)
        self.brush.setColor(color)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(self.rect)

    def mousePressEvent(self, event):
        self.show_context_menu()
        super(MainSocket, self).mousePressEvent(event)

    def show_context_menu(self):
        """
        Popup menu action for browsing and create action or
        graph from library

        """
        scene = self.scene()
        if not scene:
            return

        view = scene.views()[0]
        if not self.menu:
            self.menu = QtWidgets.QMenu(view)
            lib_action = QtWidgets.QWidgetAction(self)
            self.list_widget = ParameterListWidget(self.menu)
            lib_action.setDefaultWidget(self.list_widget)
            self.menu.addAction(lib_action)
            self.list_widget.itemClicked.connect(
                self.create_line_cb)

        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        params = self.instance.get_params()
        params = [i for i in params if i.ui_visible]
        if not self.is_output:
            params = [i.name for i in params if i.ui_visible]
        else:
            params = [i.name for i in params if i.ui_visible and not i.is_output]

        self.list_widget.addItems(params)
        self.list_widget.blockSignals(False)
        self.menu.exec_(QtGui.QCursor.pos())

    def create_line_cb(self):
        current_item = self.list_widget.currentItem()
        target_socket = None
        param_item = None
        if current_item:
            parent = self.parentItem()
            param_name = current_item.data(QtCore.Qt.DisplayRole)
            param_item = parent.find_parameter_item(param_name)
            if param_item:
                if self.is_output:
                    target_socket = param_item.output_socket
                else:
                    target_socket = param_item.input_socket

        if self.scene().pending_line:
            active_line = self.scene().pending_line
            active_line.connect_to(target_socket)

        elif param_item and target_socket:
            # Why QGraphicsWidget doesn't have map from global method?
            # Have to do it all they way from view to scene to widget local
            view = self.scene().views()[0]
            mouse_pos = QtGui.QCursor().pos()
            view_pos = view.mapFromGlobal(mouse_pos)
            scene_pos = view.mapToScene(view_pos)
            local_pos = target_socket.mapFromScene(scene_pos)
            target_socket.start_pending_line(
                param_item.parameter,
                local_pos)

        self.menu.close()


class ParameterListWidget(QtWidgets.QListWidget):
    pass
