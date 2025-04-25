from mhy.qt.core import QtWidgets
import maya.OpenMayaUI as omui
import shiboken2
from mhy.python.core.compatible import long

deformer_decompose_ui = None


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    win = shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
    return win


def run():
    import mhy.maya.rigtools.deformer_decompose.ui.window as window
    global deformer_decompose_ui
    if deformer_decompose_ui is not None:
        deformer_decompose_ui.show()
    else:
        main_window = maya_main_window()
        deformer_decompose_ui = window.Window(parent=main_window)
    deformer_decompose_ui.show()
    deformer_decompose_ui.raise_()
