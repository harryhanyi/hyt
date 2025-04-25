"""
This module create graphic widgets item for different type of parameters

"""
from mhy.qt.core.Qt import QtCore, QtGui, QtWidgets
import mhy.protostar.constants as const
from mhy.protostar.ui.config import Config
from mhy.protostar.ui.view.socket import Socket
import logging
import random

logger = logging.getLogger(__name__)


class ParameterItemBase(QtWidgets.QGraphicsWidget):
    _null_pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
    type_name = 'parameter'
    is_nested = True
    font = QtGui.QFont()
    font.setPixelSize(Config.Font.parameter_font_size)
    font.setFamily(Config.Font.title_font_family)

    class Status(object):
        standard = 0
        connected = 1
        expression_override = 2
        dynamic = 3
        locked = 4

    def __init__(self,
                 param,
                 rect,
                 parent=None,
                 background_color=QtGui.QColor(128, 128, 128)
                 ):
        super(ParameterItemBase, self).__init__(parent=parent)
        self.__param = param
        self.collapsed = False
        self.__rect = QtCore.QRect()
        self.__text_rect = QtCore.QRect()
        self.__rect = rect
        self.__text_rect = QtCore.QRect(
            self.__rect.x() + Config.Node.socket_radius + Config.Node.spacing,
            self.__rect.y(),
            self.__rect.width() - 2 * (Config.Node.socket_radius +
                                       Config.Node.spacing),
            self.__rect.height())

        self.color = background_color

        self.__input_socket = None
        self.__output_socket = None

        self.__status = ParameterItemBase.Status.standard
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.set_parameter(param)
        self.refresh_status()

    def __repr__(self):
        return self.__param.full_name

    @property
    def input_socket(self):
        return self.__input_socket

    @property
    def output_socket(self):
        return self.__output_socket

    def update_rect(self, rect):
        self.__rect = rect
        self.__text_rect = QtCore.QRect(
            self.__rect.x() + Config.Node.socket_radius + Config.Node.spacing,
            self.__rect.y(),
            self.__rect.width() - 2 * (Config.Node.socket_radius +
                                       Config.Node.spacing),
            self.__rect.height())
        self.set_parameter(self.parameter)
        self.prepareGeometryChange()
        self.update()

    def set_collapsed(self, stat):
        if stat:
            self.hide()
            self.collapsed = True
        else:
            self.show()
            self.collapsed = False

    def refresh_status(self):
        state_str = ""
        expression_str = ""
        if self.parameter.has_direct_input:
            self.__status = ParameterNode.Status.connected
            state_str = 'connected'
        elif self.parameter.has_input:
            self.__status = ParameterNode.Status.expression_override
            expression_str = self.parameter.script.code

            state_str = 'expression'
        elif self.parameter.is_dynamic:
            self.__status = ParameterNode.Status.dynamic
            state_str = 'dynamic'
        elif not self.parameter.editable:
            self.__status = ParameterNode.Status.locked
            state_str = 'locked'
        else:
            self.__status = ParameterNode.Status.standard

        if state_str:
            tool_tip = "<p><b>[{}]</b>({})<p>".format(
                self.__param.param_type,
                state_str)
        else:
            tool_tip = "<p><b>[{}]</b><p>".format(
                self.__param.param_type)

        if self.parameter.doc:
            tool_tip = tool_tip + \
                       '<p style="white-space: pre">{}</p>'.format(
                           self.parameter.doc
                       )

        if expression_str:
            tool_tip = tool_tip +\
                       '<p style="color:orange;">{}</p>'.format(
                           expression_str
                       )
        self.setToolTip(tool_tip)
        self.refresh_tool_tip()
        self.update()

    @property
    def status(self):
        return self.__status

    def refresh_tool_tip(self):
        if self.input_socket:
            self.input_socket.refresh_tool_tip()

        if self.output_socket:
            self.output_socket.refresh_tool_tip()

    def destruct(self):
        if self.__input_socket:
            self.__input_socket.destruct()
        if self.__output_socket:
            self.__output_socket.destruct()

    def update_color(self, color):
        self.color = color
        self.update()

    @property
    def name(self):
        if self.__param:
            return self.__param.name
        return ''

    @property
    def full_name(self):
        if self.__param:
            return self.__param.full_name
        return ''

    @property
    def parameter(self):
        return self.__param

    @property
    def is_execution_parameter(self):
        return self.parameter.name == 'execution'

    @property
    def ui_name(self):
        return self.parameter.ui_label

    @property
    def sockets(self):
        return self.input_socket, self.output_socket

    @property
    def rect(self):
        return self.__rect

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def boundingRect(self):
        return QtCore.QRectF(self.rect)

    def set_parameter(self, parameter):
        if not self.is_nested or\
                (not parameter.is_output and \
                 parameter.name != const.SELF_PARAM_NAME):
            rect = QtCore.QRect(
                Config.Node.margin[0] + Config.Node.outline_width/2,
                self.__rect.height()/2 - Config.Node.socket_radius / 2 +
                self.__rect.y(),
                Config.Node.socket_radius,
                Config.Node.socket_radius
            )
            if self.input_socket is None:
                self.__input_socket = Socket(
                    parameter, rect, parent=self, is_output=False)
            else:
                self.input_socket.update_rect(rect)

        rect = QtCore.QRect(
            self.__rect.width() + Config.Node.outline_width/2 - Config.Node.socket_radius -
            Config.Node.margin[1],
            self.__rect.height() / 2 - Config.Node.socket_radius / 2 + self.__rect.y(),
            Config.Node.socket_radius,
            Config.Node.socket_radius)

        if self.output_socket is None:
            self.__output_socket = Socket(
                parameter, rect, parent=self, is_output=True)
        else:
            self.output_socket.update_rect(rect)

    def paint(self, painter, option, widget=None):
        if self.hovered:
            color = self.color.lighter(130)
        else:
            color = self.color
        color.setAlpha(Config.Color.node_alpha)
        painter.setBrush(QtGui.QBrush(color))

        self.set_frame_pen(option, painter)
        painter.drawRect(self.rect)

        if self.status == ParameterItemBase.Status.standard:
            painter.setPen(QtGui.QPen(QtCore.Qt.white))
        elif self.status == ParameterItemBase.Status.connected:
            painter.setPen(
                QtGui.QPen(
                    QtGui.QColor(*Config.Color.direct_connected_param)
                )
            )
        elif self.status == ParameterItemBase.Status.expression_override:
            painter.setPen(
                QtGui.QPen(
                    QtGui.QColor(*Config.Color.expression_override_param)
                )
            )
        elif self.status == ParameterItemBase.Status.dynamic:
            painter.setPen(QtGui.QPen(QtCore.Qt.white))
        elif self.status == ParameterItemBase.Status.locked:
            painter.setPen(QtGui.QPen(QtCore.Qt.white))

        alignment = self.get_text_alignment()
        if self.parameter.name != 'execution':
            # skip drawing text on execution parameter item
            painter.setFont(self.font)
            painter.drawText(
                self.__text_rect,
                alignment,
                self.ui_name)

    def set_frame_pen(self, option, painter):
        painter.setPen(self._null_pen)

    def get_text_alignment(self):
        if self.parameter.is_output or \
           self.parameter.name == const.SELF_PARAM_NAME:
            alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
        else:
            alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        return alignment

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def break_connections(self, source=True, destinations=True):
        if source and self.input_socket:
            self.input_socket.break_connections()
        if destinations and self.output_socket:
            self.output_socket.break_connections()

    def remove_connected_lines(self, source=True, destinations=False):
        """
        Remove connected lines
        Returns:

        """
        if source and self.input_socket:
            self.input_socket.destruct()
        if destinations and self.output_socket:
            self.output_socket.destruct()

    def rebuild_connections(self, source=True, destinations=False):
        self.remove_connected_lines(source=source, destinations=destinations)
        self.create_connection_lines(source=source, destinations=destinations)

    def create_connection_lines(self, source=True, destinations=False):
        if source:
            self.__create_input_lines()
        if destinations:
            self.__create_output_lines_to_graph()

    def __create_input_lines(self):
        current_graph = self.scene().graph
        inputs = list()
        exp = False
        if not self.parameter.has_direct_input:
            exp = True

        if self.input_socket:
            inputs = self.parameter.input_params
        for src in inputs:
            src_owner = src.owner
            if current_graph == src_owner:
                # If the owner of source parameter is the graph of this
                # scene. Try to build connection from parameter node to
                # the input socket of this parameter
                param_item = self.scene().find_item(src.full_name)
                if not param_item:
                    # Create parameter node if necessary
                    param_item = self.scene().add_parameter_node(src)
                    item_pos = self.parentItem().pos()

                    width = param_item.rect.width()
                    item_pos = item_pos + QtCore.QPoint(
                        random.uniform(-2*width, -1*width),
                        random.uniform(-30, 30))

                    param_item.setPos(item_pos)

            else:
                node_item = self.scene().find_item(src.owner.name)
                if not node_item:
                    # Owner node item is in this scene
                    continue
                param_item = node_item.get_param_item(src.name)
            if not param_item:
                continue

            if not param_item.output_socket.is_connected_to(self.input_socket):
                param_item.output_socket.create_connection_line_to(
                    self.input_socket, is_exp_line=exp)

    def __create_output_lines_to_graph(self):
        current_graph = self.scene().graph
        outputs = list()
        if self.output_socket:
            outputs = self.parameter.output_params
        for output in outputs:
            is_exp_line = False
            if not output.has_direct_input:
                is_exp_line = True
            dest_owner = output.owner
            if current_graph == dest_owner:
                # If the owner of source parameter is the graph of this
                # scene. Try to build connection from parameter node to
                # the input socket of this parameter
                param_item = self.scene().find_item(output.full_name)
                if not param_item:
                    # Create parameter node if necessary
                    param_item = self.scene().add_parameter_node(output)
                    item_pos = self.parentItem().pos()

                    item_pos = item_pos + QtCore.QPoint(
                        self.rect.width() + random.uniform(10, 20),
                        random.uniform(-30, 30)
                    )
                    param_item.setPos(item_pos)

            else:
                node_item = self.scene().find_item(dest_owner.name)
                if not node_item:
                    # Owner node item is in this scene
                    continue
                param_item = node_item.get_param_item(output.name)
            if not param_item:
                continue

            if not self.output_socket.is_connected_to(param_item.input_socket):
                self.output_socket.create_connection_line_to(
                    param_item.input_socket,
                    is_exp_line=is_exp_line
                )


class ParameterNode(ParameterItemBase):
    is_nested = False

    def __init__(self, param):
        rect = QtCore.QRect(
            Config.Node.outline_width/2,
            0,
            200,
            Config.Node.parameter_node_height
        )
        super(ParameterNode, self).__init__(
            param=param,
            rect=rect,
            background_color=QtGui.QColor(*Config.Color.parameter_node_color)
        )
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable |
            QtWidgets.QGraphicsItem.ItemIsSelectable)

    def destruct(self):
        super(ParameterNode, self)
        self.scene().removeItem(self)

    @property
    def ui_name(self):
        return self.parameter.ui_label

    def set_frame_pen(self, option, painter):
        if option.state & QtWidgets.QStyle.State_Selected:
            pen = QtGui.QPen(QtGui.QColor(*Config.Color.selected_frame),
                             Config.Node.outline_width)
            painter.setPen(pen)
        else:
            pen = QtGui.QPen(QtGui.QColor(*Config.Color.frame),
                             Config.Node.outline_width)
            painter.setPen(pen)

    def boundingRect(self):
        rect = self.rect
        margin_width = Config.Node.outline_width/2
        margins = QtCore.QMargins(
            margin_width,
            margin_width,
            margin_width,
            margin_width
        )
        rect = rect.marginsAdded(margins)
        return QtCore.QRectF(rect)
