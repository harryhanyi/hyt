from mhy.qt.core import QtWidgets

try:
    from maya import cmds
    HOST = 'maya'
except BaseException:
    HOST = None


def prompt_scene_modified_dialog(parent):
    """If the current scene is modified, prompt a dialog and ask the user
    if they care about losing unsaved changes. Use this before force
    opening a file.

    Args:
        parent (QWidget): The parent widget of the message dialog.

    Returns:
        bool: Returns True if the user is ok with losing unsaved changes.
            Otherwise False.
    """
    if HOST == 'maya':
        if cmds.file(q=True, modified=True):
            btn = QtWidgets.QMessageBox.question(
                parent,
                'Warning',
                'Current scene not saved!\nUnsaved changes will be lost. Continue?')
            if btn == QtWidgets.QMessageBox.No:
                return False
        return True
    else:
        return True
