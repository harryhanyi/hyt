import sys
from PySide2 import QtWidgets

import os.path
import traceback

__SYS_EXCEPTHOOK = None


def mhy_except_handle(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    ## KeyboardInterrupt is a special case.
    ## We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        global __SYS_EXCEPTHOOK
        if __SYS_EXCEPTHOOK:
            return __SYS_EXCEPTHOOK(exc_type, exc_value, exc_traceback)
        return

    filename, line, _, _ = traceback.extract_tb( exc_traceback ).pop()
    filename = os.path.basename( filename )
    error = "{}: {}".format(exc_type.__name__, exc_value )

    QtWidgets.QMessageBox.critical(None,"Error",
        "<html>A critical error has occured.<br/> "
    + "<b>%s</b><br/><br/>" % error
    + "It occurred at <b>line %d</b> of file <b>%s</b>.<br/>" % (line, filename)
    + "Check maya script editor output for details."
    + "</html>")
    print("Exception full error report:")
    print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def registor_exception_handler():
    global __SYS_EXCEPTHOOK
    if __SYS_EXCEPTHOOK is None:
        __SYS_EXCEPTHOOK = sys.excepthook
    sys.excepthook = mhy_except_handle
