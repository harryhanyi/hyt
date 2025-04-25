"""
This module contains the abstract base_parameter descriptor class
for all other parameter descriptors to inherit.
"""

import os
import re
import ast
import abc
import copy
from collections import OrderedDict
from functools import wraps

import mhy.python.core.logger as logger
import mhy.protostar.core.exception as exp
import mhy.protostar.utils as utils
import mhy.protostar.constants as const


__all__ = ['base_parameter', 'PythonScript']


# identifier for parameter referencing on the same object
THIS_OBJECT = '__this__'
# identifier for parameter referencing from the owner graph
OWNER_GRAPH = '__graph__'
_NEXT_PARAM_ID = 0


# def _reset_param_uuid():
#     """Resets the param uuid to 0."""
#     global _NEXT_PARAM_ID
#     _NEXT_PARAM_ID = 0


def _check_editable(func):
    """A decorator for checking if a parameter is editable."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        param = args[0]
        if not param.editable:
            raise exp.ParameterError(
                'Parameter {} is not editable.'.format(param.full_name))
        if not param.is_dynamic:
            raise exp.ParameterError(
                'Static parameter {} is not editable.'.format(param.full_name))
        if not param.is_output and param.in_reference_graph:
            raise exp.ParameterError(
                'Referenced parameter {} is not editable.'.format(
                    param.full_name))
        return func(*args, **kwargs)
    return wrapper


def _check_static_editable(func):
    """A decorator for checking if a static parameter is editable.

    Raises:
        ParameterError: If the parameter is not editable.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        param = args[0]
        if not param.editable:
            raise exp.ParameterError(
                'Parameter {} is not editable.'.format(param))
        if not param.is_output and param.in_reference_graph:
            raise exp.ParameterError(
                'Referenced parameter {} is not editable.'.format(
                    param.full_name))
        return func(*args, **kwargs)
    return wrapper


def _eval_python_script(code, globals_={}, locals_={}):
    """Evaluates a python script and returns the result.

    It handles 2 types of scripts:
        1. eval a single-line scrpit directly as a Python expression.
        2. eval a multi-line script as if it's a Python function body.
    """
    # for single-line expression, run eval directly
    if re.search(r'\b(?:OrderedDict)\b', code):
        globals_['OrderedDict'] = OrderedDict
    is_func_block = bool(re.search(r'\b(?:return)\b', code))
    if not is_func_block:
        code = code.replace('\n', '')
        return eval(code, globals_, locals_)

    # for multi-line statement, wrap it with a function
    new_code = 'def _wrapper_func():\n'
    if not is_func_block:
        new_code += '    return ' + code
    else:
        new_code += code.replace('\n', '\n    ')
    func = ast.parse(new_code, mode='exec')

    # exec the wrapper function
    exec(compile(func, '<string>', mode='exec'), globals_, locals_)
    # eval the wrapper function call and return the result
    return eval('_wrapper_func()', globals_, locals_)


class PythonScript(object):
    """A class interfacing parameter script overrides.
    It handles 2 types of scripts:

    + single-line Python expression:

        + ``1 + 2``
        + ``"my title" + "my name"``
        + ``{actionA.paramA}``
        + ``{actionA.paramA} + {actionB.paramB}``
        + ``{actionA.paramA} + 10``
        + ``{$ENV_VAR} + "my_string"``

    + multi-line code block (write it as a function body):

        .. highlight:: python
        .. code-block:: python

            if {actionA.paramA} > 0:
                    return 'a'
                return 'b'
    """

    def __init__(self, code, driven_param, quiet=False):
        """Initializes a new Python script object.

        Args:
            code (str): An python script string.
            driven_param (Parameter): A parameter driven by this script.
            quiet (bool):: If True, skip validating this script.
                Otherwise raise exception if the script is bad.

        Raises:
            ParameterError: If the driven is not a parameter or not in an action
                graph yet.
        """
        if not isinstance(driven_param, base_parameter):
            raise exp.ParameterError('{} is not a Parameter object!')
        if not driven_param.owner and \
           not driven_param.owner.is_graph and \
           not driven_param.owner.graph:
            raise exp.ParameterError(
                'Parameter {} is not in a graph yet!'.format(driven_param))

        # internal variables
        self.__driven_param = driven_param
        self.__input_params = set()
        self.__input_objects = set()
        self.__input_param_refs = set()
        self.__env_var_refs = set()
        self.__code = str(code)
        self.__cache_completed = False

        # cache the input parameters
        self.__cache_reference_strings()
        self.__cache_parameter_references(quiet=quiet)

    def __repr__(self):
        """Full string representation."""
        return '{} >> {}'.format(self.__code, self.__driven_param)

    def __str__(self):
        """Short string representation."""
        return self.__code

    def __eq__(self, other):
        """Checks equality."""
        return self.__class__ == other.__class__ and self.code == other.code

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def code(self):
        """The script code string.

        :type: str
        """
        return self.__code

    @property
    def has_input(self):
        """Checks if this script has input connections.

        :type: bool
        """
        return len(self.input_params) > 0

    @property
    def input_params(self):
        """A set of input parameters.

        :type: frozenset
        """
        return frozenset(self.__input_params)

    @property
    def input_objects(self):
        """A set of input objects.

        :type: frozenset
        """
        return frozenset(self.__input_objects)

    @property
    def owner_graph(self):
        """Returns the owner graph of the driven param.

        :type: ActionGraph
        """
        owner = self.__driven_param.owner

        # for graph's output params, check within this graph
        if self.__driven_param.is_output and owner.is_graph:
            return owner
        # otherwise check in the owner's graph
        else:
            return owner.graph

    def __cache_reference_strings(self, quiet=False):
        """Returns a set of strings referncing other parameters
        or environment variables.
        """
        self.__input_param_refs = set()
        self.__env_var_refs = set()
        param_ref_to_fix = []
        for s in re.findall(r'{(.*?)}', self.__code):
            if s not in self.__input_param_refs and \
               s not in self.__env_var_refs:
                if s.startswith('$'):
                    self.__env_var_refs.add(s[1:])
                elif s.find(':') == -1:  # skip dict
                    dot_num = len([m.start() for m in re.finditer(r'\.', s)])
                    if dot_num == 0:
                        self.__input_param_refs.add(s)
                    elif dot_num == 1:
                        if s.endswith('.' + const.SELF_PARAM_NAME):
                            ns = s.split('.')[0]
                            param_ref_to_fix.append((s, ns))
                            self.__input_param_refs.add(ns)
                        else:
                            self.__input_param_refs.add(s)
                    elif not quiet:
                        logger.warn('Invalid parameter reference: {}'.format(s))

        # normalize message param reference names to action object name
        for full_name, ref_name in param_ref_to_fix:
            self.__code = self.__code.replace(full_name, ref_name)

    def __resolve_param_ref_string(self, graph, param):
        if param.owner == self.__driven_param.owner:
            if param.name == const.SELF_PARAM_NAME:
                return THIS_OBJECT
            return '{}.{}'.format(THIS_OBJECT, param.name)
        elif param.owner == graph:
            if param.name == const.SELF_PARAM_NAME:
                return OWNER_GRAPH
            return '{}.{}'.format(OWNER_GRAPH, param.name)

        if param.name == const.SELF_PARAM_NAME:
            return param.owner.name
        return param.full_name

    def __cache_parameter_references(self, quiet=False):
        """Caches all refereneced parameters."""
        graph = self.owner_graph
        if not graph:
            return

        params = copy.copy(self.__input_param_refs)

        # cache parameter references
        param_ref_to_fix = set()
        for obj in graph.iter_objects(skip_self=False):
            if not params:
                break

            # cache "message" parameter reference
            if obj.name in params:
                param = obj.message
                pstring = self.__resolve_param_ref_string(graph, param)
                if pstring != obj.name:
                    param_ref_to_fix.add((obj.name, pstring))
                params.remove(obj.name)
                self.__input_params.add(param)
                param._add_output(self.__driven_param)

            if not params:
                break

            # cache other paramater references
            for param in obj.get_params():
                if not params:
                    break

                pstring = self.__resolve_param_ref_string(graph, param)
                full_name = param.full_name

                if pstring in params:
                    params.remove(pstring)
                    self.__input_params.add(param)
                    param._add_output(self.__driven_param)
                elif pstring != full_name and full_name in params:
                    params.remove(full_name)
                    self.__input_params.add(param)
                    param._add_output(self.__driven_param)
                    param_ref_to_fix.add((full_name, pstring))

        if not params:
            self.__cache_completed = True

        for full_name, ref_name in param_ref_to_fix:
            self.__code = self.__code.replace(full_name, ref_name)

        if not quiet:
            for param in params:
                raise exp.PScriptError(
                    'Parameter reference not found on {}: {}'.format(
                        self.__driven_param, param))

    def __remove_cache(self):
        """Removes input parameter caches."""
        self.__input_params = set()
        self.__cache_completed = False

    def __validate_cache(self):
        """Makes sure input parameter caches are still good."""
        for param in self.__input_params:
            if not param or not param.owner:
                self.__remove_cache()
                return

    def evaluate(self):
        """Evaluates this script and return the result.

        Raises:
            PScriptError: If the evaluation fails.
        """
        is_str = self.__driven_param.is_str
        code = self.code
        raw_str = self.code if is_str else ''

        # cache input params again if not completed yet
        self.__validate_cache()
        if not self.__cache_completed:
            self.__cache_parameter_references(quiet=False)

        graph = self.owner_graph

        # replace parameter references with their values
        vars = {}
        for param in self.__input_params:
            if param.name == const.SELF_PARAM_NAME:
                key = param.owner.name
            else:
                key = param.full_name.replace('.', '_')

            # for iterator parameters, resolve to the current iter value
            if param.param_type == 'iter':
                val = param.iter_value
            elif param.param_type == 'message':
                val = param.owner
            else:
                val = param.value
            vars[key] = val

            # param name is sufficient for self connection
            pstring = self.__resolve_param_ref_string(graph, param)
            code = code.replace('{{{}}}'.format(pstring), key)
            if is_str:
                raw_str = raw_str.replace('{{{}}}'.format(pstring), str(val))

        # replace env variable references with their values
        for env_var in self.__env_var_refs:
            if env_var not in os.environ:
                logger.warn(
                    'Environment variable not found: {}'.format(env_var))
            val = os.environ.get(env_var, '')
            key = 'ENV_' + env_var
            vars[key] = val

            code = code.replace('{{${}}}'.format(env_var), key)
            if is_str:
                raw_str = raw_str.replace('{{${}}}'.format(env_var), str(val))

        # evaluate the final script
        try:
            return _eval_python_script(code, globals_=vars)
        except BaseException as e:
            # for string params, return the raw string directly
            if is_str:
                return raw_str

            exp.PScriptError(
                'Script eval failed on {}: {}'.format(self.__driven_param, e))

    def delete(self, bake=True):
        """Deletes this script and all referenced connections.

        Args:
            bake (bool): bakes value into the driven parameter?
        """
        # bake script result
        if bake:
            try:
                self.__driven_param.value = self.evaluate()
            except BaseException:
                pass

        # remove driven parameter from all its inputs
        for param in self.__input_params:
            param._remove_output(self.__driven_param)

    def _replace_string(self, old_string, new_string):
        """Replaces a sub-string in the script."""
        self.__code = self.code.replace(old_string, new_string)


class base_parameter(object):
    """Base abstract parameter descriptor."""

    # the string type name of this parameter
    _TYPE_STR = ''

    def __init__(
            self,
            name='parameter',
            owner=None,
            default=const.PARAM_CATTR_DEFAULT['default'],
            dynamic=const.PARAM_CATTR_DEFAULT['dynamic'],
            output=const.PARAM_CATTR_DEFAULT['output'],
            doc=const.PARAM_CATTR_DEFAULT['doc'],
            editable=const.PARAM_CATTR_DEFAULT['editable'],
            group=const.PARAM_CATTR_DEFAULT['group'],
            priority=const.PARAM_CATTR_DEFAULT['priority'],
            ui_label=const.PARAM_CATTR_DEFAULT['ui_label'],
            ui_visible=const.PARAM_CATTR_DEFAULT['ui_visible']):
        """Initializes a new parameter object.

        Args:
            name (str): The name of this parameter.
            owner (Action or ActionGraph or compound_param):
                The object this parameter belongs to.
            default (var): The default value.
            dynamic (bool): If True, init this as a dynamic parameter,
                otherwise static parameter.
                The dynamic state can **NOT** be changed after initialization.
            output (bool): If True, init this param as an output parameter.
                Otherwise input parameter.
                The output state can **NOT** be changed after initialization.
            doc (str): A description of the parameter.
            editable (bool): If False, this parameter will be ready-only.
            group (str): The name of the group it belongs to.
                + A parameter can **ONLY** belong to a group.
                + Output parameters does **NOT** support group. They
                  **ALWAYS** belong to a built-in group called "outputs".
            priority (str): The priority number of the parameter.
                positive numbers + 0: lower the number, the higher the priority.
                negative numbers: considered lowest priority.
            ui_label (str): The UI label/nice name of this parameter.
            ui_visible (bool): UI visible state.
        """
        global _NEXT_PARAM_ID
        super(base_parameter, self).__init__()

        # internal variables
        self.__owner = None
        self.__name = self.param_type
        self.__doc = doc
        self.__output = output
        self.__dynamic = True
        self.__editable = True
        self.__user_default = None
        self.__id = _NEXT_PARAM_ID
        _NEXT_PARAM_ID += 10

        self.__group = None
        self.__priority = None

        # internal UI variables
        self.__ui_label = None
        self.__ui_visible = None

        # internal value and script variables
        self.__value = None
        self.__script_enabled = False
        self.__script = None

        # a set to track output parameters
        self.__outputs = set()

        # apply properties
        self._set_owner(owner)
        self.default = default
        self.name = name
        self.ui_label = ui_label
        self.ui_visible = ui_visible
        self.priority = priority
        if not group:
            group = const.GROUP_DEFAULT
        if self.__output:
            # if group not in (const.GROUP_OUTPUT, const.GROUP_DEFAULT):
            #     logger.warn(
            #         ('Cannot assign group "{}" to '
            #          'output parameters "{}"').format(group, self.full_name))
            self.group = const.GROUP_OUTPUT
        else:
            self.group = group

        # apply dynamic and editable at the end
        self.__dynamic = dynamic
        self.editable = editable

    def __repr__(self):
        """Full string representation."""
        return '{} (type: {})'.format(self.full_name, self.__class__)

    def __str__(self):
        """Short string representation."""
        return self.full_name

    def __nonzero__(self):
        """Protostar objects is always True."""
        return True

    __bool__ = __nonzero__

    def __eq__(self, other):
        """Checks equality."""
        return self.__class__ == other.__class__ and \
            self.uuid == other.uuid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """Returns the hash value."""
        return hash(self.__id)

    # --- descriptor methods

    def __call__(self, method=None):
        """When called, updates the name and doc arguments to
        the wrapped method, then make this parameter to static.
        """
        if method:
            name = self._get_new_name(method.__name__)
            if name != method.__name__:
                raise exp.ParameterError(
                    'Invalid parameter name: {}'.format(method.__name__))
            self.__set_name(name)
            self.doc = method.__doc__
            prefix = 'Output' if self.__output else 'Input'
            method_doc = """
**{} Parameter ({})**

{}""".format(prefix, self._TYPE_STR, self.doc)
            self.__doc__ = method_doc
        return self

    def __get__(self, obj, objcls):
        """On query, returns the associated parameter."""
        if not obj:
            return self
        param = obj.param(self.__name)
        if not param:
            raise exp.ParameterError(
                'Parameter {} not found on {}'.format(self.__name, obj._owner))
        return param

    def __set__(self, *args, **kwargs):
        """On set, sets the associated parameter's value."""
        raise exp.ParameterError('Overriding parameter is not allowed.')

    # --- value type related methods

    @abc.abstractproperty
    def _type_func(self):
        """A function used to convert a value to this parameter type."""

    @abc.abstractproperty
    def _internal_default(self):
        """An internal default value. Used when user-default is not set."""

    def _convert_value(self, value):
        """Converts a value to this parameter's data type."""
        try:
            return self._type_func(value) if self._type_func else value
        except BaseException:
            raise exp.ParameterError(
                '{}: Failed converting {} from {} to {}.'.format(
                    self, value, type(value), self._type_func))

    # --- basic properties

    @property
    def param_type(self):
        """The param type string.

        :type: str
        """
        return self._TYPE_STR

    @property
    def uuid(self):
        """The global param id.

        :type: str
        """
        return self.__id

    @property
    def is_str(self):
        """Returns True if this is a string-based parameter."""
        return False

    @property
    def name(self):
        """The name of this parameter.

        :type: str
        :setter: Sets the name. Increments the name if its not unique.
        """
        return self.__name

    def _get_new_name(self, name):
        """Returns a clean and unique new name from a given name."""
        if self.owner:
            return self.owner._next_available_param_name(
                name, exclude=self.__name)
        else:
            return utils.sanitize_name(name)

    @name.setter
    @_check_editable
    def name(self, name):
        self.__set_name(name)

    def __set_name(self, name):
        name = name if name else self.param_type
        old_name = self.__name
        new_name = self._get_new_name(name)

        if old_name != new_name:
            self.__name = new_name

            # update owner action
            if self.owner:
                self.owner._sync_param_key(old_name)

            # update downstream scripts / connections
            for param in self.output_params:
                s = param.script
                if s:
                    s._replace_string('.' + old_name, '.' + new_name)

    @property
    def full_name(self):
        """Full name of this parameter ("object.param").

        :type: str
        """
        return '{}.{}'.format(self.__owner, self.__name)

    @property
    def long_name(self):
        """Long name of this param ("object_long_name.param").

        :type: str
        """
        if not self.__owner:
            return self.full_name
        else:
            return '{}.{}'.format(self.__owner.long_name, self.__name)

    @property
    def owner(self):
        """The object that owns this parameter.

        :type: Action, ActionGraph
        :setter: Sets the owner object.
        """
        return self.__owner

    def _set_owner(self, obj):
        if obj is not None:
            try:
                obj.is_graph
            except BaseException:
                raise exp.ActionError('Invalid owner object {}'.format(obj))
        self.__owner = obj
        # if obj is not None and not isinstance(obj, base_parameter):
        #     self.name = self.name

    @property
    def in_reference_graph(self):
        """Checks if this parameter is in a referenced graph."""
        if not self.owner:
            return False

        # if the immidiate owner is a graph, start from its owner.
        owner = self.owner
        if owner.is_graph:
            owner = owner.graph

        if not owner:
            return False
        return owner.in_reference_graph

    @property
    def default(self):
        """The default value.

        :setter: Sets the default value.
        """
        if self.__user_default is None:
            return self._internal_default
        return self.__user_default

    @default.setter
    @_check_static_editable
    def default(self, value):
        if value is not None:
            value = self._convert_value(value)
        if value is None or value == self._internal_default:
            self.__user_default = None
        else:
            self.__user_default = value

    @property
    def ui_label(self):
        """The UI label string (nice name).

        :type: str
        :setter: Sets theui label.
        """
        return self.__name if not self.__ui_label else self.__ui_label

    @ui_label.setter
    @_check_editable
    def ui_label(self, label):
        if not label:
            self.__ui_label = None
        else:
            label = str(label)
            if label == self.__name:
                self.__ui_label = None
            else:
                self.__ui_label = label

    @property
    def editable(self):
        """The editable state.

        :type: bool
        :setter: Sets the editable state.
        """
        return self.__editable

    @editable.setter
    def editable(self, state):
        self.__editable = bool(state)

    @property
    def ui_visible(self):
        """The UI visible state.

        :type: bool
        :setter: Sets the ui visible state.
        """
        return self.__ui_visible

    @ui_visible.setter
    def ui_visible(self, state):
        self.__ui_visible = bool(state)

    @property
    def group(self):
        """The group name this parameter belongs to.

        :type: str
        :setter: Sets the group.
        """
        return self.__group

    @group.setter
    @_check_editable
    def group(self, group):
        self.__group = str(group) if group else None

    @property
    def priority(self):
        """The priority number of this parameter.

        :type: int
        :setter: Sets the priority.
        """
        return self.__priority

    @priority.setter
    @_check_editable
    def priority(self, priority):
        self.__priority = int(priority)

    @property
    def doc(self):
        """The doc string of this parameter.

        :type: str
        :setter: Sets the doc string.
        """
        return self.__doc

    @doc.setter
    @_check_static_editable
    def doc(self, doc):
        self.__doc = utils.format_doc(doc, indent=0, prefix='')

    @property
    def is_output(self):
        """Checks if this is an output parameter.

        :type: bool
        """
        return self.__output

    @property
    def is_dynamic(self):
        """Checks if this is a dynamic parameter.

        :type: bool
        """
        return self.__dynamic

    # --- value methods

    def _get_pure_value(self):
        """Parameter value without script-override."""
        if self.__value is None:
            return self.default
        else:
            return self.__value

    @property
    def value(self):
        """Parameter value.

        Parameter value is resolved in this order:

            1. If script override is present, evaluate it and return the result.
            2. If value is not explicitly set by the user,
               return the default value.
            3. Return the user-specified value.

        :setter: Sets the parameter value.
        """
        if self.__script_enabled:
            if not self.__script:
                return self.default
            return self._convert_value(self.__script.evaluate())
        return self._get_pure_value()

    @value.setter
    @_check_static_editable
    def value(self, value):
        if self.__script_enabled:
            logger.warn(
                ('Parameter "{}" contains active script override. '
                 'The new value won\'t take effect until '
                 'the script override is turned off.').format(self))

        if value is not None:
            value = self._convert_value(value)
        if value is None or value is self.default:
            self.__value = None
        else:
            self.__value = value

    def reset_value(self):
        """Resets the value to default."""
        self.__value = None

    # --- script/connection methods

    @property
    def script_enabled(self):
        """The script enabled state.

        If enabled, the parameter value comes from the script evaluation.
        Otherwise from the user-specified value.

        :type: bool
        :setter: Sets the script enabled state.
        """
        return self.__script_enabled

    @script_enabled.setter
    @_check_static_editable
    def script_enabled(self, state):
        self.__script_enabled = bool(state)

    @property
    def script(self):
        """The script object.

        :type: PythonScript or str
        :getter: Returns the script object, or None if not set.
        :setter: Sets the script and enable script override.
        """
        return self.__script

    @script.setter
    @_check_static_editable
    def script(self, code):
        self.set_script(code, quiet=False)

    def set_script(self, code, quiet=False):
        """Sets the script of this parameter.

        Args:
            code (PythonScript or str): The code to set.
            quiet (bool): If True, skip valiating the script.
                Otherwise raise exception if the script is bad.

        Returns:
            None
        """
        # validate for "execution" parameter
        if code and self.name == 'execution' and \
           not re.search(r'^{\w+.execution}$', str(code)):
            raise exp.PConnectionError(
                'Parameter "execution" can only be chained together.')

        # remove existing script
        if self.__script:
            self.__script.delete()

        if not code:
            self.__script = None
            self.__script_enabled = False
            return

        # apply new script object
        if isinstance(code, PythonScript):
            self.__script = code
        else:
            self.__script = PythonScript(code, self, quiet=quiet)
        self.__script_enabled = True

        # evaluate the script so that the user can see potential errors
        if not quiet:
            self.__script.evaluate()

    def clear_script(self, bake=True):
        """Deletes the script override, if any.

        Args:
            bake (bool): bakes script evaluation value
                into the driven parameter?

        Returns: None
        """
        if self.__script:
            self.__script.delete(bake=bake)
            self.__script = None
        self.script_enabled = False

    @property
    def has_input(self):
        """Checks if this parameter has an input connection.

        :type: bool
        """
        return self.__script_enabled and \
            self.__script and \
            self.__script.has_input

    @property
    def has_direct_input(self):
        """Checks if this parameter has a single direct input.

        :type: bool
        """
        if len(self.input_params) == 1 and \
           re.search(r'^{\w+.\w+}$', self.script.code):
            return True
        return False

    @property
    def has_output(self):
        """Checks if this parameter has output connections.

        :type: bool
        """
        return len(self.__outputs) > 0

    @property
    def is_connected(self):
        """Checks if this parameter is connected.

        :type: bool
        """
        return self.has_input or self.has_output

    @property
    def input_params(self):
        """A set of input parameters.

        :type: frozenset
        """
        if not self.__script_enabled or not self.__script:
            return set()
        return self.__script.input_params

    @property
    def output_params(self):
        """A set of output parameters.

        :type: frozenset
        """
        return frozenset(self.__outputs)

    def is_compatible(self, other):
        """Checks if this parameter is compatible with another parameter.
        Compatible means the value of this parameter can be converted to
        the type of another parameter.

        Args:
            other: Another parameter to convert to.

        Returns:
            bool

        Raises:
            PConnectionError: If other is not a parameter.
        """
        if not isinstance(other, base_parameter):
            raise exp.PConnectionError(
                '{} is not a parameter.'.format(other))

        try:
            other._convert_value(self._internal_default)
            return True
        except BaseException:
            return False

    @_check_static_editable
    def connect(self, other, force=False):
        """Connects this parameter to another parameter.

        Args:
            other (Parameter): The other parameter to connect to.
            force (bool): If False, raise error if the other paramet
                is already connected.

        Returns:
            None

        Raises:
            PConnectionError: If other is not a parameter.
            PConnectionError: If other is not an input param.
            PConnectionError: If the 2 param type is not compatible.
            PConnectionError: If this param is already connected
                and "force" is False.
            PConnectionError: If the 2 params are not in the same action graph.
            PConnectionError: If the new connection cases a cycle.
            PConnectionError: If one of the 2 params is a callback parameter.
        """
        this_object = self.owner
        other_object = other.owner

        if not isinstance(other, base_parameter):
            raise exp.PConnectionError(
                '{} is not a parameter.'.format(other))
        elif not self.is_compatible(other):
            raise exp.PConnectionError(
                '{} is not compatible with {}.'.format(self, other))
        elif other.is_output and not other_object.is_graph:
            raise exp.PConnectionError(
                'Target parameter {} is not an input.'.format(other))
        elif other.has_input and not force:
            raise exp.PConnectionError(
                'Target parameter {} is already connected.'.format(other))
        elif self.param_type == 'callback':
            raise exp.PConnectionError(
                'Callback parameter {} cannot be connected.'.format(self))
        elif other.param_type == 'callback':
            raise exp.PConnectionError(
                'Callback parameter {} cannot be connected.'.format(other))

        # exception A: connect a graph's input to one of its objects
        is_exp_a = this_object == other_object.graph and not self.is_output
        # exception B: connect an object's param to its owner graph's output
        is_exp_b = this_object.graph == other_object and other.is_output

        # if not the above 2 exceptions,
        # make sure the connection is formed within a single graph.
        if not is_exp_a and not is_exp_b:
            if this_object.graph != other_object.graph:
                raise exp.PConnectionError(
                    '{} and {} are not in the same graph.'.format(self, other))

        # checks for connection cycles
        # self-connections are allowed
        if not is_exp_a and not is_exp_b and other_object != this_object and \
           other_object in this_object.get_connected_objects(
               output=False, as_set=True):
            raise exp.PConnectionError(
                'Connecting {} to {} causes a cycle!'.format(self, other))

        if this_object == other_object:
            name = '{}.{}'.format(THIS_OBJECT, self.name)
        elif is_exp_a:
            name = '{}.{}'.format(OWNER_GRAPH, self.name)
        else:
            name = self.full_name
        other.script = '{{{}}}'.format(name)

    def __rshift__(self, other):
        """Right shift operator ``>>``. Use it to force connect parameters.

        ``paramA >> paramB`` is equivalent to
        ``paramA.connect(paramB, force=True)``.
        """
        self.connect(other, force=True)

    def _add_output(self, out_param):
        """Adds an output parameter."""
        self.__outputs.add(out_param)

    def _remove_output(self, out_param):
        """Removes an output parameter."""
        if out_param in self.__outputs:
            self.__outputs.remove(out_param)

    # --- data methods

    def _get_data(self, creation=True):
        """Returns the serialized data of this parameter.

        Args:
            creation (bool): If False, skip serializing creation data.

        Returns:
            dict
        """
        data = {'type': self.param_type, 'name': self.name}
        data['script_enabled'] = self.script_enabled
        if self.script:
            data['script'] = self.script.code
        if self.__value is not None:
            data['value'] = self.__value

        # get creation data
        if creation:
            data['creation'] = {}
            for key, dv in const.PARAM_CATTR_DEFAULT.items():
                if hasattr(self, 'is_' + key):
                    prop = 'is_' + key
                else:
                    prop = key

                if hasattr(self, prop):
                    # Label and default are special cases
                    if key == 'default':
                        val = self._internal_default
                        rVal = self.default
                    elif key == 'ui_label':
                        val = self.__ui_label
                        rVal = self.ui_label
                    else:
                        val = getattr(self, prop)
                        rVal = val

                    if val != dv:
                        data['creation'][key] = rVal

        return data

    def _set_data(self, data, creation=True, value=True):
        """Sets the data of this parameter.

        Args:
            data (dict): The data extracted from self._get_data().
            creation (bool): Apply creation data?
            value (bool): Apply value data (value and script override)?

        Returns:
            None
        """
        # apply creation data
        if creation:
            self.name = data['name']
            if 'creation' in data:
                for key, dv in const.PARAM_CATTR_DEFAULT.items():
                    if hasattr(self, key):
                        # wrapped with try-except in case the setter
                        # does not exsit
                        try:
                            setattr(self, key, data['creation'].get(key, dv))
                        except BaseException:
                            pass

        if value and self.editable:
            # apply script, skip the builtin "self" parameter
            if self.name != const.SELF_PARAM_NAME:
                if 'script' in data:
                    self.set_script(data['script'], quiet=True)
                    # self.script = data['script']
                else:
                    self.script = None
                self.script_enabled = data['script_enabled']

            # apply value, skip all message parameters
            if self.param_type != 'message':
                if 'value' in data:
                    self.value = data['value']
                else:
                    self.value = None

    def copy(self, name=None, owner=None):
        """Returns a copy of this parameter.
        The copied parameter can **ONLY** be dynamic.

        Args:
            name (str): The name of the copied parameter.
                If None, use the next available.
            owner (Action, ActionGraph): The new owner object.
                If None, use the owner of this parameter.

        Returns:
            Parameter: The copied parameter object.
        """
        data = self._get_data()
        name = name if name else data['name']
        kwargs = data.get('creation', {})
        kwargs['dynamic'] = True
        if not owner:
            owner = self.owner
        param = self.__class__(name=name, owner=owner, **kwargs)
        param._set_data(data, creation=False)
        return param
