"""
All signals are used in MHY pacakge.
"""
from PySide2 import QtCore, QtWidgets


class SignalManager(object):
    """
    The class is designed to manage all signals in MHY package
    """
    class __SignalObject(QtCore.QObject):  # pylint: disable=invalid-name
        """
        The dummy class to hold all the signals.
        """
        item_sel_changed = QtCore.Signal(list)
        pose_files_changed = QtCore.Signal(list)
        refresh_active_items = QtCore.Signal(list)

    signal_object = __SignalObject()
    item_sel_changed = signal_object.item_sel_changed
    pose_files_changed = signal_object.pose_files_changed
    refresh_active_items = signal_object.refresh_active_items


