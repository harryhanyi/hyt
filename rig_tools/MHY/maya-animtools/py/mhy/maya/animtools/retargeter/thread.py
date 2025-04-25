import os
import traceback

import mhy.maya.anim.retarget.retargeter as rt
import mhy.maya.anim.retarget.utils as util

from mhy.qt.core import QtCore


def safe_join(*args):
    return os.path.join(*args).replace('\\', '/')


class ExecStatus(object):

    kRunning = -1
    kFail = 0
    kSuccess = 1
    kNone = 2


class RetargetExecution(object):
    """
    An execution class for batch retargeting animation.
    """

    progress_started = None
    frame_count_changed = None
    current_frame_changed = None
    status_changed = None

    DEFAULT_ARG_VAL = {
        'src_rig': '',
        'tgt_rig': '',
        'config_file': '',
        'src_files': [],
        'from_string': '',
        'to_string': ''}

    def __init__(self, **kwargs):
        # convert kwargs to vars
        for attr, val in self.DEFAULT_ARG_VAL.items():
            if attr not in kwargs:
                kwargs[attr] = val
        for key, val in kwargs.items():
            setattr(self, key, val)

        if not isinstance(self.src_files, (list, tuple)):
            self.src_files = [self.src_files]

        # establish output file names
        self.output_file_names = []
        for src_file in self.src_files:
            fname = os.path.splitext(os.path.split(src_file)[-1])[0]
            if self.from_string:
                fname = fname.replace(self.from_string, self.to_string)
            self.output_file_names.append(fname + '.ma')

    def run(self):
        """executes a batch retarget request."""
        out_files = []

        if not os.path.isdir(self.output_path):
            os.mkdir(self.output_path)

        retargeter = rt.Retargeter(
            self.tgt_rig, config_file=self.config_file, src_rig=self.src_rig)
        retargeter.retarget_started.connect(self.progress_started)
        retargeter.frame_count_changed.connect(self.frame_count_changed)
        retargeter.current_frame_changed.connect(self.current_frame_changed)
        retargeter.status_changed.connect(self.status_changed)

        for i, src_file in enumerate(self.src_files):
            if not os.path.isfile(src_file):
                util.log_warn('Soruce animation not found: {}'.format(src_file))
                continue

            out_path = safe_join(self.output_path, self.output_file_names[i])

            try:
                retargeter.run(src_file, output_file=out_path)
            except BaseException:
                traceback.print_exc()

        # finish up
        return out_files


class RetargetThread(RetargetExecution, QtCore.QThread):
    """
    A custom Qthread for transferring animation.
    """

    progress_started = QtCore.Signal()
    frame_count_changed = QtCore.Signal(int)
    current_frame_changed = QtCore.Signal(int)
    status_changed = QtCore.Signal(str, int)

    def __init__(self, parent=None, **kwargs):
        RetargetExecution.__init__(self, **kwargs)
        QtCore.QThread.__init__(self, parent)
