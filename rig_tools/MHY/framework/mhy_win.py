import os
import sys
import re
import json
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QMenu, QComboBox, QLineEdit, QStyledItemDelegate
from PyQt6.QtGui import QAction
from PyQt6 import uic


DOCUMENTS_DIR = os.path.expanduser("~\Documents")
MHY_DIR = DOCUMENTS_DIR + "/MHY"
BASE_DIR = DOCUMENTS_DIR + "/MHY/framework"


class MHYWin(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi(BASE_DIR+"/mhy_win.ui", self)
        self.button_taskFlow.clicked.connect(self.launch_task_tracking)
        self.button_maya.clicked.connect(self.launch_maya)

    def launch_task_tracking(self):
        self.close()
        print("Task Tracking launches")
        subprocess.run(["python", MHY_DIR+"/task-tracking/task_tracking.py"])

    def launch_maya(self):
        self.close()
        print("Maya launches")
        subprocess.run([MHY_DIR+"/launcher/maya_launcher.bat"], shell=True)

    def popout_dialog(self, title, message):
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if title == "Error":
            dialog.setIcon(QMessageBox.Icon.Warning)
        elif title == "Success":
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = MHYWin()
    win.show()

    sys.exit(app.exec())
