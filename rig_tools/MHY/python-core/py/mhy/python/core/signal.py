import mhy.python.core.compatible as compat

try:
    from mhy.qt.core import QtCore
except BaseException:
    QtCore = None


def _is_qt_signal(obj):
    if QtCore and isinstance(obj, QtCore.Signal):
        return True
    return False


class Signal(object):
    """
    A Qt-friendly signal class for storing and executing callbacks.

    Usage:

    .. code-block:: python
        def func(int_val):
            print(int_val)

        signal = Signal(int)
        signal.connect(func)
        for i in range(3):
            signal.emit(i)
    """

    def __init__(self, *arg_types, **kwarg_types):
        """Initializes a signal object."""
        self.__arg_types = arg_types
        self.__kwarg_types = kwarg_types
        self.clear()

    def connect(self, receiver):
        """Connects a callable receiver object to this signal.

        Args:
            receiver (function): A callable function.

        Returns:
            None

        Raises:
            RuntimeError: If the expected signal arguments cannot be passed
                into the receiver function.
        """
        if not _is_qt_signal(receiver):
            if not callable(receiver):
                raise ValueError('Reciever is not callable: {}'.format(receiver))

            status = compat.validate_args(
                receiver, self.__arg_types, self.__kwarg_types)
            if not status:
                raise RuntimeError(
                    ('{} not compatible with signal. '
                     'Expected argument types are: {}, {}').format(
                         receiver, self.__arg_types, self.__kwarg_types))

        self.__callbacks.add(receiver)

    def disconnect(self, receiver):
        """Disonnects a callable receiver object to this signal.

        Args:
            receiver (function): A callable function.

        Returns:
            None
        """
        if receiver in self.__callbacks:
            self.__callbacks.remove(receiver)

    def emit(self, *args, **kwargs):
        """Executes all callbacks in this object.

        Args:
            args: Arguments to pass into each callable object.
            kwargs: Keyword arguments to pass into each callable object.

        Returns:
            None

        Raises:
            RuntimeError: If the emitted signal arguments does not match
                the expected argument types.
        """
        if len(args) != len(self.__arg_types):
            raise RuntimeError('Invalid signal arguments {}'.format(args))
        if set(kwargs.keys()) != set(self.__kwarg_types.keys()):
            raise RuntimeError(
                'Invalid signal keyword arguments {}'.format(kwargs))

        for arg, typ in zip(args, self.__arg_types):
            if not isinstance(arg, typ):
                raise RuntimeError(
                    '{}: Wrong argument type. Expecting a {}.'.format(arg, typ))
        for key, typ in self.__kwarg_types.items():
            arg = kwargs[key]
            if not isinstance(arg, typ):
                raise RuntimeError(
                    ('{}: {}: Wrong keyword argument type. '
                     'Expecting a {}.').format(key, arg, typ))

        for cb in self.__callbacks:
            if _is_qt_signal(cb):
                cb.emit(*args, **kwargs)
            else:
                cb(*args, **kwargs)

    def clear(self):
        """Clears all callbacks in this object.

        Returns:
            None
        """
        self.__callbacks = set()
