from PySide2 import QtWidgets
import maya.OpenMayaUI as omui
import shiboken2
import sys


def maya_main_window():
    """
    Get the maya main window as QtWidgets.QMainWindow instance
    Returns:
        QtWidgets.QMainWindow:
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info[0] == 3:
        return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
    else:
        return shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QMainWindow)


def init_menus():
    """
    Init the menus

    """
    main_window = maya_main_window()
    if not main_window:
        return
    menu_bar = main_window.menuBar()
    actions = menu_bar.actions()
    mhy_menu = QtWidgets.QMenu('MHY', menu_bar)
    mhy_menu.setObjectName('MHY_menu')
    menu_bar.insertMenu(actions[-1], mhy_menu)
