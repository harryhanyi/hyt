from mhy.qt.core import QtCore, QtGui, QtWidgets
import mhy.maya.rigtools.pose_editor.api.utils as utils


class AdjustWidget(QtWidgets.QLineEdit):
    """
    The widget can be used to interactive change value by drag inside widget.
    """
    _pre_excluded = 9
    kInt = 1
    kShowTotal = 2

    def __init__(self, property_name, delegate, value=0.0,
                 high=1.0, low=0.0, step=1.0, mode=0, offset=0.0,
                 callbacks=None, change_signal=None, *args, **kwargs):
        QtWidgets.QLineEdit.__init__(self, *args, **kwargs)
        self.delegate = delegate
        self._value = value
        self._low = low
        self._high = high
        self._step = step
        self._drag_current_count = 0
        self._last_position = None
        self._mode = mode
        self._offset = offset
        self.property_name = property_name
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.init_ui()
        if change_signal:
            change_signal.connect(self.value_changed)
        self.callbacks = callbacks or {}

    def make_callback(self, callback_type):
        callbacks = self.callbacks.get(callback_type, [])
        for callback in callbacks:
            callback(widget=self)

    @property
    def value(self):
        if self._mode & self.kInt:
            return int(self._value)
        return self._value

    def value_changed(self, delegate, value):
        """
        Update UI after pose weight changed.
        """
        if delegate != self.delegate:
            return

        self.set_value(value)

    def set_value(self, value):
        """
        set widget value.
        """
        self._value = value
        new_value = utils.round_to_value(value)
        if self._mode & self.kInt:
            new_value = int(value)
        if self._mode & self.kShowTotal:
            self.setText(
                "{}/{}".format(new_value+self._offset, self._high+self._offset))
        else:
            self.setText(utils.round_to_str(new_value))

    def init_ui(self):
        """
        initialize the children widgets.
        """
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.returnPressed.connect(self.clearFocus)
        self.setCursor(QtCore.Qt.SplitHCursor)
        self.setMouseTracking(0)
        self.set_value(self._value)
        self.setValidator(QtGui.QDoubleValidator())

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit mouseMoveEvent.
        update the value while dragging the mouse.
        """
        if not self.hasFocus():
            if self._drag_current_count == AdjustWidget._pre_excluded:
                self.on_drag_enter()
            if self._drag_current_count >= AdjustWidget._pre_excluded:
                self.on_drag()
            self._drag_current_count += 1
        self.make_callback(callback_type="changing")
        super(AdjustWidget, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit mousePressEvent.
        record the initial value when begin drag mouse.
        """
        self.setMouseTracking(1)
        self._last_position = QtGui.QCursor.pos()
        super(AdjustWidget, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # pylint: disable=invalid-name
        """
        function will be called if the mouse was released
        """
        self.setMouseTracking(0)
        if self._drag_current_count == 0:
            self.setFocus()
            return
        self._drag_current_count = 0
        self.setCursor(QtCore.Qt.SplitHCursor)
        # if the mouse was released we need to put the mouse to its last pos
        QtGui.QCursor.setPos(self._last_position)
        self.make_callback(callback_type='changed')
        super(AdjustWidget, self).mouseReleaseEvent(event)

    def focusInEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit focusInEvent.
        change cursor to IBeamCursor to give user a hint
        for the begin of editing value.
        """
        self.setCursor(QtCore.Qt.IBeamCursor)
        super(AdjustWidget, self).focusInEvent(event)

    def focusOutEvent(self, event):  # pylint: disable=invalid-name
        """
        override the QLineEdit focusOutEvent.
        change cursor to splitHCursor to give user a hint
        for the end of editing value.
        """
        self.setCursor(QtCore.Qt.SplitHCursor)
        super(AdjustWidget, self).focusOutEvent(event)

    def on_drag_enter(self):
        """function will be called if the mouse was hold down for the amount
        of on_dragEnter"""
        self.setCursor(QtCore.Qt.BlankCursor)

    def on_drag(self):
        """function will be called everytime you drag your mouse but first
        after on_drag"""
        current_position = QtGui.QCursor.pos()
        current_x = current_position.x()
        if abs(current_x - self._last_position.x()) < 10:
            return
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        step_size = self._step
        # ignore the drag move less than 10 pixels.
        tolerate = 10.0
        if modifiers == QtCore.Qt.ControlModifier:
            step_size = 0.1*self._step
        self._value += step_size * \
            round((current_x - self._last_position.x()) / tolerate)
        value = max(min(self._value, self._high), self._low)
        # sets the new text
        self.set_value(value)
        self._last_position = current_position
        # reset the cursor if it reaches the end of the screen
        desktop_width = QtWidgets.QApplication.desktop().availableGeometry().width()
        if current_x == (desktop_width - 1):
            QtGui.QCursor.setPos(0, QtGui.QCursor.pos().y())
        elif current_x == 0:
            QtGui.QCursor.setPos(desktop_width - 1, QtGui.QCursor.pos().y())
