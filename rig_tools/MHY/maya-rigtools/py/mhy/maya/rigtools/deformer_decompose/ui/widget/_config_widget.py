from mhy.qt.core import QtWidgets, QtCore


class ConfigBase(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.contentWidget = QtWidgets.QWidget(self)
        self.contentLayout = QtWidgets.QVBoxLayout()
        self.contentLayout.setContentsMargins(0, 0, 0, 0)

        self.contentWidget.setLayout(self.contentLayout)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.contentWidget)
        spacer = QtWidgets.QSpacerItem(0,
                                       0,
                                       QtWidgets.QSizePolicy.Minimum,
                                       QtWidgets.QSizePolicy.Expanding
                                       )
        self.contentLayout.addSpacerItem(spacer)
        self.scrollArea.setWidgetResizable(True)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.scrollArea)



