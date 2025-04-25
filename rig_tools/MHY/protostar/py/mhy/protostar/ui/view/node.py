import os
import logging

from mhy.qt.core.Qt import QtCore, QtGui, QtWidgets
from mhy.qt.icon_lib.api import get_pixmap
from mhy.protostar.ui.view.parameter_item import ParameterItemBase
from mhy.protostar.ui.config import Config
import mhy.protostar.ui.manager as manager
from mhy.protostar.constants import ExecStatus
from mhy.protostar.ui.view.socket import MainSocket

__all__ = ['Node', 'MainSocket']

logger = logging.getLogger(__name__)


class Node(QtWidgets.QGraphicsItem):

    """
    Base class for node graphic item
    As much as possible, everything is drawn in the node paint function for
    performance reasons
    """
    type_name = "node"

    __width = Config.Node.width
    title_font = QtGui.QFont()
    title_font.setPixelSize(Config.Font.title_font_size)
    title_font.setFamily(Config.Font.title_font_family)

    status_icons = {}

    def __init__(self, obj):
        """
        Initialize the instance with
        Args:
            obj(Action or Graph):

        """
        super(Node, self).__init__()
        self.__instance = obj

        self.source = self.__instance.type_name

        if self.source not in manager.pix_map_cache:
            icon_path = obj.icon_path
            if not os.path.isfile(icon_path):
                logger.warning("Failed to find icon "
                               "path: `{}`".format(icon_path))
            manager.pix_map_cache[self.source] = {
                'original': QtGui.QPixmap(obj.icon_path),
                'scaled': QtGui.QPixmap(obj.icon_path)
            }

        # Variables related to parameter priorities
        self.priorities = []
        self.current_priority = 0

        self.__status = ExecStatus.kNone
        self.__title_color = self.instance.ui_color

        self.is_collapsed = False

        self.init_tool_tip()

        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable |
            QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.init_icons()

        self.init_main_sockets()

        # Build input slots
        self.parameter_items = dict()
        self.__params = list()

        self.full_height = Config.Node.title_bar_height
        self.__height = self.full_height
        self.__reload_parameters()

        self.update_status('main', ExecStatus.kNone)

        self.__instance.status_changed.connect(self.update_status)

        if not self.is_graph:
            self.__instance.break_point_reached.connect(
                self.break_point_reached_cb)
        self.set_collapsed(Config.Node.default_collapsed)

    def __repr__(self):
        return self.name

    def init_icons(self):
        # Temporary put it here before figuring out the best way
        # to init icon for batch mode
        icon_map = {
            'error': ('/IOS/general/svg/close.svg',
                      Config.Color.title_color_failed),
            'running': ('/IOS/mail/svg/forward.svg',
                        Config.Color.title_color_running),
            'succeed': ('/IOS/general/svg/check_mark.svg',
                        Config.Color.title_color_succeed),
            'reference': ('/IOS/general/png/128/games_card_diamonds.png',
                          Config.Color.refrence_indicator
                          )
        }

        for n, v in icon_map.items():
            if n not in self.status_icons:
                self.status_icons[n] = get_pixmap(
                    sub_dir=v[0],
                    color=v[1]).scaled(
                    300,
                    300,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )

    def init_main_sockets(self):
        rect = QtCore.QRect(
            -Config.Node.main_socket_radius-Config.Node.spacing,
            Config.Node.title_bar_height + Config.Node.icon_bar_height/2 -Config.Node.main_socket_radius/2,
            Config.Node.main_socket_radius,
            Config.Node.main_socket_radius
        )
        self.input_socket = MainSocket(
            instance=self.instance,
            rect=rect,
            parent=self,
            is_output=False
        )

        rect = QtCore.QRect(
            Config.Node.width + Config.Node.spacing,
            Config.Node.title_bar_height + Config.Node.icon_bar_height/2 -Config.Node.main_socket_radius/2,
            Config.Node.main_socket_radius,
            Config.Node.main_socket_radius
        )
        self.output_socket = MainSocket(
            instance=self.instance,
            rect=rect,
            parent=self,
            is_output=True
        )

    def init_tool_tip(self):
        tool_tip = ''
        if self.is_reference:
            if self.is_graph:
                type_name = self.__instance.type_name
            else:
                type_name = self.__instance.graph.type_name

            tool_tip = '<p style="color:orange;">Reference [{}]</p>'.\
                format(type_name)

        if not self.is_graph:
            # self.__title_color = Config.Color.node_title_background
            self.__node_type = self.__instance.type_name
            tool_tip = tool_tip + '<p style="white-space: ' \
                                  'pre">{}</p>'.format(
                self.__instance.doc)
        else:
            # self.__title_color = Config.Color.graph_title_background
            self.__node_type = 'graph'
            tool_tip = tool_tip + \
                       "<p>Node graph(double click to spread contents</p>"
        self.setToolTip(tool_tip)

    @property
    def instance(self):
        return self.__instance

    @property
    def name(self):
        """Return the name of the action or graph
        """
        return self.instance.name

    @property
    def node_type(self):
        return self.__node_type

    @property
    def parameters(self):
        return self.__params

    @property
    def break_point_status(self):
        return self.instance.break_point.value

    @property
    def rect(self):
        margin = Config.Node.outline_width
        if self.is_collapsed:
            rect = QtCore.QRectF(
                -0.5 * margin - Config.Node.main_socket_radius,
                -0.5 * margin,
                self.width() + margin + 2*Config.Node.main_socket_radius,
                self.content_height() + Config.Node.title_bar_height + margin)
        else:
            rect = QtCore.QRectF(
                -0.5 * margin,
                -0.5 * margin,
                self.width() + margin,
                self.content_height() + Config.Node.title_bar_height + margin)

        return rect

    @property
    def is_graph(self):
        if not self.__instance:
            return False

        return self.__instance.is_graph

    @property
    def is_reference(self):
        if not self.__instance:
            return False
        if self.is_graph:
            return self.__instance.referenced
        else:
            return self.__instance.in_reference_graph

    def copy(self):
        """
        Make a copy of this item. Copy will not create connection on
        duplicated object
        Returns:

        """

        return

    def update_status(self, exec_name, stat):
        if exec_name != 'main':
            return
        self.__status = stat

        self.refresh_socket_tool_tip()

        # This is a hacky way to refresh viewport immediately,
        # need a better way to trigger refreshing
        if manager.force_refreshing_view:
            scene = self.scene()
            if scene:
                scene.views()[0].viewport().repaint()

            if self.__status == ExecStatus.kFail:
                manager.SignalManager.focus_on_item_signal.emit(self)

    def refresh_socket_tool_tip(self):
        for param in self.parameter_items.values():
            param.refresh_tool_tip()

    def break_point_reached_cb(self):
        manager.SignalManager.focus_on_item_signal.emit(self)

    def width(self):
        return self.__width

    def content_height(self):
        return self.full_height

    def destruct(self):
        for _, item in self.parameter_items.items():
            item.destruct()
        self.scene().removeItem(self)

    def break_connections(self):
        for _, item in self.parameter_items.items():
            item.break_connections()

    def get_param_item(self, parameter_name):
        return self.parameter_items.get(parameter_name)

    def set_collapsed(self, state):
        self.is_collapsed = state
        if state:
            self.update_priority_level(-10)
        else:
            self.update_priority_level(0)

    def update_action_name(self, new_name):
        self.__instance.name = new_name
        self.update()

    def __reload_parameters(self):
        # Remove current parameter items
        for item in self.parameter_items.values():
            item.destruct()

        self.__params = self.__instance.get_params(sort=True)
        # self.__params.sort(key=lambda a: a.is_output)
        self.parameter_items.clear()

        if not self.is_graph:
            color = Config.Color.node_color
        else:
            color = Config.Color.graph_color

        priorities = []
        idx = 0
        for param in self.parameters:
            if not param.ui_visible:
                # Skip param not visible on the ui
                continue
            priorities.append(param.priority)
            rect = QtCore.QRect(
                Config.Node.outline_width/2,
                Config.Node.title_bar_height +
                Config.Node.icon_bar_height + idx * Config.Node.section_height,
                self.width() - Config.Node.outline_width,
                Config.Node.section_height
            )
            param_item = ParameterItemBase(
                param,
                rect,
                parent=self,
                background_color=color)
            self.parameter_items[param.name] = param_item
            idx = idx + 1

        self.priorities = list(set(priorities))
        self.priorities.sort()

        self.prepareGeometryChange()
        self.full_height = \
            idx*Config.Node.section_height + \
            Config.Node.icon_bar_height + Config.Node.outline_width/2

        self.update_parameter_color(color)

        self.update_priority_level(self.current_priority)

    def update_priority_level(self, level):
        idx = 0
        for param in self.parameters:
            if not param.ui_visible:
                # Skip param not visible on the ui
                continue
            param_item = self.parameter_items.get(param.name)
            if not param_item:
                continue
            if level == -10\
                    or (level >= 0 and
                        (param.priority > level >= 0 or param.priority < 0)):
                param_item.set_collapsed(True)
                continue
            param_item.set_collapsed(False)
            rect = QtCore.QRect(
                Config.Node.outline_width/2,
                Config.Node.title_bar_height +
                Config.Node.icon_bar_height + idx * Config.Node.section_height,
                self.width() - Config.Node.outline_width,
                Config.Node.section_height
            )
            param_item.update_rect(rect)
            idx = idx + 1
        self.full_height = \
            idx*Config.Node.section_height + \
            Config.Node.icon_bar_height + Config.Node.outline_width/2

        self.current_priority = level

        if self.current_priority == -1:
            self.input_socket.hide()
            self.output_socket.hide()
        else:
            self.input_socket.show()
            self.output_socket.show()

        self.prepareGeometryChange()
        self.update()

    def increase_priority_level(self):
        level = self.offset_priority_level(False)
        self.update_priority_level(level)

    def decrease_priority_level(self):
        level = self.offset_priority_level(True)
        self.update_priority_level(level)

    def offset_priority_level(self, positive=True):
        """
        Offset the current priority level. level -10 means all
        parameter items are collapsed
        For example, the possible priorities are [-1, 0, 1, 2]
        default level will be 0.
        Moving at positive direction will get: 0, 1, 2, -1
        From level -1 moving negative direction will get -1, 2, 1, 0, -10


        Args:
            positive(bool):

        Returns:

        """
        current_level = self.current_priority
        if positive:
            if current_level == -1 or current_level == max(self.priorities):
                return -1
            for i in self.priorities:
                if i != -1 and i > current_level:
                    return i
        else:
            if current_level in [0, -10]:
                return -10
            for i in self.priorities[::-1]:
                if current_level < 0 <= i:
                    return i
                if 0 <= i < current_level:
                    return i
        return current_level

    def reload_parameters(self):
        self.__reload_parameters()
        self.create_connection_lines()

    def update_title_color(self, color):
        self.__title_color = color
        self.update()

    def update_parameter_color(self, color):
        for idx, item in enumerate(self.parameter_items.values()):
            if idx % 2:
                bg_color = QtGui.QColor(*color)
            else:
                bg_color = QtGui.QColor(*color).lighter(110)
            item.update_color(bg_color)

    def boundingRect(self):
        """Return a QRect that represents the bounding box of the node.
        Here that sould be the bounding box of the primary shape of the node.
        """
        return self.rect

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Re-implement paint method
        """
        if option.state & QtWidgets.QStyle.State_Selected:
            pen = QtGui.QPen(QtGui.QColor(*Config.Color.selected_frame),
                             Config.Node.outline_width)
            painter.setPen(pen)
        else:
            pen = QtGui.QPen(QtGui.QColor(*Config.Color.frame),
                             Config.Node.outline_width)
            painter.setPen(pen)

        # Set brush and pen, then start drawing
        color = QtGui.QColor(*self.__title_color)
        color.setAlpha(Config.Color.node_alpha)
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        rect = QtCore.QRectF(
            0,
            Config.Node.title_bar_height,
            self.width(),
            self.content_height())
        painter.drawRect(rect)

        alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        title_rect = QtCore.QRect(
            Config.Node.icon_bar_height,
            0,
            self.width() + Config.Node.icon_bar_height,
            Config.Node.title_bar_height)
        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        painter.setFont(self.title_font)
        painter.drawText(title_rect, alignment, self.name)

        pix = manager.pix_map_cache.get(self.source)
        if pix:
            pix = pix['scaled']
            if pix.height() == 0:
                ratio = 1
            else:
                ratio = pix.width()/pix.height()
            rect = QtCore.QRect(
                Config.Node.outline_width,
                Config.Node.title_bar_height,
                Config.Node.icon_bar_height*ratio,
                Config.Node.icon_bar_height)
            painter.drawPixmap(rect, pix)
        if not self.__status == ExecStatus.kNone:
            rect = QtCore.QRect(
                0,
                0,
                Config.Node.icon_bar_height,
                Config.Node.icon_bar_height)
            if self.__status == ExecStatus.kRunning:
                icon = self.status_icons['running']
                painter.drawPixmap(rect, icon)
            elif self.__status == ExecStatus.kSuccess:
                icon = self.status_icons['succeed']
                painter.drawPixmap(rect, icon)
            elif self.__status == ExecStatus.kFail:
                icon = self.status_icons['error']
                painter.drawPixmap(rect, icon)

        if self.is_reference:
            rect = QtCore.QRect(
                self.width() - Config.Node.icon_bar_height/2,
                Config.Node.title_bar_height + Config.Node.icon_bar_height/2-Config.Node.icon_bar_height/4,
                Config.Node.icon_bar_height/2,
                Config.Node.icon_bar_height/2)
            painter.drawPixmap(rect, self.status_icons['reference'])

        if self.break_point_status:
            rect = QtCore.QRect(
                0,
                Config.Node.title_bar_height + Config.Node.icon_bar_height / 2 - Config.Node.icon_bar_height / 4,
                Config.Node.icon_bar_height / 2,
                Config.Node.icon_bar_height / 2)
            painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))
            painter.drawEllipse(rect)

    def create_connection_lines(self):
        """
        This method will create connection lines based on
        internal backend data of each parameter.

        """
        for par in self.parameter_items.values():
            par.create_connection_lines()

    def mouseDoubleClickEvent(self, event):
        if self.is_graph:
            manager.SignalManager.tab_opened_signal.emit(self.instance)

    def find_parameter_item(self, param_name):
        return self.parameter_items.get(param_name)

    def toggle_pb(self):
        pb = self.instance.break_point.value
        self.instance.break_point.value = not pb
        self.update()

