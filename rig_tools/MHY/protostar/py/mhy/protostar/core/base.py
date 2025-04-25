import abc
import uuid

import mhy.python.core.logger as logger


ABCObject = abc.ABCMeta('ABC', (object,), {})


# @six.add_metaclass(abc.ABCMeta)
# class BaseObject():
class BaseObject(ABCObject):
    """Base abstract class for all classes in the protostar framework.

    Each action object is assigned an unique uuid at creation time.
    It acts as the identifier of this object.

    Derived classes must implement name() and long_name().

    This class also comes with convenience logging methods.
    """

    def __init__(self):
        """Initializes a new object with an unique uuid."""
        self.__uuid = uuid.uuid4()

    def __eq__(self, other):
        """Checks equality."""
        return self.__class__ == other.__class__ and self.uuid == other.uuid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        """Protostar objects is always True."""
        return True

    __bool__ = __nonzero__

    def __hash__(self):
        """Returns the hash value."""
        return hash(self.__uuid)

    @property
    def uuid(self):
        """Returns the uuid of this object."""
        return self.__uuid

    @property
    def class_name(self):
        """Returns the type of this object."""
        return self.__class__.__name__

    @abc.abstractproperty
    def name(self):
        """The short name ob this object."""

    @abc.abstractproperty
    def long_name(self):
        """The long name ob this object."""

    # --- convenience logging methods

    @classmethod
    def info(cls, text, title=True, **kwargs):
        if title:
            kwargs['format_'] = '[Protostar]: %(message)s'
        else:
            kwargs['format_'] = '%(message)s'
        logger.info(text, **kwargs)

    @classmethod
    def warn(cls, text, title=True, **kwargs):
        if title:
            kwargs['format_'] = '[Protostar] [WARN]: %(message)s'
        else:
            kwargs['format_'] = 'concise'
        logger.warn(text, **kwargs)

    @classmethod
    def error(cls, text, title=True, **kwargs):
        if title:
            kwargs['format_'] = '[Protostar] [ERROR]: %(message)s'
        else:
            kwargs['format_'] = 'concise'
        logger.error(text, **kwargs)

    @classmethod
    def debug(cls, text, title=True, **kwargs):
        if title:
            kwargs['format_'] = '[Protostar] [DEBUG]: %(message)s'
        else:
            kwargs['format_'] = 'concise'
        logger.debug(text, **kwargs)
