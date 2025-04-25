"""
All signals are used in MHY pacakge.
"""
import numbers
from PySide2 import QtCore, QtWidgets


class SignalManager(object):
    """
    The class is designed to manage all signals in MHY package
    """
    class __SignalObject(QtCore.QObject):  # pylint: disable=invalid-name
        """
        The dummy class to hold all the signals.
        """
        influence_update_signal = QtCore.Signal()
        pose_update_signal = QtCore.Signal(list)

        pose_cache_finished_signal = QtCore.Signal(object)
        single_step_cache_finished_signal = QtCore.Signal(list)
        target_cache_finished_signal = QtCore.Signal(object)

        corrective_pose_update_signal = QtCore.Signal(object)
        refresh_corrective_view_signal = QtCore.Signal()

        pose_selection_changed_signal = QtCore.Signal(object)
        controller_selection_changed_signal = QtCore.Signal(str)

        pose_changed_signal = QtCore.Signal(object, numbers.Number)
        update_influence_attribute_signal = QtCore.Signal(object)

    signal_object = __SignalObject()
    influence_update = signal_object.influence_update_signal
    pose_update = signal_object.pose_update_signal

    pose_changed_signal = signal_object.pose_changed_signal
    update_influence_attribute_signal = signal_object.update_influence_attribute_signal
    corrective_pose_update = signal_object.corrective_pose_update_signal
    refresh_corrective_view_signal = signal_object.refresh_corrective_view_signal

    controller_selection_changed = signal_object.controller_selection_changed_signal
    pose_selection_changed = signal_object.pose_selection_changed_signal

    # Pose data cache related signals
    influence_cache_finished_signal = signal_object.pose_cache_finished_signal
    single_step_cache_finished_signal = signal_object.single_step_cache_finished_signal
    target_cache_finished_signal = signal_object.target_cache_finished_signal
