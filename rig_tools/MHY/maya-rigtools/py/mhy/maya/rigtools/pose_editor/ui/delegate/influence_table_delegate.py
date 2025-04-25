"""
Delegate module controls influence table view's drawing
"""
from PySide2 import QtWidgets, QtGui, QtCore

__all__ = ["InfluenceItemDelegate"]


class InfluenceItemDelegate(QtWidgets.QItemDelegate):
    def paint(self, painter, option, index):
        """
        Override paint virtual method to draw item
        Args:
            painter(QtGui.QPainter): Passed in
            option(QtWidget.QStyleOption) : Passed in
            index(QtCore.QModelIndex): Passed in

        """
        opt = QtWidgets.QStyleOptionViewItem(option)
        bg_brush = index.data(QtCore.Qt.BackgroundRole)

        if option.state & QtWidgets.QStyle.State_Selected:
            current_color = bg_brush.color()
            if bg_brush.color().alpha() == 0:
                bg_brush.setColor(QtGui.QColor('#595d58'))
            else:
                bg_brush.setColor(current_color.lighter())

        opt.backgroundBrush = bg_brush
        opt.palette.setBrush(QtGui.QPalette.Highlight, bg_brush)

        option.widget.style().drawPrimitive(QtWidgets.QStyle.PE_PanelItemViewItem,
                                            opt, painter)
        text_rect = option.rect
        display_role = index.data(QtCore.Qt.DisplayRole)
        if display_role is not None:
            text = str(index.data(QtCore.Qt.DisplayRole))
            if index.column() == 0:
                text_rect.setLeft(text_rect.left() + 15)  # Offset a bit to the right
                alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            else:
                alignment = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter

            option.widget.style().drawItemText(
                painter,
                text_rect,
                alignment,
                option.palette,
                True,
                text
            )
            painter.restore()
