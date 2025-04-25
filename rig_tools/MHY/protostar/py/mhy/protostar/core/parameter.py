"""
A collection of parameter descriptors.

Parameter descriptors transforms a method in an action
or action graph class into a parameter accessor.

Usage:

+ **Define a static parameters in an action class**

.. code:: python

    class MyAction(Action):

        # --- input parameters

        @bool_param(default=True)
        def my_param_a(self):
            '''Describes what this parameter do.'''

        @str_param(default='default_str')
        def my_param_b(self):
            '''Describes what this parameter do.'''

        # --- output parameters

        @list_param(output=True)
        def my_param_c(self):
            '''Describes what this parameter do.'''

+ **Add dynamic parameters in an action object**

.. code:: python

    action.add_dynamic_param('str', name='my_dyn_param', default='some_value')
"""

import os
import sys
import re
import inspect
import copy
from collections import OrderedDict
from functools import partial

import mhy.protostar.core.parameter_base as pb
import mhy.protostar.core.exception as exp
import mhy.protostar.utils as util
import mhy.protostar.constants as const


__all__ = [
    '_create_parameter',
    'pyobject_param',
    'message_param',
    'bool_param',
    'vector2_param',
    'vector3_param',
    'rgb_param',
    'int_param',
    'float_param',
    'enum_param',
    'str_param',
    'dir_param',
    'file_param',
    'callback_param',
    'list_param',
    'iter_param',
    'dict_param'
]


def _create_parameter(type_name, *args, **kwargs):
    """Creates a parameter object of a given type.

    Args:
        type_name (str): Parameter type name.
        args: Parameter creation arguments.
        kwargs: Parameter creation keyword arguments.

    Returns:
        pb.base_parameter: The newly created parameter object.

    Raises:
        ParameterError: If the given type_name is not found.
    """
    for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(obj, pb.base_parameter) and obj._TYPE_STR == type_name:
            return obj(*args, **kwargs)
    raise exp.ParameterError('Parameter type not found: {}'.format(type_name))


class pyobject_param(pb.base_parameter):
    """Python object parameter descriptor.

    Python object parameters can **ONLY** be outputs!

    :type_name: ``pyobject``
    """

    _TYPE_STR = 'pyobject'

    def __init__(self, **kwargs):
        """Initializes a new numeric parameter object.

        Args:
            kwargs: Parameter's creation keyword arguments.
        """
        super(pyobject_param, self).__init__(**kwargs)
        if not self.is_output:
            raise exp.ParameterError('pyobject parameter can ONLY be output!')

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return


class message_param(pb.base_parameter):
    """Message parameter descriptor.

    Message parameters have no value but can be referenced
    in script overrides to represent the owner object itself.

    :type_name: ``message``
    """

    _TYPE_STR = 'message'

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return

    def _convert_value(self, value):
        """Converts a value to this parameter's data type."""
        return value

    @property
    def value(self):
        """The parameter value."""
        return pb.base_parameter.value.fget(self)

    @value.setter
    @pb._check_static_editable
    def value(self, _):
        raise exp.ParameterError(
            'Setting message parameter\'s value is not allowed.')

    @property
    def script(self):
        return pb.base_parameter.script.fget(self)

    @script.setter
    @pb._check_static_editable
    def script(self, code):
        if self.name == const.SELF_PARAM_NAME:
            raise exp.ParameterError(
                'Connecting builtin parameter "{}" is not allowed.'.format(
                    const.SELF_PARAM_NAME))
        pb.base_parameter.script.fset(self, code)


class bool_param(pb.base_parameter):
    """Boolean parameter desciptor.

    :type_name: ``bool``
    """

    _TYPE_STR = 'bool'

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return bool

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return False


class numeric_param(pb.base_parameter):
    """Abstract descrptor interfacing numeric data types."""

    def __init__(
            self,
            min_value=const.PARAM_CATTR_DEFAULT['min_value'],
            max_value=const.PARAM_CATTR_DEFAULT['max_value'],
            **kwargs):

        """Initializes a new numeric parameter object.

        Args:
            min_value (var): The minimum value.
            max_value (var): The maximum value.
            kwargs: Parameter's creation keyword arguments.
        """
        self.__min = None
        self.__max = None
        super(numeric_param, self).__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    # --- basic properties

    @property
    def min_value(self):
        """The minimum value."""
        return self.__min

    @min_value.setter
    @pb._check_static_editable
    def min_value(self, value):
        if value is None:
            self.__min = None
        else:
            self.__min = self._convert_value(value)

    @property
    def max_value(self):
        """The maximum value."""
        return self.__max

    @max_value.setter
    @pb._check_static_editable
    def max_value(self, value):
        if value is None:
            self.__max = None
        else:
            self.__max = self._convert_value(value)

    @property
    def value(self):
        """The parameter value.
        Values are clamped by min and max before returing.

        :setter: Sets the parameter value.
        """
        # Enforce min/max here instead of in the value setter so that
        # min/max can be enforced for connections.
        return self.clamp_value(super(numeric_param, self).value)

    @value.setter
    @pb._check_static_editable
    def value(self, value):
        pb.base_parameter.value.fset(self, value)

    def clamp_value(self, value):
        """Clamps the input value by the min/max values."""
        value = self._convert_value(value)
        if self.min_value is not None and value < self.min_value:
            return self.min_value
        if self.max_value is not None and value > self.max_value:
            return self.max_value
        return value


class int_param(numeric_param):
    """Integer parameter descriptor.

    :type_name: ``int``
    """

    _TYPE_STR = 'int'

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return int

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return 0


class float_param(numeric_param):
    """Float parameter descriptor.

    :type_name: ``float``
    """

    _TYPE_STR = 'float'

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return float

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return 0.0


class _vector_param(pb.base_parameter):
    """
    Abstract vector parameter descriptor.
    """

    # vector length
    _LEN = 2

    def __init__(self, as_int=False, **kwargs):
        """Initializes a new vector parameter object.

        Args:
            as_int (bool): If True, use int as each item type.
                Otherwise use float.
            kwargs: Parameter's creation keyword arguments.
        """
        self.__as_int = as_int
        super(_vector_param, self).__init__(**kwargs)

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return int if self.__as_int else float

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return tuple([self._type_func(0)] * self._LEN)

    def _convert_value(self, value):
        """Converts a value to this parameter's data type."""
        tf = self._type_func
        try:
            if not isinstance(value, (list, tuple)):
                return tuple([tf(value)] + [tf(0)] * (self._LEN - 1))
            else:
                new_val = []
                for i in range(self._LEN):
                    if i < len(value):
                        new_val.append(tf(value[i]))
                    else:
                        new_val.append(tf(0))
                return tuple(new_val)
        except BaseException:
            raise exp.ParameterError(
                '{}: Failed converting {} from {} to vector{}.'.format(
                    self, value, type(value), self._LEN))


class vector2_param(_vector_param):
    """Vector2 parameter descriptor.

    :type_name: ``vector2``
    """

    _LEN = 2
    _TYPE_STR = 'vector2'


class vector3_param(_vector_param):
    """Vector3 parameter descriptor.

    :type_name: ``vector3``
    """

    _LEN = 3
    _TYPE_STR = 'vector3'


class rgb_param(vector3_param):
    """Color RGB parameter descriptor.
    Values are in range 0 ~ 255.

    :type_name: ``rgb``
    """

    _TYPE_STR = 'rgb'

    def _convert_value(self, value):
        """Converts a value to this parameter's data type."""
        value = list(super(rgb_param, self)._convert_value(value))
        for i in range(3):
            if value[i] < 0:
                value[i] = 0
            elif value[i] > 255:
                value[i] = 255
        return tuple(value)


class enum_param(int_param):
    """Enum parameter descriptor.

    :type_name: ``enum``
    """

    _TYPE_STR = 'enum'

    def __init__(
            self,
            items=const.PARAM_CATTR_DEFAULT['items'],
            **kwargs):
        """Initializes a new enum parameter object.

        Args:
            items (list): A list of enum item strings.
            kwargs: int_param's creation keyword arguments.
        """
        if not isinstance(items, (list, tuple)):
            items = [items]
        items = [str(x) for x in items]
        if not items:
            raise exp.ParameterError('{}: Enum values are empty.'.format(self))
        self.__items = items

        for key in ('min_value', 'max_value'):
            if key in kwargs:
                kwargs.pop(key)
        super(enum_param, self).__init__(**kwargs)

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return int

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return 0

    @property
    def items(self):
        """The enumerated item list.

        :type: list
        """
        return self.__items

    @items.setter
    @pb._check_static_editable
    def items(self, items):
        if not isinstance(items, (list, tuple)):
            items = [items]
        items = [str(x) for x in items]
        if not items:
            raise exp.ParameterError('{}: Enum values are empty.'.format(self))
        self.__items = items

    @property
    def min_value(self):
        """Enums min value is always 0."""
        return 0

    @min_value.setter
    @pb._check_static_editable
    def min_value(self, value):
        if value:
            raise exp.ParameterError('Minimun enum value cannot be set!')

    @property
    def max_value(self):
        """Enums max value is always the length - 1."""
        return len(self.__items) - 1

    @max_value.setter
    @pb._check_static_editable
    def max_value(self, value):
        if value:
            raise exp.ParameterError('Maximun enum value cannot be set!')

    @property
    def enum_value(self):
        """The current enum string.

        :type: str
        """
        return self.items[self.value]

    @property
    def enum_default(self):
        """The default enum string.

        :type: str
        """
        if self.default is None:
            return 0
        return self.items[self.default]

    def _convert_value(self, value):
        """Converts a value into the matching type of this parameter.

        Raises:
            ParameterError: If the input enum string doesn't exist.
            ParameterError: If the input index is out of range.
        """
        # try convert enum string to enum id
        if not isinstance(value, int):
            try:
                value = self.items.index(str(value))
            except BaseException:
                raise exp.ParameterError(
                    '{}: Enum value {} does not exists.'.format(self, value))
        return value

    def _get_data(self, creation=True):
        """Returns the serialized data of this parameter.

        Args:
            creation (bool): If False, skip serializing creation data.

        Returns:
            dict
        """
        data = super(enum_param, self)._get_data(creation=creation)
        # remove min and max values
        if creation:
            for key in ('min_value', 'max_value'):
                if key in data['creation']:
                    data['creation'].pop(key)
        return data


class str_param(pb.base_parameter):
    """String parameter descriptor.

    :type_name: ``str``
    """

    _TYPE_STR = 'str'

    @property
    def is_str(self):
        """Returns True if this is a string-based parameter."""
        return True

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return str

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return ''

    def _convert_value(self, value):
        """Converts a value to the matching type of this parameter."""
        if value is None:
            return ''
        return super(str_param, self)._convert_value(value)


class dir_param(str_param):
    """Directory path parameter descriptor.

    Values are converted to a proper directory path string in the setter.

    :type_name: ``dir``
    """

    _TYPE_STR = 'dir'

    def _convert_value(self, value):
        """Converts a value to the matching type of this parameter."""
        value = super(dir_param, self)._convert_value(value)
        if value:
            value = value.replace('\\', '/')
            dirname, last = os.path.split(value)
            dots = [m.start() for m in re.finditer(r'\.', last)]
            if len(dots) == 1:
                value = dirname
            if value.endswith('/'):
                return value[:-1]
        return value

    def makedirs(self):
        """Makes the directory if not exists already."""
        path = self.value
        if path and not os.path.isdir(path):
            os.makedirs(path)


class file_param(str_param):
    """File path parameter descriptor.

    Values are converted to a proper file path string in the setter.

    :type_name: ``file``
    """

    _TYPE_STR = 'file'

    def __init__(self, ext=None, **kwargs):
        """Initializes a new enum parameter object.

        Args:
            ext (str or list): A file extension to work with.
            kwargs: str_param's creation keyword arguments.
        """
        if not ext:
            self.__ext = None
        elif not isinstance(ext, (tuple, list)):
            self.__ext = [ext]
        else:
            self.__ext = list(ext)

        super(file_param, self).__init__(**kwargs)

    @property
    def ext(self):
        """The associated extensions.

        :type: set
        """
        return self.__ext

    def _convert_value(self, value):
        """Converts a value into the matching type of this parameter.

        Raises:
            ParameterError: If the input value is not a file path.
            ParameterError: If extension is specified but not matched.
        """
        value = super(file_param, self)._convert_value(value)
        if value:
            value = value.replace('\\', '/')
            if value.rfind('.') == -1:
                raise exp.ParameterError('Not a file path: {}'.format(value))
            if self.__ext:
                ext = os.path.splitext(value)[-1][1:]
                if ext not in self.__ext:
                    raise exp.ParameterError(
                        'Invalid file extension: {}'.format(ext))
        return value

    def makedirs(self):
        """Makes the directory if not exists already."""
        val = self.value
        if val:
            path, _ = os.path.split(self.value)
            if path and not os.path.isdir(path):
                os.makedirs(path)


class callback_param(pb.base_parameter):
    """Callback parameter descriptor.

    Use it to call a method in the owner object, or call a partial object
    directly.

    Callback params can **ONLY** be static.

    :type_name: ``callback``
    """

    _TYPE_STR = 'callback'

    def __init__(self, **kwargs):
        """Initializes a new numeric parameter object.

        Args:
            kwargs: Parameter's creation keyword arguments.
        """
        super(callback_param, self).__init__(**kwargs)
        if self.is_dynamic:
            raise exp.ParameterError('callback parameter can ONLY be static!')

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return str

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return None

    def _convert_value(self, value):
        """Converts a value to the matching type of this parameter."""
        if self._type_func is None or isinstance(value, partial):
            return value
        else:
            return self._type_func(value)

    @property
    def value(self):
        """Calls the referenced method and returns its output.

        Raises:
            ParameterError: If the function doesn't exist in the owner object.
                or the owner object is not set.
        """
        func = pb.base_parameter.value.fget(self)
        if not func:
            return

        # If the function is a partial object, call it directly
        if isinstance(func, partial):
            return func()
        # otherwise call the function in the owner object.
        else:
            if not self.owner:
                raise exp.ParameterError(
                    'Parameter {} has no owner.'.format(self))
            if not hasattr(self.owner, func):
                raise exp.ParameterError(
                    'Funtion {} not found in {}.'.format(func, self.owner))
            return getattr(self.owner, func)()

    @value.setter
    @pb._check_static_editable
    def value(self, method):
        pb.base_parameter.value.fset(self, method)

    @property
    def script_enabled(self):
        """Returns False. Script is always disabled."""
        return False

    @script_enabled.setter
    def script_enabled(self, _):
        raise exp.ParameterError(
            'Callback parameter does not accept script override!')

    @property
    def script(self):
        """Script is always None."""
        return

    @script.setter
    def script(self, _):
        raise exp.ParameterError(
            'Callback parameter does not accept script override!')

    def _get_data(self, creation=True):
        """Returns the serialized data of this parameter.

        Args:
            creation (bool): If False, skip serializing creation data.

        Returns:
            dict
        """
        data = super(callback_param, self)._get_data(creation=creation)
        # remove min and max values
        for key in ('script', 'script_enabled'):
            data.pop(key)
        return data


_ITEM_TYPE_DICT = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool
}


class item_param(pb.base_parameter):
    """Abstract item parameter descriptor.

    Item parameters are allowed to have a series of items
    accessible via indices/keys.
    """

    def __init__(
            self,
            item_type=const.PARAM_CATTR_DEFAULT['item_type'],
            min_count=const.PARAM_CATTR_DEFAULT['min_count'],
            max_count=const.PARAM_CATTR_DEFAULT['max_count'],
            **kwargs):

        """Initializes a new numeric parameter object.

        Args:
            min_count (int): The minimum number of items.
            max_count (var): The maximum number of items.
            item_type (str): If not None, enforce this type on all items.
            kwargs: Parameter's creation keyword arguments.
        """
        self.__min = None
        self.__max = None
        self.__item_type = None
        super(item_param, self).__init__(**kwargs)
        self.min_count = min_count
        self.max_count = max_count
        self.item_type = item_type

    # --- basic properties

    @property
    def min_count(self):
        """The minimum number of items."""
        return self.__min

    @min_count.setter
    @pb._check_static_editable
    def min_count(self, value):
        if not value:
            self.__min = None
        else:
            self.__min = int(value)

    @property
    def max_count(self):
        """The maximum number of items."""
        return self.__max

    @max_count.setter
    @pb._check_static_editable
    def max_count(self, value):
        if not value:
            self.__max = None
        else:
            self.__max = int(value)

    @property
    def item_type(self):
        """The item item name."""
        return self.__item_type

    @item_type.setter
    @pb._check_static_editable
    def item_type(self, value):
        if not value:
            self.__item_type = None
        elif value in _ITEM_TYPE_DICT:
            self.__item_type = value
        else:
            raise exp.ParameterError('Invalid item type {}'.format(value))

    @property
    def value(self):
        return copy.copy(pb.base_parameter.value.fget(self))

    @value.setter
    @pb._check_static_editable
    def value(self, value):
        self._check_minmax_count(value)
        pb.base_parameter.value.fset(self, value)

    @property
    def script(self):
        return pb.base_parameter.script.fget(self)

    @script.setter
    @pb._check_static_editable
    def script(self, code):
        pb.base_parameter.script.fset(self, code)
        self._check_minmax_count()

    # --- methods

    def _check_minmax_count(self, val=None):
        """Raises error if value doesn't match min/max count."""
        if not self.min_count and not self.max_count:
            return
        val = self.value if not val else val
        if self.max_count is not None and len(val) > self.max_count:
            raise exp.ParameterError(
                '{} exceeded item max count {}.'.format(
                    self, self.max_count))
        if self.min_count is not None and len(val) < self.min_count:
            raise exp.ParameterError(
                '{} doesn\'t meet item min count {}.'.format(
                    self, self.min_count))

    def __len__(self):
        """Returns the number of items.

        Returns:
            int: item count.
        """
        val = self.value
        return len(val) if val is not None else 0

    def __getitem__(self, i):
        """Returns the item at a given index.

        Raises:
            ParameterError: If the key/index is invalid.
        """
        try:
            return self.value[i]
        except BaseException:
            raise exp.ParameterError(
                'Invalid index/key {} for accessing {}.'.format(i, self))

    @pb._check_static_editable
    def __setitem__(self, i, val):
        """Sets the item at a given index/key.

        Args:
            i (var): The index/key.
            val (var): A value to use.

        Returns:
            None

        Raises:
            ParameterError: If the key/index is invalid.
        """
        result = self.value
        try:
            result[i] = val
            self.value = result
        except BaseException:
            raise exp.ParameterError(
                'Invalid index/key {} for accessing {}.'.format(i, self))

    @pb._check_static_editable
    def __delitem__(self, i):
        """Deletes an item at a given key/index.

        Args:
            i (var): An index or key to access the item.

        Returns:
            None
        """
        self.pop(i)

    @pb._check_static_editable
    def pop(self, i):
        """Pops an item at a given key/index.

        Args:
            i (var): An index or key to access the item.

        Returns:
            var: The item popped.

        Raises:
            ParameterError: If script override is in effect.
            ParameterError: If the key/index is invalid.
        """
        val = self.value
        try:
            result = val.pop(i)
            self.value = val
            return result
        except BaseException:
            raise exp.ParameterError(
                'Invalid index/key {} for accessing {}.'.format(i, self))


class list_param(item_param):
    """List parameter descriptor.

    :type_name: ``list``
    """

    _TYPE_STR = 'list'

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return list

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return []

    def _convert_value(self, value):
        """Converts a value to the matching type of this parameter."""
        if not isinstance(value, (list, tuple)):
            value = [value]
        type_func = _ITEM_TYPE_DICT.get(self.item_type)
        if type_func:
            try:
                return [type_func(x) for x in value]
            except BaseException:
                raise exp.ParameterError(
                    'Can\'t convert all items in {} to type {}'.format(
                        self, self.item_type))
        else:
            if (self.is_output and not self.is_dynamic) or \
               (self.script_enabled and self.script):
                return value
            return util.primitify_list(value)

    @pb._check_static_editable
    def append(self, val):
        """Appends an item to this list.

        Args:
            val (var): A value to append.
                If None, appends a new param with the default value.

        Returns:
            None
        """
        result = self.value
        result.append(val)
        self.value = result

    @pb._check_static_editable
    def insert(self, i, val):
        """Inserts an item to this list.

        Args:
            i (int): The insert index.
            val (var): A value to append.
                If None, appends a new param with the default value.

        Returns:
            None
        """
        result = self.value
        try:
            result.insert(i, val)
        except BaseException:
            raise exp.ParameterError(
                'Invalid index {} for accessing {}.'.format(i, self))
        self.value = result


class iter_param(list_param):
    """Iterator parameter descriptor.

    Iterator parameter is a special list parameter, where param.value
    returns the current iterate item value instead of the entire list.

    Iterator parameter can only be added to action graphs.

    :type_name: ``iter``
    """

    _TYPE_STR = 'iter'

    def __init__(self, *args, **kwargs):
        self.__iter_id = 0
        super(iter_param, self).__init__(*args, **kwargs)

    @property
    def iter_id(self):
        """The current iteration id.

        :type: int
        :setter: Sets the current iteration id.
        """
        return self.__iter_id

    @iter_id.setter
    def iter_id(self, i):
        self.__iter_id = int(i)

    @property
    def iter_value(self):
        """The parameter value at the current iter id.

        :setter: Sets the parameter value at the current iteration id.
        """
        return self.value[self.__iter_id]

    @iter_value.setter
    @pb._check_static_editable
    def iter_value(self, value):
        val = self.value
        val[self.__iter_id] = value
        self.value = val


class dict_param(item_param):
    """Ordered dict parameter descriptor.

    :type_name: ``dict``
    """

    _TYPE_STR = 'dict'

    def __init__(
            self,
            key_type=const.PARAM_CATTR_DEFAULT['key_type'],
            **kwargs):

        """Initializes a new numeric parameter object.

        Args:
            key_type (str): If not None, enforce this type on all keys.
            kwargs: Parameter's creation keyword arguments.
        """
        self.__key_type = None
        super(dict_param, self).__init__(**kwargs)
        self.key_type = key_type

    @property
    def key_type(self):
        """The minimum number of items."""
        return self.__key_type

    @key_type.setter
    @pb._check_static_editable
    def key_type(self, value):
        if not value:
            self.__key_type = None
        elif value in _ITEM_TYPE_DICT and value != 'bool':
            self.__key_type = value
        else:
            raise exp.ParameterError('Invalid key type {}'.format(value))

    @property
    def _type_func(self):
        """A function that converts a value to this parameter type."""
        return OrderedDict

    @property
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""
        return OrderedDict()

    def _convert_value(self, value):
        """Converts a value to the matching type of this parameter."""
        if not isinstance(value, dict):
            raise exp.ParameterError(
                '{}: Failed converting {} from {} to dict'.format(
                    self, value, type(value)))
        key_type_func = _ITEM_TYPE_DICT.get(self.key_type)
        item_type_func = _ITEM_TYPE_DICT.get(self.item_type)
        if key_type_func or item_type_func:
            try:
                new_dict = OrderedDict()
                for key, val in value.items():
                    if key_type_func:
                        key = key_type_func(key)
                    if item_type_func:
                        val = item_type_func(val)
                    new_dict[key] = val
            except BaseException:
                raise exp.ParameterError(
                    'Can\'t convert all items in {} to type {}'.format(
                        self, self.item_type))
        else:
            new_dict = value

        if not key_type_func or not item_type_func:
            if self.is_output and not self.is_dynamic:
                return new_dict
            return util.primitify_dict(new_dict)

        return new_dict
