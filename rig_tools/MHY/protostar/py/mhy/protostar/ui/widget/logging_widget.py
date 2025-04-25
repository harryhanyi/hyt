from mhy.qt.core.Qt import QtWidgets


class LoggingLine(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LoggingLine, self).__init__(parent=parent)
        self.logging = ""
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.line = QtWidgets.QLineEdit()
        self.line.setReadOnly(True)
        self.open_full_log_pb = QtWidgets.QPushButton("...")
        self.open_full_log_pb.setFixedSize(32, 32)
        layout.addWidget(self.line)
        layout.addWidget(self.open_full_log_pb)
        layout.setContentsMargins(2, 2, 0, 0)
