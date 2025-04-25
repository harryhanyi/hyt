"""
Qt utility functions
"""

import os
import re

import mhy.python.core.compatible as compat
from mhy.qt.core import QtGui, QtWidgets, QtCompat

try:
    import maya.OpenMayaUI as OpenMayaUI
    HOST = 'maya'
except BaseException:
    HOST = None


RES_PATH = os.environ.get('MHY_QT_RESOURCE_PATH')


def get_icon(file_name, color=None):
    """Returns an icon object.

    Args:
        file_name (str): Name of an icon under the shared_icon folder.
        color: (QColor): If applied, overlay color on icon

    Returns:
        QIcon: The icon object.
    """
    if not RES_PATH:
        return QtGui.QIcon()

    if file_name.startswith(':') or os.path.isfile(file_name):
        file_path = file_name
    else:
        file_path = os.path.join(
            RES_PATH, 'shared_icons', file_name).replace('\\', '/')

    if color:
        pix_map = QtGui.QPixmap(file_path)
        mask = pix_map.mask()
        if not isinstance(color, QtGui.QColor):
            color = QtGui.QColor(*color)
        pix_map.fill(color)
        pix_map.setMask(mask)
        return QtGui.QIcon(pix_map)
    else:
        return QtGui.QIcon(file_path)


def list_stylesheet():
    """Returns a list of stylesheet names in the shared_sheet folder.

    Returns:
        list: A list of style names.
    """
    styles = []
    if not RES_PATH:
        return styles

    base_path = os.path.join(RES_PATH, 'shared_styles')
    for each in os.listdir(base_path):
        path = os.path.join(base_path, each)
        if os.path.isdir(path):
            styles.append(each)
    return styles


def get_stylesheet(style_name):
    """Returns a stylesheet string.

    Args:
        style_name (str): Name of an stylesheet under the shared_styles folder.

    Returns:
        str: The stylesheet string.
    """
    if not RES_PATH:
        return ''

    base_path = os.path.join(
        RES_PATH, 'shared_styles', style_name).replace('\\', '/')
    qss_path = os.path.join(base_path, 'style.qss').replace('\\', '/')

    lines = []
    with open(qss_path, 'r') as f:
        lines = f.readlines()

    results = []
    for line in lines:
        if re.search('BASE_STYLE_PATH', line):
            line = line.replace('BASE_STYLE_PATH', base_path)
        results.append(line)

    return '\n'.join(results)


def get_root_window():
    """Returns the root window of the current app."""
    if HOST == 'maya':
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        return QtCompat.wrapInstance(compat.long(ptr), QtWidgets.QWidget)
    else:
        app = QtWidgets.QApplication.instance()
        if app:
            app = QtCompat.wrapInstance(
                QtCompat.getCppPointer(app), QtWidgets.QApplication)
            window = app.activeWindow()
            return window


def is_widget_valid(widget):
    """Checks if a widget is valid in the backend.

    Args:
        widget (QWidget): A widget to check.

    Returns:
        bool
    """
    if widget is None:
        return False
    if not QtCompat.isValid(widget):
        return False
    return True
