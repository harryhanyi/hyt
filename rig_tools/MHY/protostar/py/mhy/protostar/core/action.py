"""
This module contains the base Action class for all custom actions to inherit.
"""

import sys
import abc
import webbrowser
import traceback
import inspect
from operator import attrgetter
from collections import OrderedDict

import mhy.python.core.compatible as compat
from mhy.python.core.signal import Signal

from mhy.protostar.core.base import BaseObject
import mhy.protostar.core.parameter_base as pb
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp
import mhy.protostar.constants as const
import mhy.protostar.utils as util


__all__ = [
    'custom_exec_method',
    'ActionBase',
    'Action']


def custom_exec_method(func):
    """A decorator for marking methods in actions as custom
    execution methods. Only marked methods can be called
    from action.execute(exec_name=CUSTOM_EXEC_METHOD_NAME).
    """
    func._is_custom_exec = True
    return func


class ExecProgress(object):
    """
    A class for managing the current exection progress.
    """

    def __init__(self, count):
        self.__prog_id = 0
        self.__max_id = int(count) - 1
        if self.__max_id < 1:
            self.__max_id = 1

    def __nonzero__(self):
        return True

    __bool__ = __nonzero__

    def __repr__(self):
        return 'ExecProgress (current id: {}, max id: {})'.format(
            self.__prog_id, self.__max_id)

    __str__ = __repr__

    @property
    def progress_id(self):
        return self.__prog_id

    @property
    def max_id(self):
        return self.__max_id

    @property
    def is_complete(self):
        return self.__prog_id >= self.__max_id - 1

    def increment(self):
        self.__prog_id += 1
        if self.__prog_id > self.__max_id:
            self.__prog_id = self.__max_id


class ActionBase(BaseObject):
    """Base abstract class inherited by ``Action`` and ``ActionGraph``.

    It handles action object creation, parameter management,
    and data serialization.
    """

    def __init__(self, name=None, graph=None):
        """Initializes a new action object.

        Args:
            name (str): The name of this object.
            graph (ActionGraph): An action graph to add this object to.
        """
        super(ActionBase, self).__init__()

        # internal variables
        self.__graph = None
        self.__name = ''

        # a dict to store ui-related data
        self.__ui_data = {}

        # INTERNAL USE ONLY!!
        # This var is used to force disable action/graph at execution time.
        self._force_disable = False

        # a dict to store parameters as (name : parameter) pairs
        # used for fast param query by name
        self.__param_dict = {}

        # an ordered dict to store parameters as
        # (uuid : parameter) pairs.
        # used to query parameters in creation order
        self.__param_ordered_dict = OrderedDict()

        # set owner graph and name.
        # owner graph is set first to ensure the name
        # is clean and unique in this graph
        self.graph = graph
        self.name = name if name else self.class_name

        # find static parameter descriptors
        params = []
        for name in dir(self.__class__):
            param = getattr(self.__class__, name)
            if isinstance(param, pb.base_parameter):
                params.append(param)

        # create static parameters in order
        for param in sorted(params, key=attrgetter('uuid')):
            data = param._get_data()
            kwargs = data['creation']
            kwargs['name'] = data['name']
            kwargs['dynamic'] = False
            kwargs['owner'] = self
            param = pa._create_parameter(param.param_type, **kwargs)
            self.__param_dict[param.name] = param
            self.__param_ordered_dict[param.uuid] = param

    def __repr__(self):
        """Full string representation."""
        return '{} (type: {})'.format(self.long_name, self.class_name)

    def __str__(self):
        """Short string representation."""
        return self.name

    # --- basic properties

    @abc.abstractproperty
    def type_name(self):
        """The type name of this object.

        :type: str
        """

    @abc.abstractproperty
    def source_path(self):
        """The source file path.

        :type: str
        """

    @abc.abstractproperty
    def icon_path(self):
        """The UI icon file path.

        :type: str
        """

    @abc.abstractproperty
    def is_graph(self):
        """Checks if this object is an acton graph object.

        :type: bool
        """

    @abc.abstractproperty
    def app(self):
        """The intented app/DCC name of this object.

        :type: str
        """

    @property
    def ui_data(self):
        """The UI-related data.

        :type: dict
        """
        return self.__ui_data

    @ui_data.setter
    def ui_data(self, data):
        self.__ui_data = data

    @compat.classproperty
    def doc(cls):
        return util.format_doc(cls.__doc__, indent=0, prefix='')

    @doc.setter
    def doc(cls, _):
        raise exp.ActionError(
            'Setting docstring on action objects is not allowed.')

    @property
    def name(self):
        """The short name (without namespaces).

        :type: str
        :setter: Sets the short name. Auto-increment if not unique.
        """
        return self.__name

    @name.setter
    def name(self, new_name):
        old_name = self.__name

        # sanitize new name
        if self.graph:
            new_name = self.graph._next_available_object_name(
                new_name, exclude=old_name)
        else:
            new_name = util.sanitize_name(new_name)

        if old_name != new_name:
            self.__name = new_name

            # update owner graph
            if self.graph:
                self.graph._sync_object_key(old_name)

            # update references in downstream scripts
            for param in self.get_params():
                for op in param.output_params:
                    s = op.script
                    if s:
                        s._replace_string(old_name, new_name)

    @property
    def long_name(self):
        """The long name (with namespaces).
        e.g. root_graph:sub_graph:action

        :type: str
        """
        if not self.__graph:
            return self.name
        else:
            return self.__graph.long_name + const.SEP + self.name

    @property
    def graph(self):
        """The owner action graph

        :type: ActionGraph or None
        :setter: Adds the object to an action graph. If None, remove
            this object from the current owner graph.

        Raises:
            ActionError: If a invalid graph is passed into the setter.
        """
        return self.__graph

    @graph.setter
    def graph(self, graph):
        if graph == self.__graph:
            return

        if graph is not None and \
           (not isinstance(graph, ActionBase) or not graph.is_graph):
            raise exp.ActionError('{} is not an action graph.'.format(graph))

        if graph:
            graph.add_object(self)
        elif self.graph and self.graph.has_object(self):
            self.graph.remove_object(self)
        self.__graph = graph

    @property
    def root_graph(self):
        """The root action graph this object belongs to.

        :type: ActionGraph or None
        """
        graph = self.__graph
        if not graph:
            if self.is_graph:
                return self
            return
        else:
            return graph.root_graph

    def __iter_owner_graphs(self):
        """Iterates through all the owner graphs."""
        graph = self.graph
        while graph:
            yield graph
            graph = graph.graph

    @property
    def in_reference_graph(self):
        """Checks if this object is in an referenced graph.

        :type: bool
        """
        for graph in self.__iter_owner_graphs():
            if graph.referenced:
                return True
        return False

    # --- parameter methods

    @property
    def param_count(self):
        """The number of parameters in this object.

        :type: int
        """
        return len(self.__param_dict)

    def __getattr__(self, name):
        # return the dynamic parameters
        if name in self.__param_dict:
            return self.__param_dict[name]
        raise AttributeError(
            '"{}" object have no attribute or parameter "{}"'.format(
                self.__class__.__name__, name))

    def param(self, name):
        """Returns a parameter in this object by name.

        Args:
            name (string): Name of a parameter to lookup.

        Returns:
            Parameter or None: The parameter object.
        """
        return self.__param_dict.get(str(name))

    def has_param(self, param):
        """Checks if a parameter exists in this object.

        Args:
            param (Parameter or str): A parameter object or its name.

        Returns:
            bool: True if the given parameter is found.
        """
        if isinstance(param, pb.base_parameter):
            return param.name in self.__param_dict
        return str(param) in self.__param_dict

    def _sync_param_key(self, key):
        """Syncs a parameter entry in the internal dict."""
        if key in self.__param_dict:
            param = self.__param_dict.pop(key)
            self.__param_dict[param.name] = param

    def _next_available_param_name(self, name, exclude=None):
        """Given a requested name, returns the next available parameter
        name that can be used in this object.

        Args:
            name (str): A base name to work from.
            exclude (str): A name to exclude from the current parameters.

        Returns:
            str: An unique param name in this object.
        """
        name = util.sanitize_name(name)
        cur_names = set(self.__param_dict.keys())
        if exclude and exclude in cur_names:
            cur_names.remove(exclude)
        if name not in cur_names:
            return name

        new_name = name + '1'
        i = 0
        while new_name in cur_names:
            i += 1
            new_name = name + str(i)

        return new_name

    def iter_params(
            self,
            input_=True, output=True,
            static=True, dynamic=True,
            group=None):
        """A generator that iterates parameter objects in creation order.

        Args:
            input_ (bool): Include input parameters?
            output (bool): Include output parameters?
            static (bool): Include static parameters?
            dynamic (bool): Include dynamic parameters?
            group (str or list): If not None, only returns parameters
                belongs to this group(s).

        Yields:
            parameter_base: parameter objects.
        """
        if group and not isinstance(group, (list, tuple)):
            group = (group,)

        for _, param in self.__param_ordered_dict.items():
            if group and param.group not in group:
                continue
            if (static and not param.is_dynamic) or \
               (dynamic and param.is_dynamic):
                if (input_ and not param.is_output) or \
                   (output and param.is_output):
                    yield param

    def get_params(
            self,
            input_=True, output=True,
            static=True, dynamic=True,
            group=None, sort=False):
        """Returns a list of parameter objects in creation order.

        Args:
            input_ (bool): Include input parameters?
            output (bool): Include output parameters?
            static (bool): Include static parameters?
            dynamic (bool): Include dynamic parameters?
            group (str or list): If not None, only returns parameters
                belongs to this group(s).
            sort (bool): If True, sort the return list by group names.
                Exception: outputs will always sorted to the end.
                If False: params are returned in creation order.

        Returns:
            list: a list of parameter objects.
        """
        if not sort:
            return [x for x in self.iter_params(
                input_=input_, output=output,
                static=static, dynamic=dynamic, group=group)]

        group_dict = OrderedDict()
        output_params = []
        for param in self.iter_params(
                input_=input_, output=output,
                static=static, dynamic=dynamic, group=group):
            if param.is_output:
                output_params.append(param)
            else:
                group_dict.setdefault(param.group, [])
                group_dict[param.group].append(param)

        sorted_params = []
        for _, params in group_dict.items():
            # params[0].sort(key=lambda x: x.priority)
            sorted_params.extend(params)
        # output_params[0].sort(key=lambda x: x.priority)
        sorted_params.extend(output_params)
        return sorted_params

    def add_dynamic_param(self, param_type, **kwargs):
        """Adds a dynamic parameter of a given type.
        This method can **ONLY** be used at runtime.
        It can **NOT** be called in __init__.

        Args:
            param_type (string): The parameter type string.
            kwargs: Parameter creation keyword arguments.
                Check out the parameter classes for details.

        Raises:
            ParameterError: If this method is called from __init__.
            ParameterError: If param_type is "callback".
            ParameterError: When adding an iterator parameter to an action.
        """
        # checks if this method is called in the right place
        if kwargs.get('_caller_check', True):
            if sys._getframe(1).f_code.co_name == '__init__':
                raise exp.ParameterError(
                    'this method can NOT be called in __init__.')
        if param_type == 'callback':
            raise exp.ParameterError('Callback parameter cannot be dynamic!')
        if param_type == 'iter' and not self.is_graph:
            raise exp.ParameterError(
                'Iterator parameter is not allowed on actions.')

        name = self._next_available_param_name(kwargs.get('name', 'parameter'))
        kwargs['name'] = name
        kwargs['owner'] = self
        kwargs['dynamic'] = True

        # if not self.is_graph:
        #     kwargs['output'] = False
        #     self.warn(
        #         ('Dynamic parameters on actions must be inputs. '
        #          'Changed {} from output to input.').format(name))

        param = pa._create_parameter(param_type, **kwargs)
        self.__param_dict[param.name] = param
        self.__param_ordered_dict[param.uuid] = param
        return param

    def remove_dynamic_param(self, param, force=False):
        """Removes a dynamic parameter from this object.
        (Static parameters cannot be removed!)

        Args:
            param (str or Parameter): A parameter object or its name.
            force (bool):
                If True, raise error if the given param has output connections.

        Returns:
            Parameter: The removed parameter object.

        Raises:
            ParameterError:
                If the given parameter does not exist in this object.
                If the given parameter is not dynamic.
            PConnectionError:
                If force is False and the given param has output connections.
        """
        if not isinstance(param, pb.base_parameter):
            param = self.__getitem__(param)

        if not param or param.owner != self:
            raise exp.ParameterError(
                '{} does not belong to {}.'.format(param, self))
        if not param.is_dynamic:
            raise exp.ParameterError(
                '{} is not a dynamic parameter.'.format(param))

        outputs = param.output_params
        if outputs and not force:
            raise exp.PConnectionError(
                '{} has outputs to: {}'.format(param, outputs))

        if param.name in self.__param_dict:
            self.__param_dict.pop(param.name)
            self.__param_ordered_dict.pop(param.uuid)
        param._set_owner(None)
        return param

    def clear_dynamic_params(self, force=False):
        """Removes all dynamic params.

        Args:
            force (bool): If True, raise error when any
                dynamic parameter has output connections.

        Returns:
            None
        """
        params = [p for p in self.iter_params() if p.is_dynamic]
        for param in params:
            self.remove_dynamic_param(param, force=force)

    def reset_output_parameters(self):
        """Resets all output parameter values."""
        for param in self.get_params(input_=False, output=True):
            param.reset_value()

    # --- connection methods

    def get_connected_objects(
            self, input_=True, output=True, param=None,
            recursive=False, as_set=False):
        """Returns a list of objects connected to this object.

        Args:
            input_ (bool): Include input objects?
            output (bool): Include output objects?
            param (string or Parameter or None):
                A parameter object or its name to check for connections.
                If None, checks all parameters.
            recursive (bool): [Only available when param is None]
                If True, recurse into all upstream and/or downstream.
            as_set (bool): If True, returns a set instead of list.

        Returns:
            list: A list of Action and/or ActionGraph.
        """
        if param:
            params = [self.param(param)]
            if not params[0]:
                raise exp.ParameterError(
                    '{} does not belong to {}.'.format(param, self))
        else:
            params = [x for x in self.iter_params()]

        objects = set()
        for param in params:
            if input_:
                for p in param.input_params:
                    owner = p.owner
                    if owner and owner.graph == self.graph:
                        objects.add(owner)
                        if recursive:
                            objects = objects | owner.get_connected_objects(
                                input_=input_, output=output,
                                recursive=recursive, as_set=True)

            if output:
                for p in param.output_params:
                    owner = p.owner
                    if owner and owner.graph == self.graph:
                        objects.add(owner)
                        if recursive:
                            objects = objects | owner.get_connected_objects(
                                input_=input_, output=output,
                                recursive=recursive, as_set=True)

        if as_set:
            return objects
        return sorted(list(objects), key=lambda x: x.name)

    def connect(self, param, other_object, other_param=None, force=False):
        """Connects a parameter on this object to another param on
        another object.

        Args:
            param (str): Name of a parameter on this object.
            other_object (Action or ActionGraph): The other object.
            other_param (str): Name of a parameter on the other object.
                If None, use the same parameter name.
            force (bool): If False, raise error if the other paramet
                is already connected.

        Returns:
            None

        Raises:
            PConnectionError:
                If other_object is not an action or action graph object.
            PConnectionError:
                If any of the 2 params don't exist.
        """
        if not isinstance(other_object, ActionBase):
            raise exp.PConnectionError(
                '{} is not an action or action graph.'.format(other_object))

        source = self.param(param)
        if not source:
            raise exp.PConnectionError(
                'Source parameter not found: {}.{}.'.format(self, param))

        if other_param is None:
            other_param = param
        target = other_object.param(other_param)
        if not target:
            raise exp.PConnectionError(
                'Target parameter not found: {}.{}.'.format(
                    other_object, other_param))

        source.connect(target, force=force)

    def __rshift__(self, other_param):
        """Right shift operator ``>>``. Use it to force connect the
        message parameter to another parameter.

        ``action >> param`` is equivalent to
        ``action.message >> param``
        """
        if not isinstance(other_param, pb.base_parameter):
            raise exp.PConnectionError(
                '{} is not a parameter.'.format(other_param))
        self.param(const.SELF_PARAM_NAME) >> other_param

    def promote(self, param, name=None, force=False, output=False):
        """Promotes a parameter in this object onto the owner graph.

        The concept of parameter promotion means creating a copy of a given
        parameter on the owner graph, and connect the copied parameter back
        to the original parameter. This allows the user to pass data in and
        out of sub-graphs.

        An input parameter can be promoted to the owner graph's input or output.
        An output parameter can ONLY be promoted to the owner graph's output.

        Args:
            param (str or Parameter): A parameter to promote, or its name.
            name (str): Name of the promoted parameter. If None, use the
                original parameter name.
            force (bool): If True, force promote if param is an input parameter
                and has input connections. Otherwise raise ParameterError.

        Returns:
            Parameter: The promoted parameter.

        Raises:
            ActionError:
                If this objet is not in an action graph.
            ParameterError:
                If param is not on this object.
            ParameterError:
                If param already has input connections and force is False.
            ParameterError:
                If the owner already has a parameter with the same name.
        """
        # get the owner graph
        graph = self.graph
        if not graph:
            raise exp.ActionError('{} is not in a graph yet.'.format(self))

        # get the parameter object
        if not isinstance(param, pb.base_parameter):
            param = self.param(param)
        if not param or param.owner != self:
            raise exp.ParameterError(
                '{} not found on {}.'.format(param, self))

        # if param is output, the promoted param must be an output as well.
        if param.is_output:
            output = True

        # establish param name
        name = str(name) if name else param.name
        if graph.has_param(name):
            raise exp.ParameterError(
                'Graph {} already has a parameter named {}.'.format(
                    graph, name))

        if not force and not output and param.has_input:
            raise exp.ParameterError(
                '{} already has a input connections!.'.format(param))

        # copy the param onto the owner graph
        data = param._get_data()
        data['name'] = name
        data['creation']['output'] = output
        cparam = graph.add_dynamic_param(
            data['type'], name=data['name'], **data['creation'])

        # connect back to the original param
        if output:
            param >> cparam
        else:
            cparam >> param

        self.info('Promoted {} to {}'.format(param.full_name, cparam.full_name))
        return cparam

    def get_promoted_param(self, param):
        """Returns the promoted parameter on the owner
        graph associated with a given parameter.

        Args:
            param (str or Parameter): A parameter to check, or its name.

        Returns:
            base_parameter or None: The promoted parameter if any.
        """
        # get the parameter object
        if not isinstance(param, pb.base_parameter):
            param = self.param(param)
        if not param or param.owner != self:
            raise exp.ParameterError(
                '{} not found on {}.'.format(param, self))

        # if a script override is present, check if it
        # contains input coming from the owner graph
        if param.script_enabled and param.script:
            owner_graph = param.script.owner_graph
            for each in param.script.input_params:
                if each.owner == owner_graph:
                    return each

        # if no script override, check if the owner graph
        # has any parameter recieving input from this parameter.
        else:
            owner_graph = self.graph
            if owner_graph:
                for each in owner_graph.get_params(
                        input_=False, output=True):
                    if param in each.input_params:
                        return each

    # --- search methods

    def find_actions(
            self, type_=None, name=None, recursive=True, from_root=False):
        """Search for actions.

        Args:
            type_(str): The action type. Team prefix is optional.
                If None, consider all action types.
            name (str): The action name.
                If None, consider all action names.
            from_root (bool): If True, search from the root graph.
                Otherwise search within the graph this action belongs to.

        Returns:
            list: A list of actions found.
        """
        if from_root:
            graph = self.root_graph
        elif self.is_graph:
            graph = self
        else:
            graph = self.graph

        actions = []
        if not graph:
            return actions

        for each in graph.iter_objects():
            if not each.is_graph:
                if not type_ or each.type_name == type_ or \
                   str(each.type_name).split(':')[-1] == type_:
                    if not name or each.name == name:
                        actions.append(each)
            elif recursive:
                actions.extend(each.find_actions(
                    type_=type_, name=name,
                    from_root=False, recursive=recursive))

        return actions

    # --- data methods

    def copy(self, name=None, graph=pb.OWNER_GRAPH, bake_script=False):
        """Returns a copy of this object.

        Args:
            name (str): Name of the copied object.
                If None, use the next available name.
            graph (ActionGraph or None): A graph to copy this action to.
                If is OWNER_GRAPH, use the current graph.
            bake_script (bool): If True, bake script values for all params.

        Returns:
            Action: The copied object.
        """
        if graph and graph == pb.OWNER_GRAPH:
            graph = self.graph

        if self.graph and graph != self.graph:
            bake_script = True
        if graph and graph.in_reference_graph:
            graph = None
            bake_script = True

        name = name if name else self.name
        dup = self.__class__(name=name, graph=graph)
        data = self._get_data()

        for pdata in data['parameters']:
            if bake_script:
                # bake script values
                pdata['value'] = self.param(pdata['name']).value
                pdata['script_enabled'] = False
                if 'script' in pdata:
                    pdata.pop('script')
            else:
                # replace parameter reference to self action with
                # the original action
                if 'script' in pdata:
                    pdata['script'] = pdata['script'].replace(
                        pb.THIS_OBJECT, self.name)

        dup._set_data(data)
        return dup

    def _get_data(self):
        """Returns the serialized data of this object.

        Returns:
            dict
        """
        data = {
            'name': self.name,
            'source': self.type_name,
            'parameters': []
        }

        if self.__ui_data:
            data['ui_data'] = self.__ui_data

        for param in self.get_params():
            # skip static outputs, these are set by the action execution.
            if param.is_output and not param.is_dynamic:
                continue
            pdata = param._get_data(creation=param.is_dynamic)
            data['parameters'].append(pdata)

        return data

    def _set_data(self, data, param=True, value=True):
        """Applies serialized data to this object.
        The name string in the data is skipped.

        Args:
            data (dict): Serialized data generated from self._get_data().
            param (bool): If False, skip setting parameter data.
            value (bool): If False, skip setting value data.

        Returns:
            None
        """
        # apply ui data
        self.ui_data = data.get('ui_data', {})

        # applies parameter data (except scripts)
        if param:
            self.clear_dynamic_params(force=True)
            for pdata in data['parameters']:
                name = pdata['name']

                # param not found, create a dynamic param
                if not self.has_param(name):
                    dv = pdata.get('creation', {}).get(
                        'dynamic', const.PARAM_CATTR_DEFAULT['dynamic'])
                    if pdata.get('dynamic', dv):
                        p = self.add_dynamic_param(
                            pdata['type'], name=name,
                            **pdata.get('creation', {}))
                        p._set_data(pdata, creation=False, value=False)
                else:
                    p = self.param(name)
                    try:
                        p._set_data(
                            pdata, creation=p.is_dynamic, value=False)
                    except BaseException as e:
                        # param found but type doesn't match - try apply data
                        # and print warning if failed.
                        raise exp.ParameterError(
                            'Param {} type changed ({} -> {}): {}'.format(
                                p, pdata['type'], p.param_type, e))

        # applies script data at the end
        if value:
            self._set_value_data(data)

    def _set_value_data(self, data):
        """Applies serialized data to this object.
        This call ONLY applies the value data (value and script override).

        Args:
            data (dict): Serialized data generated from self._get_data().

        Returns:
            None
        """
        for pdata in data['parameters']:
            name = pdata['name']
            param = self.param(name)
            if param:
                param._set_data(pdata, creation=False, value=True)

    # --- debugging

    def print_detail(self, verbose=False):
        """Prints nicely formatted details about this action.

        Args:
            verbose (bool): If True, print detailed doc and parameter status.
                Otherwise only print parameter name and type.

        Returns:
            None
        """
        typ = 'Graph' if self.is_graph else 'Action'
        msg = '\n>> {} ({} | {})'.format(self.long_name, typ, self.type_name)
        self.info(msg, title=False, format_='simple')
        if verbose:
            if not self.is_graph:
                self.info(
                    util.format_doc(self.__class__.__doc__),
                    title=False, format_='simple')
            self.info('   |', title=False, format_='simple')

        self.info('-- Input Parameters:', title=False, format_='simple')

        params = self.get_params(input_=True, output=False)
        if not params:
            self.info('   ... None', title=False, format_='simple')
        else:
            for param in params:
                msg = ' + {} ({})'.format(param.name, param.param_type)
                if verbose:
                    dyn = 'dynamic' if param.is_dynamic else 'static'
                    msg += ' | ({})'.format(dyn)
                self.info(msg, title=False, format_='simple')
                if verbose:
                    self.info(
                        util.format_doc(param.doc),
                        title=False, format_='simple')

                    enabled = 'Off' if param.script_enabled else 'On'
                    self.info(
                        '   + Value ({}): {}'.format(
                            enabled, param._get_pure_value()),
                        title=False, format_='simple')

                    enabled = 'On' if param.script_enabled else 'Off'
                    script = param.script.code if param.script else 'None'
                    self.info(
                        '   + Script ({}): {}'.format(enabled, script),
                        title=False, format_='simple')

                    self.info('   |', title=False, format_='simple')

        self.info('-- Output Parameters:', title=False, format_='simple')

        params = self.get_params(input_=False, output=True)
        if not params:
            self.info('   ... None', title=False, format_='simple')
        else:
            for param in params:
                msg = ' + {} ({})'.format(param.name, param.param_type)
                if verbose:
                    dyn = 'dynamic' if param.is_dynamic else 'static'
                    msg += ' | ({})'.format(dyn)
                self.info(msg, title=False, format_='simple')
                if verbose:
                    self.info(
                        util.format_doc(param.doc),
                        title=False, format_='simple')

    def is_equivalent(self, other, **kwargs):
        """Checks if this object and the other object is equivalent.
        Equivalent means the object type and all parameters are the same.

        Returns:
            bool: The equivalent check result.
        """
        if self.__class__.__name__ != other.__class__.__name__:
            self.warn('Class name mismatched: {} - {}'.format(self.long_name, other))
            return False

        pair = '{} - {}'.format(self.long_name, other.long_name)
        if not self.is_graph and self.type_name != other.type_name:
            self.warn('Source mismatched: ' + pair)
            return False
        # if self.is_graph and self.source_path != other.source_path:
        #     self.warn('Source mismatched: ' + pair)
        #     return False
        if self.param_count != other.param_count:
            self.warn('Parameter count mismatched: ' + pair)
            return False
        for param in self.get_params():
            if not other.has_param(param.name):
                self.warn('Param not found: {}.{}'.format(
                    other.long_name, param.name))
                return False
            other_param = other.param(param.name)
            if param.param_type != other_param.param_type:
                self.warn('[{}] type mismatched: '.format(param.name) + pair)
                return False
            if param.is_dynamic != other_param.is_dynamic:
                self.warn(
                    '[{}] dynamic state mismatched: '.format(param.name) + pair)
                return False
            if param.script_enabled != other_param.script_enabled:
                self.warn(
                    '[{}] script_enable mismatched: '.format(param.name) + pair)
                return False
            if param.script != other_param.script:
                self.warn('[{}] script mismatched: {}\n{}\n\n{}'.format(
                    param.name, pair, param.script, other_param.script))
                return False

            try:
                if param.param_type != 'message' and \
                   param.value != other_param.value:
                    self.warn(
                        '[{}] value mismatched: '.format(param.name) + pair)
                    return False
            except BaseException:
                self.warn('[{}] value eval failed: '.format(param.name) + pair)
                return False

            for key in const.PARAM_CATTR_DEFAULT.keys():
                if hasattr(param, key):
                    if getattr(param, key) != getattr(other_param, key):
                        self.warn(
                            '[{}] property {} mismatched: '.format(
                                param.name, key) + pair)
                        return False
        return True

    # --- default static parameters builtin to all actions and graphs.

    @pa.message_param(priority=0)
    def execution(self):
        """Used to enfoce execution order by chaining this parameter
        together between actions and/or action graphs.
        """

    @pa.bool_param(default=True, priority=-1)
    def enabled(self):
        """The enabled state of this object."""

    @pa.bool_param(default=False, ui_visible=False, priority=-1)
    def break_point(self):
        """If True, stop execution when this action is completed."""

    @pa.message_param(output=True, priority=-1)
    def message(self):
        """This parameter has no value but can be referenced
        in script overrides to represent this action object itself.
        """

    # --- core methods for sub-classes to implement.

    @abc.abstractmethod
    def execute(self):
        """
        The main execution method.
        """


class Action(ActionBase):
    """Base abstract class inherited by all user-developed actions.

    Every sub-class has to implement the main execution method ``run()``.
    """

    # The import source name.
    # This is handled by the factory class. Do NOT override.
    _SOURCE = None

    # a link to the help page
    _HELP_URL = None

    # specify the required app/DCC to run this action
    _APP = None

    # category tags
    _TAGS = []

    # ui node color
    _UI_COLOR = None

    # ui icon file name
    _UI_ICON = None

    # This is handled by the factory class. Do NOT override.
    _UI_ICON_PATH = None

    def __init__(self, name=None, graph=None):
        """Initializes a new action object.

        Args:
            name (str): The name of this object.
            graph (ActionGraph): An action graph to add this object to.
        """
        super(Action, self).__init__(name, graph=graph)
        # internal variables
        self.__status = {}

        # signals
        self.status_changed = Signal(str, int)
        self.break_point_reached = Signal()

    @compat.classproperty
    def tags(cls):
        """The tags associated with this action.

        :type: list
        """
        if not isinstance(cls._TAGS, (list, tuple)):
            tags = set((cls._TAGS,))
        else:
            tags = set(cls._TAGS)
        tags.add(const.TAG_ACTION)
        return tuple(sorted(list(tags)))

    @tags.setter
    def tags(cls, _):
        raise exp.ActionError(
            'Setting tags on action objects is not allowed.')

    @classmethod
    def has_tag(cls, tags):
        """Checks if a tag is associated with this object.

        Args:
            tag (str): A tag to check.

        Returns:
            bool
        """
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        return bool(set(tags) & set(cls.tags))

    @compat.classproperty
    def ui_color(cls):
        """The UI display color (RGB in 0 ~ 255 range).

        :type: tuple
        """
        if cls._UI_COLOR:
            return tuple(cls._UI_COLOR)
        return const.DEFAULT_ACTION_UI_COLOR

    @ui_color.setter
    def ui_color(cls, _):
        raise exp.ActionError(
            'Setting ui color on action objects is not allowed.')

    @compat.classproperty
    def ui_icon(cls):
        """The UI icon file name.

        :setter: Sets the ui icon file name.
        :type: str
        """
        return cls._UI_ICON

    @ui_icon.setter
    def ui_icon(cls, _):
        raise exp.ActionError(
            'Setting ui icon on action objects is not allowed.')

    @compat.classproperty
    def icon_path(cls):
        """The UI icon file path.

        :type: str
        """
        if not cls._UI_ICON_PATH:
            return const.DEF_ACTION_ICON
        return cls._UI_ICON_PATH

    @property
    def is_graph(self):
        """Returns False."""
        return False

    @compat.classproperty
    def type_name(self):
        """The type name of this action (including the team prefix).

        :type: str
        """
        return self._SOURCE

    @property
    def source_path(self):
        """The source file path.

        :type: str
        """
        path = inspect.getfile(self.__class__)
        if path:
            return path.replace('\\', '/')

    @compat.classproperty
    def app(cls):
        """The intented app/DCC name of this object.

        :type: str
        """
        return cls._APP

    def get_status(self, exec_name='main'):
        """Returns the current execution status.

        Args:
            exec_name (str): The execution name. Default to "main"
                indicating the main execution.

        Returns:
            ExecStatus: The execution status.
        """
        return self.__status.get(exec_name, const.ExecStatus.kNone)

    def set_status(self, status, exec_name='main'):
        """Sets the current execution status.

        Args:
            exec_name (str): The execution name. Default to "main"
                indicating the main execution.

        Returns:
            ExecStatus: The execution status.
        """
        cur = self.get_status(exec_name=exec_name)
        if cur != status:
            self.__status[exec_name] = status
            self.status_changed.emit(exec_name, status)

    def reset_status(self, exec_name='main'):
        """Resets the execution status.

        Args:
            exec_name (str): The execution name. Default to "main"
                indicating the main execution.

        Returns:
            None
        """
        if exec_name == 'main':
            self.reset_output_parameters()
        if exec_name in self.__status:
            cur = self.__status.pop(exec_name)
            if cur != const.ExecStatus.kNone:
                self.status_changed.emit(exec_name, const.ExecStatus.kNone)

    def open_help(self):
        """Opens the help page in the default browser, if set.

        Returns:
            None
        """
        if self._HELP_URL:
            webbrowser.open(self._HELP_URL)
        else:
            self.warn('Help url not defined: {}'.format(self.class_name))

    def execute(self, exec_name='main', *args, **kwargs):
        """Executes this action.

        This method also:
            + Prints logging message before the execution.
            + Prints error traceback if the execution fails.
            + Updates execution status at the end.

        Args:
            exec_name (str): Name of this execution.
                If "main", perform the main execution by calling
                ``start()``, ``run()``, ``end()`` in order.
                Otherwise finds the custom execution method that matches
                this name and executes it.
            exec_progress (ExecProgress): An execution progress object to use.
            args: Arguments to pass into the custom execution method.
            kwargs: Keyword arguments to pass into the custom execution method.

        Returns:
            ExecStatus: The final execution status.
        """
        # resets the status of this action
        self.reset_status(exec_name)

        # for custom executions, find the execution method
        if exec_name == 'main':
            exec_method = None
            info_name = '{} ({})'.format(self, self.type_name)
        else:
            exec_method = self._get_custom_exec_method(exec_name)
            info_name = '{}.{} ({})'.format(self, exec_name, self.type_name)

        # no method matching exec_name, pass
        if exec_name != 'main' and not hasattr(self, exec_name):
            pass
        # no custom execution method found, pass
        elif exec_name != 'main' and not exec_method:
            pass
        elif self.enabled.value:
            # print starting log
            if exec_name == 'main':
                self.info('-------------', title=False, format_='simple')
            self.info('Action started... {}'.format(info_name))

            # set status to running
            self.set_status(const.ExecStatus.kRunning, exec_name=exec_name)

            try:
                # execute ths action
                if not exec_method:
                    self.start()
                    obj_args, obj_kwargs = compat.filter_args(
                        self.run, args, kwargs)
                    self.run(*obj_args, **obj_kwargs)
                    self.end()
                else:
                    obj_args, obj_kwargs = compat.filter_args(
                        exec_method, args, kwargs)
                    exec_method(*obj_args, **obj_kwargs)

                # set status to success
                self.set_status(const.ExecStatus.kSuccess, exec_name=exec_name)
            except BaseException:
                # set status to fail and print traceback
                self.set_status(const.ExecStatus.kFail, exec_name=exec_name)
                traceback.print_exc()
                raise exp.ActionError('Action failed... {}'.format(info_name))
        else:
            self.info('Action skipped... {}'.format(info_name))

        return self.get_status(exec_name)

    def _get_custom_exec_method(self, method_name):
        """Returns custom execute method in this class.

        Args:
            method_name (str): The custom execution method name.

        Returns:
            function or None: The custom execution method or None if not found.
        """
        try:
            method = getattr(self, method_name)
            if hasattr(method, '_is_custom_exec'):
                return method
        except BaseException:
            return

    def get_custom_exec_names(self):
        """Returns a list of custom execution method names.

        Returns:
            list: A list of custom execution method names.
        """
        exec_names = []
        for each in dir(self):
            if self._get_custom_exec_method(each):
                exec_names.append(each)
        return exec_names

    @abc.abstractmethod
    def run(self):
        """The main execution method.

        **This method is abstract**. All derived classes must implement it.
        """

    def start(self):
        """Optional execution method for the derived classes to implement.

        Executed before ``run()`` is called.
        """

    def end(self):
        """Optional execution method for the derived classes to implement.

        Executed after ``run()`` is called.
        """


# --- DCC-specific abstract action classes


class MayaAction(Action):
    """Abstract class inherited by all Maya Actions.

    Every sub-class has to implement the main execution method ``run()``.
    """

    _APP = 'maya'

    def execute(self, exec_name='main', exec_progress=None, *args, **kwargs):
        """Re-implement the main execution method to pop a Maya progress
        window during execution and allow user to interrupt with ESC key."""
        from maya import cmds, OpenMaya

        ui_mode = OpenMaya.MGlobal.mayaState() in (
            OpenMaya.MGlobal.kInteractive, OpenMaya.MGlobal.kBaseUIMode)

        info_name = '' if exec_name == 'main' else '.{}'.format(exec_name)
        info_name = self.name + info_name

        # start or update the progress window
        if exec_progress and ui_mode:
            max_val = exec_progress.max_id
            cmds.progressWindow(
                title='Protostar',
                minValue=0,
                maxValue=max_val,
                isInterruptable=True)

            cmds.progressWindow(
                edit=True,
                status='Executing... {}'.format(info_name),
                maxValue=max_val,
                progress=exec_progress.progress_id)

        # execute this action.
        # kill progress window, if execution fails
        try:
            status = super(MayaAction, self).execute(
                exec_name=exec_name, *args, **kwargs)
        except BaseException as e:
            if exec_progress and ui_mode:
                cmds.progressWindow(endProgress=True)
            raise e

        if exec_progress and ui_mode:
            # close progress window on user interruption
            if cmds.progressWindow(query=True, isCancelled=True):
                cmds.progressWindow(endProgress=True)
                raise exp.ActionError('Execution interrupted by user...')

            # closs progress window if break point is reached
            no_break = kwargs.get('no_break', False)
            if not no_break and self.break_point.value:
                cmds.progressWindow(endProgress=True)

            # clos progress window if this is the last action in the
            # current execution.
            elif exec_progress.is_complete:
                cmds.progressWindow(endProgress=True)

        return status


class HoudiniAction(Action):
    """Abstract class inherited by all Houdini Actions.

    Every sub-class has to implement the main execution method ``run()``.
    """

    _APP = 'houdini'
