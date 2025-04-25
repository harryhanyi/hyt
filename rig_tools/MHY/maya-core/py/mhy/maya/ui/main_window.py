"""
This module contains functions related maya main window

"""


import maya.OpenMayaUI as omui
import shiboken2
from PySide2 import QtWidgets


def get_main_window():
    """
    Return the Maya main window as a QMainWindow object.
    Returns:
        QMainWindow: The maya main window as QMainWindow instance
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
