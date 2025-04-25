"""
This is a view for picker items
"""
import six
import os
import json
from PySide2 import QtGui, QtCore, QtWidgets

import maya.OpenMaya as OpenMaya

import mhy.maya.animtools.picker_manager.ui.manager as manager
import mhy.qt.core.widgets.node_graph as ng
from mhy.maya.nodezoo.node import Node
import mhy.maya.animtools.picker_manager.node.viewport_picker as vp
import mhy.maya.animtools.picker_manager.api.pickers as picker_api


def _load_picker_shapes():
    """
    This method get the shape data based on environment var which
    is sync with the plugin source code
    Returns:
        dict: A dictionary mapped from shape name to draw data
    """
    result = {}
    resource_env = os.environ.get('MHY_RESOURCE_PATH')
    for root in resource_env.split(';'):
        shape_path = os.path.join(root, 'picker_shapes')
        if os.path.isdir(shape_path):
            for i in os.listdir(shape_path):
                full_path = os.path.join(shape_path, i)
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    name = data.get('name')
                    if name:
                        result[name] = data.get('shapes')
    return result


class ItemBase(QtWidgets.QGraphicsItem):
    """
    The base class of picker graphic item
    """
    brush = QtGui.QBrush()
    brush.setStyle(QtCore.Qt.SolidPattern)

    empty_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    # Pen.
    pen = QtGui.QPen()
    pen.setColor(QtGui.QColor(20, 20, 20, 0))

    empty_pen = QtGui.QPen()
    empty_pen.setColor(QtGui.QColor(20, 20, 20, 0))

    def __init__(self):
        super(ItemBase, self).__init__()
        self.node = None
        self.name = None
        self.is_hidden = False

    def init_from_data(self, data, namespace=None):
        self.name = data.get('name')
        if namespace:
            self.name = namespace + ':' + self.name
        self.node = Node(self.name)
        self.update_internal_data(data)

    def init_from_node(self, node):
        if isinstance(node, six.string_types):
            node = Node(node)
        self.node = node
        self.name = node.name
        data = self.node.export()
        self.update_internal_data(data)

    def refresh_state(self):
        self.init_from_node(self.node)

    def boundingRect(self):
        return QtCore.QRectF(self.rect)

    def update_internal_data(self, data=None):
        if self.scene():
            self.scene().update()


class TextItemBase(QtWidgets.QGraphicsWidget):
    text_pen = QtGui.QPen()
    text_pen.setColor(QtCore.Qt.white)

    def __init__(self, parent, font_size=36):
        super(TextItemBase, self).__init__(parent=parent)
        self.rect = QtCore.QRectF()
        self.__text = ""
        self.font = QtGui.QFont()
        self.font.setPixelSize(font_size)
        self.text_color = QtCore.Qt.white
        self.alpha = 1.0

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.rect)
        return path

    def set_text(self, text):
        self.__text = text
        self.update()

    def set_rect(self, rect):
        self.rect = rect
        self.prepareGeometryChange()
        self.update()

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.update()

    def paint(self, painter, option, widget=None):
        """Re-implement paint method
        """
        self.text_pen.setColor(self.text_color)
        painter.setPen(self.text_pen)
        painter.setFont(self.font)

        alignment = QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft
        painter.drawText(self.rect, alignment, self.__text)


class ContainerItem(ItemBase):
    """
    This is container item class that will draw a back ground image behind
    picker items
    """

    def __init__(self):
        super(ContainerItem, self).__init__()
        self.image = ""
        self.rect = QtCore.QRectF()
        self.alpha = 0
        self.frame_pen = QtGui.QPen(QtGui.QColor(122, 182, 255, 160))
        self.frame_pen.setWidth(3)
        self.active_sel_text = ""
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)

        self.namespace_item = TextItemBase(font_size=36, parent=self)
        self.selection_item = TextItemBase(font_size=18, parent=self)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.scene():
            if self.node:
                self.node.set_picker_position([value.x(), -1*value.y()])

        return super(ContainerItem, self).itemChange(change, value)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def boundingRect(self):
        unit_rect = self.rect.united(self.namespace_item.rect).\
            united(self.selection_item.rect)
        return unit_rect

    def update_internal_data(self, data):
        pos = data.get('position', (0, 0))
        self.setPos(pos[0], -1 * pos[1])
        self.image = data.get('image_path', '')
        width = data.get('width', 0)
        height = data.get('height', 0)

        color = data.get('containerTextColor', [1.0, 1.0, 1.0])
        text_color = QtGui.QColor(255*color[0], 255*color[1], 255*color[2])
        self.namespace_item.text_color = text_color
        self.selection_item.text_color = text_color

        self.rect = QtCore.QRectF(-0.5*width, -0.5*height, width, height)
        rect = QtCore.QRectF(-0.5*width+150, -0.5*height, 500, 80)
        self.namespace_item.set_rect(rect)
        if ':' in self.name:
            self.namespace_item.set_text(self.name.split(':')[0])
        else:
            self.namespace_item.set_text("")
        rect = QtCore.QRectF(0.5*width-350, -0.5*height, 750, 80)
        self.selection_item.set_rect(rect)
        self.alpha = data.get('alpha', 1)
        self.namespace_item.set_alpha(self.alpha)
        self.selection_item.set_alpha(self.alpha)
        self.prepareGeometryChange()
        super(ContainerItem, self).update_internal_data()

    def set_active_selection(self, to_sel):
        if not to_sel:
            active_sel_text = ""
        elif len(to_sel) > 1:
            active_sel_text = "... {} items".format(len(to_sel))
        else:
            active_sel_text = to_sel[0].name
        self.selection_item.set_text(active_sel_text)
        self.update()

    def paint(self, painter, option, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        source = QtCore.QRectF(0.0, 0.0, 1000, 1000)
        pixmap = QtGui.QPixmap(self.image)
        painter.setPen(self.empty_pen)
        painter.setOpacity(self.alpha)
        painter.drawPixmap(self.rect, pixmap, source)


class PickerItem(ItemBase):
    shape_map = _load_picker_shapes()

    def __init__(self):
        super(PickerItem, self).__init__()
        self.ui_type = 'circle'
        self.rotate = 0
        self.draw_data = None
        self.is_filled = False
        self.line_width = 2

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self.sel_paths = []
        self.sel_areas = []

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.scene():
            if self.node:
                self.node.set_picker_position([value.x(), -1*value.y()])
        return super(PickerItem, self).itemChange(change, value)

    def update_internal_data(self, data):
        self.ui_type = data.get('uiType', 'circle')
        self.rotate = data.get('rotate', 0)

        if self.ui_type not in ['circle', 'rect']:
            self.setRotation(-1*self.rotate)

        if self.ui_type == 'circle':
            radius = self.node.get_radius()
            self.rect = QtCore.QRect(-0.5 * radius, -0.5 * radius, radius, radius)
        elif self.ui_type == 'rect':
            width = data.get('width', 0)
            height = data.get('height', 0)
            self.rect = QtCore.QRect(-0.5 * width, -0.5 * height, width, height)
        else:
            width = data.get('width', 0)
            height = data.get('height', 0)
            draw_data = self.shape_map.get(self.ui_type)
            self.rect = QtCore.QRect(-0.5 * width, -0.5 * height, width, height)

            if draw_data:
                points_list = list()
                tmp_data_list = []
                for item_shape in draw_data:
                    tmp_data = dict()
                    wire_frame_data = item_shape.get('wireframe')
                    if wire_frame_data:
                        wire_frame_data = [[width*i[0]*0.5, -0.5*height*i[1]] for i in wire_frame_data]
                        points_list.extend(wire_frame_data)
                        tmp_data['wireframe'] = wire_frame_data

                    shaded_data = item_shape.get('shaded')
                    if shaded_data:
                        shaded_data = [[width * 0.5 * i[0], -0.5*height * i[1]] for i in shaded_data]
                        points_list.extend(shaded_data)
                        tmp_data['shaded'] = shaded_data

                    if tmp_data:
                        tmp_data_list.append(tmp_data)
                self.rect = self.get_bounding_box(points_list)
                self.draw_data = tmp_data_list

        self.is_filled = data.get('is_filled', True)
        self.line_width = data.get('line_width', 2)
        color = data.get('color', [1.0, 1.0, 1.0])
        color = [i * 255 for i in color]
        high_color = data.get('hiColor', [1.0, 1.0, 1.0])
        high_color = [i * 255 for i in high_color]
        alpha = 255 * data.get('alpha', 1.0)
        self.color = QtGui.QColor(color[0], color[1], color[2], alpha)
        self.high_light_color = QtGui.QColor(high_color[0], high_color[1], high_color[2], alpha)
        self.brush.setColor(QtGui.QColor(color[0], color[1], color[2], alpha))
        self.pen.setColor(QtGui.QColor(color[0], color[1], color[2], alpha))
        self.pen.setWidth(self.line_width)
        pos = data['position']
        self.setPos(pos[0], -1 * pos[1])
        super(PickerItem, self).update_internal_data()
        self.setToolTip(self.name)

    def shape(self):
        path = QtGui.QPainterPath()
        if self.ui_type == 'rect':
            path.addRect(self.boundingRect())
        elif self.ui_type == 'circle':
            path.addEllipse(self.boundingRect())
        else:
            path.addRect(self.rect)
        return path

    def paint(self, painter, option, widget):
        if not manager.show_hidden_pickers and self.is_hidden:
            return
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        painter.setPen(self.empty_pen)

        if self.isSelected():
            self.brush.setColor(self.high_light_color)
            self.pen.setColor(self.high_light_color)
        else:
            self.brush.setColor(self.color)
            self.pen.setColor(self.color)

        painter.setBrush(self.brush)
        painter.setPen(self.empty_pen)

        if self.ui_type == 'circle':
            painter.drawEllipse(self.rect)
        elif self.ui_type == 'rect':
            painter.drawRect(self.rect)

        else:
            if self.draw_data:
                for i in self.draw_data:
                    draw_line = True
                    shaded_data = i.get('shaded')
                    if shaded_data:
                        painter.setBrush(self.brush)
                        painter.setPen(self.empty_pen)
                        path = QtGui.QPainterPath()
                        if not len(shaded_data) > 1:
                            continue
                        triangles = [shaded_data[x:x+3] for x in range(0, len(shaded_data), 3)]
                        for tri in triangles:
                            poly = QtGui.QPolygon()
                            path.moveTo(tri[0][0], tri[0][1])
                            poly.append(QtCore.QPoint(tri[0][0], tri[0][1]))
                            for pnt in tri[1:]:
                                poly.append(QtCore.QPoint(pnt[0], pnt[1]))
                                path.lineTo(pnt[0], pnt[1])
                            painter.fillPath(path, self.brush)
                        draw_line = False

                    wire_frame_data = i.get('wireframe')
                    if wire_frame_data:
                        path = QtGui.QPainterPath()
                        if not len(wire_frame_data) > 1:
                            continue
                        path.moveTo(wire_frame_data[0][0], wire_frame_data[0][1])
                        for pnt in wire_frame_data[1:]:
                            path.lineTo(pnt[0], pnt[1])
                        if draw_line:
                            painter.setBrush(self.empty_brush)
                            painter.setPen(self.pen)
                            painter.drawPath(path)

    @staticmethod
    def get_bounding_box(points):
        x_coordinates, y_coordinates = zip(*points)
        rect = QtCore.QRect(QtCore.QPoint(min(x_coordinates), min(y_coordinates)),
                            QtCore.QPoint(max(x_coordinates), max(y_coordinates)))
        return rect

    def mirror_from(self, other, container_item):
        container_node = container_item.node
        self.node.mirror_from(other.node, container_node)


class PickerView(ng.NodeGraphView):

    _center_line_pen = QtGui.QPen(QtGui.QColor(122, 182, 255, 120), 4.0)

    def __init__(self, scene, parent=None):
        super(PickerView, self).__init__(scene, parent)
        self.setObjectName('View')
        self.__container = None
        self.undo_is_open = False

    def set_container(self, container=None, sync_children=False):
        """

        Args:
            container:
            sync_children(bool):

        Returns:

        """
        self.clear_pickers()
        if not container:
            self.scene().container_item = None
            return
        container = vp.ViewportPicker(container)
        namespace = container.get_name_space()
        picker_api.switch_container_to(container, sync_children=sync_children)
        item = self.set_container_picker(container)
        children_info = container.get_children_information() or {}
        for _, data in children_info.items():
            self.add_picker(data, namespace=namespace)
        self.frame_items()
        return item

    @property
    def container(self):
        return self.__container

    def add_picker(self, data, namespace=None):
        """
        Add picker to the graph view
        Args:
            data:
            namespace:

        Returns:

        """
        name = data.get('name')
        if namespace:
            name = '{}:{}'.format(namespace, name)
        if not Node.object_exist(name):
            OpenMaya.MGlobal.displayWarning("{} does not exist. Skip".format(name))
            return
        item = PickerItem()
        item.init_from_data(data, namespace)
        self.scene().add_node(item)

    def clear_pickers(self):
        """
        Clear pickers from scene

        """
        scene = self.scene()
        if scene:
            scene.clear()

    def set_container_picker(self, container):
        self.__container = container
        item = ContainerItem()
        item.init_from_node(container)
        self.scene().add_node(item)
        self.scene().container_item = item
        return item

    def drawBackground(self, painter, rect):
        result = super(PickerView, self).drawBackground(painter, rect)
        container_item = self.scene().container_item
        if manager.edit_mode and container_item:
            painter.setPen(self._center_line_pen)
            pos = container_item.pos()
            painter.drawLines([QtCore.QLineF(pos.x(), rect.top(), pos.x(), rect.bottom())])
        return result


class PickerScene(ng.NodeGraphScene):

    def __init__(self):
        super(PickerScene, self).__init__()
        self.__nodes = dict()
        self.container_item = None

    @property
    def nodes(self):
        return self.__nodes

    def add_node(self, node_item):
        self.addItem(node_item)
        self.__nodes[node_item.name] = node_item

    def remove_node(self, node_item):
        self.removeItem(node_item)
        if node_item.name in self.__nodes:
            del self.__nodes[node_item]

    def find_node(self, picker):
        return self.__nodes.get(picker.name)

    def clear(self):
        super(PickerScene, self).clear()
        self.__nodes.clear()

    def update_active_selection_text(self, to_sel):
        if self.container_item:
            self.container_item.set_active_selection(to_sel)

    def itemsBoundingRect(self):
        """
        Override this method to return a rect without container node
        Returns:

        """
        node_list = [node for node in self.__nodes.values() if isinstance(node, PickerItem)]
        return self.get_bounding_rect(node_list)

    def find_container_node(self):
        for node in self.__nodes.values():
            if isinstance(node, ContainerItem):
                return node

    def align_selected_items(self, method):
        """
        Align the selected items with a given method
        Args:
            method(int): One of PickerScene.AlignMethod option

        """
        items = self.selectedItems()
        if not items:
            return

        super(PickerScene, self).align_selected_items(method)
        for item in items:
            if item.node:
                pos = item.pos()
                item.node.set_picker_position([pos.x(), -1 * pos.y()])

        if self.container_item:
            picker_api.sync_container_children_info(self.container_item.node)

    def mirror_pickers(self):
        if not self.container_item:
            return
        for name, node in self.__nodes.items():
            if '_L_' in name:
                target_node_name = name.replace('_L_', '_R_')
                target_node = self.__nodes.get(target_node_name)
                if target_node:
                    target_node.mirror_from(node, self.container_item)
                    target_node.refresh_state()
        picker_api.sync_container_children_info(self.container_item.node)
