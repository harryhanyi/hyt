from mhy.qt.core import QtWidgets, QtCore


class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", defaultCollapsed=False, parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.collapsed = defaultCollapsed
        self.minHeight = 0
        self.maxHeight = 0
        self.toggle_button = QtWidgets.QToolButton(text=title)
        self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Fixed)
        self.toggle_button.setFixedHeight(38)
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        if defaultCollapsed:
            self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        else:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)

        self.content_area = QtWidgets.QScrollArea(self)
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_button.pressed.connect(self.on_pressed)

    def on_pressed(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
            self.content_area.setFixedHeight(self.minHeight)
        else:
            self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
            self.content_area.setFixedHeight(self.maxHeight)

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        content_height = layout.sizeHint().height()
        self.maxHeight = self.minHeight + content_height
        if self.collapsed:
            self.content_area.setFixedHeight(self.minHeight)
        else:
            self.content_area.setFixedHeight(self.maxHeight)
