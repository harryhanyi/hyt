"""
This modules contains utility functions related to maya functionality
"""
from functools import wraps

from maya import cmds, OpenMaya


# --- decorators


def undoable(func):
    """Makes a function undoable as a single chunk
    rather than individual steps."""

    @wraps(func)
    def undo_func(*args, **kwargs):
        cmds.undoInfo(ock=True)
        try:
            return func(*args, **kwargs)
        except BaseException:
            raise
        finally:
            cmds.undoInfo(cck=True)

    return undo_func


_REPEAT_FUNCTION = None
_ARGS = None
_KWARGS = None


def _do_repeat_command():
    if _REPEAT_FUNCTION is not None:
        _REPEAT_FUNCTION(*_ARGS, **_KWARGS)


def repeatable(func):
    """A decorator that stores the arguments of the wrapped function and adds
    it into the repeatList stack (so that user can press "G" to repeat it).
    """

    @wraps(func)
    def repeat_func(*args, **kwargs):
        global _REPEAT_FUNCTION
        global _ARGS
        global _KWARGS

        _REPEAT_FUNCTION = func
        _ARGS = args
        _KWARGS = kwargs

        # store the command to be repeated:
        command_to_repeat = ('python("from {} import _do_repeat_command as drc;'
                             'drc();")').format(__name__)

        # run the function
        ret = func(*args, **kwargs)

        # add the repeatable command to the repeatLast memory stack:
        cmds.repeatLast(
            addCommand=command_to_repeat,
            addCommandLabel=func.__name__)

        return ret

    return repeat_func


def restore_selection(func):
    """A decorator that stores the current selection and restores it
    after the wrapped function is called.
    """

    @wraps(func)
    def sel_func(*args, **kwargs):
        sel = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(sel)
        try:
            return func(*args, **kwargs)
        except BaseException:
            raise
        finally:
            if not sel.isEmpty():
                sel_strings = []
                sel.getSelectionStrings(sel_strings)
                sel = []
                for s in sel_strings:
                    if s and cmds.objExists(s):
                        sel.append(s)
            else:
                sel = []

            if sel:
                cmds.select(sel, replace=True)
            else:
                cmds.select(clear=True)

    return sel_func
