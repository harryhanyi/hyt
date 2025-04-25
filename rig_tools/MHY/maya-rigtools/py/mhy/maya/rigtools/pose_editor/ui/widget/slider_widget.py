from PySide2 import QtCore, QtWidgets
from mhy.maya.rigtools.pose_editor.settings import Settings


class SliderWidget(QtWidgets.QWidget):
    """
    The wrapper QWidget class combine a label, a slider and a text input. Together.
    """

    def __init__(self, delegate=None, value=Settings.maximum_weight,
                 decimal=2, callbacks={}, change_signal=None, *args, **kwargs):
        super(SliderWidget, self).__init__(*args, **kwargs)
        self.__decimal = decimal
        self.__format = "%."+str(decimal)+"f"
        layout = QtWidgets.QHBoxLayout(self)
        self.delegate = delegate
        self.__value = value
        self.sub_steps = 100
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent=self)
        self.slider.setMinimum(0.0)
        self.slider.setMaximum(round(self.sub_steps * Settings.maximum_weight))
        self.slider.setValue(round(self.sub_steps * value))
        self.slider.setTickInterval(1.0)
        self.input = QtWidgets.QLineEdit(self.float_to_str(value), parent=self)
        self.input.editingFinished.connect(self.text_changed)
        self.slider.valueChanged.connect(self.slider_changing)
        self.slider.sliderReleased.connect(self.slider_changed)
        self.input.setMaximumWidth(96)
        layout.addWidget(self.slider)
        layout.addWidget(self.input)
        self.callbacks = callbacks
        if change_signal:
            change_signal.connect(self.value_changed)

    def make_callback(self, callback_type):
        callbacks = self.callbacks.get(callback_type, [])
        for callback in callbacks:
            callback(widget=self)

    @property
    def name(self):
        """
        The name of the Pose, current is editing.
        """
        if self.delegate is None:
            return ""
        return self.delegate.name

    def value_changed(self, delegate, value):
        """
        Delegate value changed callback to update UI.
        """
        self.slider.blockSignals(True)
        self.input.blockSignals(True)
        self.slider.setValue(self.sub_steps * value)
        value_str = str(value)
        self.input.setText(value_str)
        self.slider.blockSignals(False)
        self.input.blockSignals(False)

    @ property
    def decimal(self):
        """
        The slider's decimal number.
        """
        return self.__decimal

    @ decimal.setter
    def decimal(self, value):
        """
        The setter for slider's decimal number.
        """
        if not isinstance(value, int):
            raise(Exception("the decimal can only be set to a integer number!"))
        self.__decimal = value
        self.__format = "%."+str(value)+"f"

    def float_to_str(self, value):
        """
        Convert float to string value. only to keep the number of decimal.
        """
        return self.__format % (value)

    @ property
    def value(self):
        """
        The weight value of the Pose, current is editing.
        """
        return self.__value

    @ value.setter
    def value(self, v):
        """
        Setter function for set the weight of the Pose, current is editing.
        """
        value_str = self.float_to_str(v)
        v = float(value_str)
        self.__value = v
        self.slider.setValue(round(self.sub_steps * v))
        value_str = str(v)
        self.input.setText(value_str)

    def slider_changing(self, value):
        """
        Slider changed callback.
        """
        value_str = self.float_to_str(float(value)/self.sub_steps)
        value = float(value_str)
        self.input.setText(value_str)
        if self.__value == value:
            return
        self.__value = value
        self.make_callback(callback_type="changing")

    def slider_changed(self):
        """
        Slider changed callback.
        """
        self.make_callback(callback_type="changed")

    def text_changed(self):
        """
        Text input changed callback.
        """
        self.make_callback(callback_type="changed")
        value_str = self.input.text()
        value = float(value_str)
        self.slider.setValue(round(self.sub_steps * value))
        if self.__value == value:
            return
        self.__value = value
        self.make_callback(callback_type="changing")
