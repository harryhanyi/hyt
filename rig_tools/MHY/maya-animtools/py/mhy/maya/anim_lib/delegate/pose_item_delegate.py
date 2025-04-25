from PySide2 import QtWidgets, QtGui, QtCore


class PoseItemDelegate(QtWidgets.QItemDelegate):
    pose_label_color = QtGui.QColor(138, 255, 146, 120)
    pose_bar_color = QtGui.QColor(138, 255, 146, 10)
    anim_label_color = QtGui.QColor(245, 66, 99, 120)
    anim_bar_color = QtGui.QColor(245, 66, 99, 10)

    def paint(self, painter, option, index):
        """
        Override paint virtual method to draw pose item
        Args:
            painter(QtGui.QPainter): Passed in
            option(QtWidget.QStyleOption) : Passed in
            index(QtCore.QModelIndex): Passed in

        """
        rect = option.rect
        # painter.setPen(QtGui.QPen(QtCore.Qt.white))
        display_role = index.data(QtCore.Qt.DisplayRole)
        item = index.data(QtCore.Qt.UserRole)
        font = QtGui.QFont()
        font.setPixelSize(24)
        painter.drawPixmap(rect, index.data(QtCore.Qt.DecorationRole))
        if not item:
            return
        if item.is_static:
            label_color = self.pose_label_color
            bar_color = self.pose_bar_color
        else:
            label_color = self.anim_label_color
            bar_color = self.anim_bar_color

        if display_role is not None:
            painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            title_bar_rect = QtCore.QRect(rect.x(), rect.y(), rect.width(), 40)
            painter.setBrush(QtGui.QBrush(bar_color))
            painter.drawRect(title_bar_rect)
            text = str(index.data(QtCore.Qt.DisplayRole))
            alignment = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
            text_rect = QtCore.QRect(rect.x(), rect.y(), rect.width(), 37)
            painter.setPen(QtGui.QPen(label_color))
            painter.setFont(font)
            option.widget.style().drawItemText(
                painter,
                text_rect,
                alignment,
                option.palette,
                True,
                text
            )
        # Draw Selection high light
        if option.state & QtWidgets.QStyle.State_Selected:
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            edge_rect = QtCore.QRect(x+4, y+4, w-8, h-8)
            edge_pen = QtGui.QPen(label_color)
            edge_pen.setWidth(4)
            painter.setPen(edge_pen)
            painter.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
            painter.drawRect(edge_rect)
            # painter.restore()
