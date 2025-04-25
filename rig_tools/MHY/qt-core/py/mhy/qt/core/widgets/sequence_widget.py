"""
This module contains a widget allow user to interactively review a sequence
of images on local disk
"""
import os
import re

from mhy.qt.core import QtWidgets, QtCore, QtGui
from mhy.qt.icon_lib.api import get_icon


__all__ = ['ImageSequenceWidget']

STYLE = """
QToolBar {
    border: 0px solid black; 
    border-radius:2px;
    background-color: rgb(0,0,0,100);
}

QToolButton {
    background-color: transparent;
}
"""


class ImageSequenceWidget(QtWidgets.QPushButton):
    DEFAULT_PLAYHEAD_COLOR = QtGui.QColor(59, 150, 255, 130)

    def __init__(self, parent=None):
        super(ImageSequenceWidget, self).__init__(parent=parent)
        self.image_updated = False
        self._imageSequence = ImageSequence("")
        self._imageSequence.frameChanged.connect(self._frameChanged)
        self.thumb_nail_dir = None
        self.setMouseTracking(True)
        self.updateIcon()
        self.setSize(350, 350)

    def has_frames(self):
        """
        Check if the images sequence has any frames.

        :rtype: bool
        """
        return bool(self.first_frame())

    def first_frame(self):
        """
        Get the first frame in the image sequence.

        :rtype: str
        """
        return self._imageSequence.first_frame()

    def isSequence(self):
        """
        Check if the image sequence has more than one frame.

        :rtype: bool
        """
        return bool(self._imageSequence.frameCount() > 1)

    def dirname(self):
        """
        Get the directory to the image sequence on disk.

        :rtype: str
        """
        return self._imageSequence.dirname()

    def isControlModifier(self):
        """
        Check if the the control modifier is active.

        :rtype: bool
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        return modifiers == QtCore.Qt.ControlModifier

    def setSize(self, w, h):
        """
        Reimplemented so that the icon size is set at the same time.

        :type w: int
        :type h: int
        :rtype: None
        """
        self._size = QtCore.QSize(w, h)
        self.setIconSize(self._size)
        self.setFixedSize(self._size)

    def update_thumb_nail_cb(self, path):
        """

        Args:
            path:

        Returns:

        """
        if not path:
            self.setPath(path)
            self.thumb_nail_dir = None
            return

        list_path = os.listdir(path)
        if len(list_path) == 1:
            file_path = os.path.join(path, list_path[0])
            self.setPath(file_path)
        else:
            self.setPath(path)
        self.thumb_nail_dir = path
        self.image_updated = True

    def setPath(self, path):
        """
        Set a single frame image sequence.

        :type path: str
        """
        self._imageSequence.set_path(path)
        self.updateIcon()

    def updateIcon(self):
        """Update the icon for the current frame."""
        if self._imageSequence.frames():
            icon = self._imageSequence.current_icon()
            self.setIcon(icon)
        else:
            tmp_icon = get_icon(sub_dir='/WINDOWS10/communications/png/256/emoji.png', color=[233, 236, 255, 40])
            self.setIcon(tmp_icon)

    def enterEvent(self, event):
        """
        Start playing the image sequence when the mouse enters the widget.

        :type event: QtCore.QEvent
        :rtype: None
        """
        self._imageSequence.start()

    def leaveEvent(self, event):
        """
        Stop playing the image sequence when the mouse leaves the widget.

        :type event: QtCore.QEvent
        :rtype: None
        """
        self._imageSequence.pause()

    def mouseMoveEvent(self, event):
        """
        Reimplemented to add support for scrubbing.

        :type event: QtCore.QEvent
        :rtype: None
        """
        if self.isControlModifier() and self._imageSequence.frameCount() > 1:
            percent = 1.0 - (float(self.width() - event.pos().x()) / float(self.width()))
            frame = int(self._imageSequence.frameCount() * percent)
            self._imageSequence.jump_to_frame(frame)
            icon = self._imageSequence.current_icon()
            self.setIcon(icon)

    def _frameChanged(self, frame=None):
        """
        Triggered when the image sequence changes frame.

        :type frame: int or None
        :rtype: None
        """
        if not self.isControlModifier():
            icon = self._imageSequence.current_icon()
            self.setIcon(icon)

    def current_filename(self):
        """
        Return the current image location.

        :rtype: str
        """
        return self._imageSequence.current_filename()

    def playhead_height(self):
        """
        Return the height of the playhead.

        :rtype: int
        """
        return 4

    def paintEvent(self, event):
        """
        Triggered on frame changed.

        :type event: QtCore.QEvent
        :rtype: None
        """
        super(ImageSequenceWidget, self).paintEvent(event)

        painter = QtGui.QPainter()
        painter.begin(self)

        if self.current_filename() and self._imageSequence.frameCount() > 1:
            r = event.rect()

            playhead_height = self.playhead_height()
            playhead_position = self._imageSequence.percent() * r.width() - 1

            x = r.x()
            y = self.height() - playhead_height

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(self.DEFAULT_PLAYHEAD_COLOR))
            painter.drawRect(x, y, playhead_position, playhead_height)

        painter.end()


class ImageSequence(QtCore.QObject):
    DEFAULT_FPS = 24

    frameChanged = QtCore.Signal(int)

    def __init__(self, path, *args):
        QtCore.QObject.__init__(self, *args)

        self._fps = self.DEFAULT_FPS
        self._timer = None
        self._frame = 0
        self._frames = []
        self._dirname = None
        self._paused = False

        if path:
            self.set_path(path)

    def first_frame(self):
        """
        Get the path to the first frame.

        :rtype: str
        """
        if self._frames:
            return self._frames[0]
        return ""

    def set_path(self, path):
        """
        Set a single frame or a directory to an image sequence.

        :type path: str
        """
        if not path:
            self._frame = 0
            self._frames = list()
            return
        if os.path.isfile(path):
            self._frame = 0
            self._frames = [path]
        elif os.path.isdir(path):
            self.set_dirname(path)

    def set_dirname(self, dirname):
        """
        Set the location to the image sequence.

        :type dirname: str
        :rtype: None
        """

        def natural_sort_items(items):
            """
            Sort the given list in the way that humans expect.
            """
            convert = lambda text: int(text) if text.isdigit() else text
            alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
            items.sort(key=alphanum_key)

        self._dirname = dirname
        if os.path.isdir(dirname):
            self._frames = [dirname + "/" + filename for filename in os.listdir(dirname)]
            natural_sort_items(self._frames)

    def dirname(self):
        """
        Return the location to the image sequence.

        :rtype: str
        """
        return self._dirname

    def reset(self):
        """
        Stop and reset the current frame to 0.

        :rtype: None
        """
        if not self._timer:
            self._timer = QtCore.QTimer(self.parent())
            self._timer.setSingleShot(False)
            self._timer.timeout.connect(self._frameChanged)

        if not self._paused:
            self._frame = 0
        self._timer.stop()

    def pause(self):
        """
        ImageSequence will enter Paused state.

        :rtype: None
        """
        self._paused = True
        self._timer.stop()

    def resume(self):
        """
        ImageSequence will enter Playing state.

        :rtype: None
        """
        if self._paused:
            self._paused = False
            self._timer.start()

    def stop(self):
        """
        Stops the movie. ImageSequence enters NotRunning state.

        :rtype: None
        """
        self._timer.stop()

    def start(self):
        """
        Starts the movie. ImageSequence will enter Running state

        :rtype: None
        """
        self.reset()
        if self._timer:
            self._timer.start(1000.0 / self._fps)

    def frames(self):
        """
        Return all the filenames in the image sequence.

        :rtype: list[str]
        """
        return self._frames

    def _frameChanged(self):
        """
        Triggered when the current frame changes.

        :rtype: None
        """
        if not self._frames:
            return

        frame = self._frame
        frame += 1
        self.jump_to_frame(frame)

    def percent(self):
        """
        Return the current frame position as a percentage.

        :rtype: None
        """
        if len(self._frames) == self._frame + 1:
            _percent = 1
        else:
            _percent = float((len(self._frames) + self._frame)) / len(self._frames) - 1
        return _percent

    def frameCount(self):
        """
        Return the number of frames.

        :rtype: int
        """
        return len(self._frames)

    def current_icon(self):
        """
        Returns the current frame as a QIcon.

        :rtype: QtGui.QIcon
        """
        return QtGui.QIcon(self.current_filename())

    def current_pixmap(self):
        """
        Return the current frame as a QPixmap.

        :rtype: QtGui.QPixmap
        """
        return QtGui.QPixmap(self.current_filename())

    def current_filename(self):
        """
        Return the current file name.

        :rtype: str or None
        """
        try:
            return self._frames[self.current_frame_number()]
        except IndexError:
            pass

    def current_frame_number(self):
        """
        Return the current frame.

        :rtype: int or None
        """
        return self._frame

    def jump_to_frame(self, frame):
        """
        Set the current frame.

        :rtype: int or None
        """
        if frame >= self.frameCount():
            frame = 0
        self._frame = frame
        self.frameChanged.emit(frame)
