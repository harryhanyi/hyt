"""
This module is a global cache shared with all the modules

"""
from PySide2 import QtCore
from mhy.protostar.lib import ActionLibrary
import logging

logger = logging.getLogger(__name__)

action_lib = ActionLibrary()
action_lib.refresh()

accepted_socket_type = None

is_execution_type = False

force_refreshing_view = False

pix_map_cache = {}


def scale_pix_map(value):
    force_size = 300
    for name, v in pix_map_cache.items():
        width = v['original'].width()
        height = v['original'].height()
        width_factor = force_size*width/height
        v['scaled'] = v['original'].scaled(
            force_size*width_factor*max(value, 1.0),
            force_size*max(value, 1.0),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
    

class SignalManager(object):
    """
    The class is designed to manage all global signals
    """
    class SignalObject(QtCore.QObject):
        """
        The dummy class to hold all the signals.
        """
        tab_opened_signal = QtCore.Signal(object)
        graph_updated_signal = QtCore.Signal(object)
        expression_edited_signal = QtCore.Signal(object)
        reload_graph_parameters_signal = QtCore.Signal(object)
        parameter_connection_changed_signal = QtCore.Signal(object)
        file_to_open_signal = QtCore.Signal(str)
        repaint_lines_signal = QtCore.Signal()
        focus_on_item_signal = QtCore.Signal(object)

    signal_object = SignalObject()
    tab_opened_signal = signal_object.tab_opened_signal
    graph_updated_signal = signal_object.graph_updated_signal
    expression_edited_signal = signal_object.expression_edited_signal

    # Signal to trigger graph parameter panel refreshing
    reload_graph_parameters_signal = \
        signal_object.reload_graph_parameters_signal

    # Signal to trigger updating the connection status of a parameter
    # Connected lines will be recreated when this signal emits
    parameter_connection_changed_signal = \
        signal_object.parameter_connection_changed_signal

    # Called to force all graph views to refresh line items
    repaint_lines_signal = signal_object.repaint_lines_signal

    # Called to open an graph file
    file_to_open_signal = signal_object.file_to_open_signal

    focus_on_item_signal = signal_object.focus_on_item_signal
