from PySide2 import QtWidgets, QtGui, QtCore
from mhy.maya.rigtools.pose_editor.ui.model.pose_tree_model import PoseTreeModel


class ActionListItemDelegate(QtWidgets.QItemDelegate):
    def paint(self, painter, option, index):
        """
        Override paint virtual method to draw item
        Args:
            painter(QtGui.QPainter): Passed in
            option(QtWidget.QStyleOption) : Passed in
            index(QtCore.QModelIndex): Passed in

        """
        bg_brush = index.data(QtCore.Qt.BackgroundRole)

        if option.state & QtWidgets.QStyle.State_Selected:
            current_color = bg_brush.color()
            if bg_brush.color().alpha() == 0:
                bg_brush.setColor(QtGui.QColor('#595d58'))
            else:
                bg_brush.setColor(current_color.lighter())

        rect = option.rect
        # opt.backgroundBrush = bg_brush
        # opt.palette.setBrush(QtGui.QPalette.Highlight, bg_brush)

        draw_weight_bar = False
        painter.setBrush(bg_brush)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        if index.column() == PoseTreeModel.Weight_Index:
            current_weight = index.data(QtCore.Qt.UserRole) or 0
            weight = max(current_weight, 0)
            if weight is not None:
                painter.drawRect(option.rect)
                x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
                offset = w*weight/10
                high_light_rect = QtCore.QRect(x, y, offset, h)
                current_color = bg_brush.color()
                current_color.setAlpha(current_color.alpha() + 150)
                bg_brush.setColor(current_color)
                painter.setBrush(bg_brush)
                painter.drawRect(high_light_rect)
                draw_weight_bar = True
        if not draw_weight_bar:
            painter.drawRect(option.rect)

        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        display_role = index.data(QtCore.Qt.DisplayRole)
        if display_role is not None:
            text = str(index.data(QtCore.Qt.DisplayRole))
            color = index.data(QtCore.Qt.ForegroundRole)
            if index.column() == 0:
                rect.setLeft(rect.left() + 5)  # Offset a bit to the right
                alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            else:
                alignment = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter

            painter.setPen(QtGui.QPen(color))
            option.widget.style().drawItemText(
                painter,
                rect,
                alignment,
                option.palette,
                True,
                text
            )
            painter.restore()
