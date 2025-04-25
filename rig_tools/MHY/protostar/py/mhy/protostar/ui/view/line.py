from mhy.qt.core.Qt import QtCore, QtGui, QtWidgets
import logging
import mhy.protostar.ui.manager as manager
from mhy.protostar.ui.config import Config
from mhy.protostar.core.exception import PConnectionError

logger = logging.getLogger(__name__)


class Line(QtWidgets.QGraphicsPathItem):
    type_name = "line"
    zero_area_object = True
    # Color
    pending_color = QtGui.QColor(*Config.Color.pending_line_color)
    expression_color = QtGui.QColor(*Config.Color.expression_override_param)
    connected_color = QtGui.QColor(*Config.Color.direct_connected_param)
    selection_color = QtGui.QColor(*Config.Color.selected_frame)

    # Pen
    pen = QtGui.QPen()
    pen.setWidth(2)

    def __init__(self,
                 start_point,
                 end_point,
                 scene,
                 source=None,
                 target=None,
                 is_exp_line=False):

        super(Line, self).__init__()
        self.__scene = scene
        self.__start_point = start_point
        self.__end_point = end_point
        self.__source = None
        self.__target = None
        self.__is_exp_line = is_exp_line

        self.source = source
        self.target = target

        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setBrush(QtCore.Qt.NoBrush)
        self.setAcceptHoverEvents(True)

        self.__is_hovered = False
        self.drag = False
        self.refresh_tool_tip()
        self.init_path()

    @property
    def is_connected(self):
        return bool(self.__target and self.__source)

    def init_path(self):
        if self.source:
            src_point = self.source.get_center()
        else:
            src_point = self.__start_point
        src_point = self.mapFromScene(src_point)

        if self.target:
            dst_point = self.target.get_center()
        else:
            dst_point = self.__end_point
        dst_point = self.mapFromScene(dst_point)

        dist_between = dst_point - src_point
        path = QtGui.QPainterPath()
        path.moveTo(src_point)
        path.cubicTo(
            src_point + QtCore.QPointF(dist_between.x() * 0.4, 0),
            dst_point - QtCore.QPointF(dist_between.x() * 0.4, 0),
            dst_point
        )
        self.setPath(path)

    def refresh_tool_tip(self):
        if self.source and self.target:
            self.setToolTip("{}[{}] -> {}[{}]".format(
                self.source.parameter.full_name,
                self.source.parameter.param_type,
                self.target.parameter.full_name,
                self.target.parameter.param_type
            )
            )
        else:
            self.setToolTip("")

    def destruct(self):
        if self.source and self in self.source.out_lines:
            self.source.out_lines.remove(self)
            self.source.update()
        if self.target:
            if self in self.target.in_lines:
                self.target.in_lines.remove(self)
                self.target.update()
            if self.__is_exp_line:
                for line in self.target.in_lines:
                    line.destruct()
        scene = self.scene()
        if scene:
            self.scene().removeItem(self)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton or\
                event.button() == QtCore.Qt.MiddleButton:
            self.setSelected(True)
            self.drag = True

    def update_path(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.start_point)
        dx = self.end_point.x() - self.start_point.x()
        dy = self.end_point.y() - self.start_point.y()
        ctrl1 = QtCore.QPointF(self.start_point.x() + dx * 0.25,
                               self.start_point.y() + dy * 0.1)

        ctrl2 = QtCore.QPointF(self.start_point.x() + dx * 0.75,
                               self.start_point.y() + dy * 0.9)
        path.cubicTo(ctrl1, ctrl2, self.end_point)
        self.setPath(path)

    def paint(self, painter, option, widget):
        self.init_path()

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        if not self.is_connected:
            color = self.pending_color
        elif option.state & QtWidgets.QStyle.State_Selected:
            color = self.selection_color

        elif self.__is_exp_line:
            color = self.expression_color
        else:
            color = self.connected_color

        # Set line style based on if is directly connected
        if self.is_connected and not self.__is_exp_line:
            self.pen.setStyle(QtCore.Qt.SolidLine)
        else:
            self.pen.setStyle(QtCore.Qt.DashLine)

        if self.__is_hovered:
            color = color.lighter(130)

        self.pen.setColor(color)
        self.setPen(self.pen)

        option.state = option.state & (not QtWidgets.QStyle.State_ReadOnly)
        super(Line, self).paint(painter, option, widget)

    def hoverEnterEvent(self, event):
        self.__is_hovered = True
        self.update()
        super(Line, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.__is_hovered = False
        self.update()
        super(Line, self).hoverLeaveEvent(event)

    def delete(self):
        if self.source:
            self.source.out_lines.remove(self)
        if self.target:
            self.target.in_lines.remove(self)
        if self in self.scene().connected_lines:
            self.scene().connected_lines.remove(self)
        self.scene().pending_line = False
        self.scene().removeItem(self)

    def check_connection(self):
        if self.source and self.target:
            return True
        return False

    def shape(self):
        return self.path()

    @property
    def start_point(self):
        return self.__start_point

    @start_point.setter
    def start_point(self, point):
        self.__start_point = point
        self.update_path()

    @property
    def end_point(self):
        return self.__end_point

    @end_point.setter
    def end_point(self, point):
        self.__end_point = point
        self.update_path()

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, widget):
        if self.__source is not None:
            if self.__source == widget:  # Source already connected
                return
            else:
                self.disconnect_source()
        else:
            self.__source = widget
            if self.__source is not None and \
                    self not in self.__source.out_lines:
                self.__source.out_lines.append(self)

            if self.__source and self.__target:
                if not self.is_parameter_connected(self.__source.parameter,
                                                   self.__target.parameter):
                    self.__source.parameter.connect(self.__target.parameter,
                                                    force=True)
        if self.target:
            self.target.parameter_item.refresh_status()
        self.refresh_tool_tip()
        self.update()

    def disconnect_source(self):
        if not self.__source:
            return
        if self.target:
            self.target.parameter.clear_script()
            self.target.parameter_item.refresh_status()

        if self in self.__source.out_lines:
            self.__source.out_lines.remove(self)
        self.__source = None

        self.update()

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, target_socket):
        if self.__target is not None:
            if self.__target == target_socket:
                return
            else:
                self.disconnect_target()
        else:
            self.__target = target_socket
            if self.__target is not None and self not in self.__target.in_lines:
                self.__target.in_lines.append(self)
            if self.__source and self.__target:
                if not self.is_parameter_connected(
                        self.__source.parameter, self.__target.parameter):
                    self.__source.parameter.connect(
                        self.__target.parameter, force=True)
        if self.target:
            self.target.parameter_item.refresh_status()
            target_owner = self.target.parameter.owner
            if target_owner.is_graph:
                manager.SignalManager.reload_graph_parameters_signal.emit(
                    target_owner)
        if self.__is_exp_line:
            target_socket.expression_override = True
        self.refresh_tool_tip()
        self.update()

    @staticmethod
    def is_parameter_connected(source, target):
        input_param = target.input_params
        for i in input_param:
            if i == source:
                return True
        return False

    def disconnect_target(self):
        """
        This method will disconnect the line from target and
        break the connection on the backend parameter instance

        """
        if not self.__target:
            return
        self.__target.parameter.clear_script()

        if self in self.__target.in_lines:
            self.__target.in_lines.remove(self)
        for line in self.__target.in_lines:
            if line != self:
                line.destruct()
        self.target.parameter_item.refresh_status()
        target_owner = self.target.parameter.owner
        if target_owner.is_graph:
            manager.SignalManager.reload_graph_parameters_signal.emit(
                target_owner
            )
        self.__target.expression_override=None
        self.__target.update()
        self.__target = None
        self.update()

    def update(self):
        if self.__target and self.__source:
            self.setZValue(-10)
        else:
            self.setZValue(10)
        super(Line, self).update()

    def dragged(self, event):
        scene = self.scene()
        if not scene:
            return
        items = self.scene().items(event.scenePos())

        items = [item for item in items if item.type_name == 'parameter' or
                 item.type_name == 'socket' and item.is_main_socket]

        snap = False
        sockets_list = []
        if items:
            item = items[0]
            if self.target is None:
                if item.type_name == 'parameter':
                    if item.input_socket:
                        self.end_point = item.input_socket.get_center()
                        sockets_list = [item.input_socket]
                        snap = True
                elif not item.is_output:
                    self.end_point = item.get_center()
                    sockets_list = [item]
                    snap = True
            elif self.source is None:
                if item.type_name == 'parameter':
                    if item.output_socket:
                        self.start_point = item.output_socket.get_center()
                        sockets_list = [item.output_socket]
                        snap = True
                elif item.is_output:
                    self.start_point = item.get_center()
                    sockets_list = [item]
                    snap = True

        if not snap:
            if self.target is None:
                point_b = event.scenePos()
                self.end_point = point_b
            else:
                point_a = event.scenePos()
                self.start_point = point_a

        self.scene().update_hovered_items(sockets_list)

    def dropped(self):
        scene = self.scene()
        if not scene:
            self.destruct()

        result = False

        if self.target is None and self.source:
            items = scene.items(scene.pending_line.end_point)
            socket = self.source
        elif self.source is None and self.target:
            items = scene.items(scene.pending_line.start_point)
            socket = self.target
        else:
            self.destruct()
            return

        items = [item for item in items if item.type_name == 'socket']
        for item in items:
            if item.is_main_socket:
                # Drop on main socket will popup a menu to target
                # connection to a specific socket
                return

            elif socket.is_connected_to(item):
                # If this socket is already connected
                # to this item, skip
                break

            elif socket.parentItem() == item.parentItem():
                # Avoid connection made from an output of a parameter to
                # the input of itself
                continue

            elif item.parameter.name == 'execution' and \
                    not manager.is_execution_type:
                # Execution parameter is only allowed to connect
                # to another execution parameter
                continue

            result = self.connect_to(item)
            break
        if not result:
            scene.pending_line = None
            self.destruct()

    def connect_to(self, item):
        """
        Connect this line to a given item
        Args:
            item(Socket): Try to connect the not connected end of this line
            to an item.

        Returns:
            bool: If succeed

        """
        if not item:
            return False

        if self.target is None and not item.is_output and self.source:
            if not self.check_compatible(
                    self.source.parameter,
                    item.parameter):
                return False
            try:
                self.target = item
                self.scene().pending_line = None
                item.update()
                return True
            except PConnectionError:
                return False

        elif self.source is None and item.is_output and self.target:
            if not self.check_compatible(
                    item.parameter, self.target.parameter):
                return False
            try:
                self.source = item
                self.scene().pending_line = None
                item.update()
                return True
            except PConnectionError:
                return False
        return False

    @staticmethod
    def check_compatible(source, destination):
        """
        Check if 2 parameters are compatible to connect
        Args:
            source(Parameter):
            destination(Parameter):

        Returns:
            bool: If compatible
        """
        if not source.is_compatible(destination):
            logger.warning(
                "{} is not compatible with {}, abort"
                " connection.".format(source,
                                      destination))
            return False
        return True
