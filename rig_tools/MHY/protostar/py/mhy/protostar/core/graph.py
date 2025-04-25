"""
The Action Graph class.
"""

import os
import json
import traceback
from collections import OrderedDict

from mhy.python.core.signal import Signal

import mhy.protostar.core.action as act
import mhy.protostar.core.exception as exp
import mhy.protostar.utils as util
import mhy.protostar.constants as const


__all__ = ['ActionGraph']


class ActionGraph(act.ActionBase):
    """Action graph class.

    An action graph is a block that holds a number of actions,
    sub-graphs, and the connections between them.
    """

    def __init__(self, name=None, graph=None):
        """Initializes a new graph object.

        Args:
            name (str): The name of this object.
            graph (ActionGraph): An action graph to add this object to.
        """
        self.__app = None
        self.__doc = ''
        self.__tags = []
        self.__ui_color = None
        self.__ui_icon = None
        # This is handled by the factory class. Do NOT override.
        self._icon_path = None
        self.__source = None
        self.__source_path = None
        self.__referenced = False
        # a dict to store objects as (name : object) pairs
        # used for fast object query by name
        self.__object_dict = {}
        # an ordered dict to store objects as (uuid : object) paris
        # used to query objects in creation order
        self.__object_ordered_dict = OrderedDict()

        # signals
        self.status_changed = Signal(str, int)

        super(ActionGraph, self).__init__(name, graph=graph)

    # --- Basic properties

    @property
    def type_name(self):
        """The type name of this action (including the team prefix).

        :type: str
        """
        return self.__source

    @property
    def source_path(self):
        """The source file path.

        :type: str
        """
        return self.__source_path

    @property
    def doc(self):
        return util.format_doc(self.__doc, indent=0, prefix='')

    @doc.setter
    def doc(self, doc):
        self.__doc = str(doc)

    @property
    def tags(self):
        """The tags associated with this graph.

        :type: list
        """
        return self.__tags

    @tags.setter
    def tags(self, tags):
        if not tags:
            self.__tags = []
            return

        if not isinstance(tags, (list, tuple)):
            tags = set((tags,))
        else:
            tags = set(tags)
        tags.add(const.TAG_GRAPH)
        self.__tags = tuple(sorted([str(x) for x in tags]))

    def has_tag(self, tags):
        """Checks if a tag is associated with this object.

        Args:
            tag (str): A tag to check.

        Returns:
            bool
        """
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        return bool(set(tags) & set(self.tags))

    @property
    def ui_color(self):
        """The UI display color (RGB in 0 ~ 255 range).

        :type: tuple
        """
        if not self.__ui_color:
            return const.DEFAULT_GRAPH_UI_COLOR
        return self.__ui_color

    @ui_color.setter
    def ui_color(self, color):
        if not color:
            self.__ui_color = None
            return

        if not isinstance(color, (list, tuple)) or \
           len(color) != 3:
            raise exp.ActionError('Invalid UI color: {}'.format(color))
        for each in color:
            if not str(each).isdigit():
                raise exp.ActionError('Invalid UI color: {}'.format(color))

        if util.vector_equal(color, const.DEFAULT_GRAPH_UI_COLOR):
            self.__ui_color = None
            return

        self.__ui_color = tuple(color)

    @property
    def ui_icon(self):
        """The UI icon file name.

        :setter: Sets the ui icon file name.
        :type: str
        """
        return self.__ui_icon

    @ui_icon.setter
    def ui_icon(self, icon):
        self.__ui_icon = str(icon)

    @property
    def icon_path(self):
        """The UI icon file path.

        :type: str
        """
        if not self._icon_path:
            return const.DEF_GRAPH_ICON
        return self._icon_path

    @property
    def is_graph(self):
        """Returns True."""
        return True

    @property
    def app(self):
        """The intented app/DCC name of this object.

        :type: str
        """
        return self.__app

    def get_status(self, exec_name='main'):
        """Returns the collective execution status of this graph.

        +---------------------+--------------------------------------------+
        | ExecStatus.kRunning | If more than 1 objects are being executed. |
        +---------------------+--------------------------------------------+
        | ExecStatus.kSuccess | If all objects are successfully executed.  |
        +---------------------+--------------------------------------------+
        | ExecStatus.kFail    | If more than 1 objects failed execution.   |
        +---------------------+--------------------------------------------+
        | ExecStatus.kNone    | If none of the above applies.              |
        +---------------------+--------------------------------------------+

        Args:
            exec_name (str): The execution name. Default to "main"
                indicating the main execution.

        Returns:
            ExecStatus: The execution status.
        """
        success_count = 0
        total_count = 0

        # We need to sort objects and skip disabled so that all
        # disabled objects (including downstream) are bypassed
        for obj in self.get_sorted_objects(skip_disabled=True):
            if obj.get_status(exec_name) == const.ExecStatus.kRunning:
                return const.ExecStatus.kRunning
            elif obj.get_status(exec_name) == const.ExecStatus.kSuccess:
                success_count += 1
            elif obj.get_status(exec_name) == const.ExecStatus.kFail:
                return const.ExecStatus.kFail
            total_count += 1

        if total_count > 0 and success_count == total_count:
            return const.ExecStatus.kSuccess
        return const.ExecStatus.kNone

    def reset_status(self, exec_name='main'):
        """Resets the status for all objects owned.

        Args:
            exec_name (str): The execution name. Default to "main"
                indicating the main execution.

        Returns:
            None
        """
        if exec_name == 'main':
            self.reset_output_parameters()
        cur = self.get_status(exec_name=exec_name)
        for _, obj in self.__object_dict.items():
            obj.reset_status(exec_name)
        new = self.get_status(exec_name=exec_name)
        if cur != new:
            self.status_changed.emit(exec_name, new)

    @property
    def object_count(self):
        """The number of objects owned.

        :type: int
        """
        return len(self.__object_dict)

    # --- Referencing

    def _set_source(self, source):
        """Sets the source string of this graph.
        Source is set by the factory class. Do NOT override.
        """
        self.__source = source

    def _set_source_path(self, source_path):
        """Sets the source string of this graph.
        Source is set by the factory class. Do NOT override.
        """
        self.__source_path = source_path

    @property
    def referenced(self):
        """The referenced state of this graph.

        :type: bool
        """
        return bool(self.__source and self.__referenced)

    def import_reference(self):
        """If referenced, imports/dereferences this graph so that
        the user can make changes.

        Returns:
            None
        """
        if not self.__referenced:
            self.warn('{} is not referenced.'.format(self))
        else:
            self.__referenced = False

    def revert_reference(self):
        """Reverts this graph to the referenced state.
        **This will wipe all custom changes.**

        Returns:
            None
        """
        from mhy.protostar.lib import ActionLibrary as alib

        self.__referenced = True
        data = self._get_data()

        if not self.type_name:
            self.warn(
                'Graph {} is not associated with a source graph.'.format(self))
            return

        try:
            _, path = alib.get_graph(self.type_name)
        except BaseException:
            self.warn('Graph source not found: {}'.format(self.type_name))
            return

        if not os.path.isfile(path):
            self.warn('Graph source not found: {}'.format(path))
            return

        # read data
        self.read(path)

        # re-apply referenced state as reading data will reset it
        self.__referenced = True

        # re-apply data. only param values/scripts will be applied
        # this is because refereced state is on
        self._set_data(data)

    # --- Methods for interacting with objects in this graph

    def _next_available_object_name(self, name, exclude=None):
        """Given a requested name, returns the next available object name
        that can be used in this graph.

        Args:
            name (str): A base name to work from.
            exclude (str): A name to exclude from the current objects.

        Returns:
            str: An unique object name in this graph.
        """
        name = util.sanitize_name(name)
        cur_names = set(self.__object_dict.keys())
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

    def get_object(self, name):
        """Returns an object in this graph by name.

        Args:
            name (str): The object's short name.

        Returns:
            Action or ActionGraph: The object found.

        Raises:
            ActionError: If the object is not found.
        """
        obj = self.__object_dict.get(str(name))
        if not obj:
            raise exp.ActionError('{} not found in {}.'.format(name, self))
        return obj

    def iter_objects(self, skip_self=True):
        """Iterates through all objects in this graph in creation order.

        Args:
            skip_self (bool): If True, skip this graph itself.

        Yields:
            Action or ActionGraph: The action object or graph object.
        """
        if not skip_self:
            yield self
        for _, obj in self.__object_ordered_dict.items():
            yield obj

    '''
    def get_root_objects(self):
        """Returns a list of root objects in this graph, respects creation order.

        Root objects are the ones without input connections from any
        other objects in this graph.

        Return:
            list: A list of root objects.
        """
        roots = []
        for uuid, obj in self.__object_ordered_dict.items():
            in_objects = obj.get_connected_objects(
                input_=True, output=False, as_set=True)
            if not in_objects or \
               (len(in_objects) == 1 and in_objects.pop() in (self, obj)):
                roots.append(obj)
        return roots
    '''

    def __mark_object(
            self, obj, sorted_objects, marked_objects,
            skipped_objects, skip_disabled):
        """Marks an object in this graph.
        Used internally for traversing the graph.

        Returns:
            bool: Returns False if skip_disabled is True and this
                object or any of the upstream objects are disabled.
                In this case this object won't get marked.
        """
        if obj in marked_objects:
            return True
        if obj in skipped_objects:
            return False

        status = True
        if skip_disabled and \
           (not obj.enabled.value or obj._force_disable):
            status = False

        # mark all input objects are marked before this object
        for in_obj in obj.get_connected_objects(
                input_=True, output=False, as_set=True):
            if in_obj not in (self, obj):
                if in_obj not in marked_objects:
                    self.__mark_object(
                        in_obj, sorted_objects,
                        marked_objects, skipped_objects, skip_disabled)

        # mark this object
        if status:
            sorted_objects.append(obj)
            marked_objects.add(obj)
        else:
            skipped_objects.add(obj)

        return status

    def get_sorted_objects(self, skip_disabled=True):
        """Traverses the graph and return a list of objects sorted by
        connection dependencies and the creation order.

        Note:
            auto-skipping downstream objects from a disabled object is
            not allowed. This is because complex connections might not
            result in 1-to-1 dependencies.

        Args:
            skip_disabled (bool)
                If True, skip disabled objects.

        Return:
            list: A list of sorted objects.
        """
        sorted_objects = []
        marked_objects = set()
        skipped_objects = set()
        for obj in self.iter_objects(skip_self=True):
            self.__mark_object(
                obj, sorted_objects,
                marked_objects, skipped_objects, skip_disabled)
        return sorted_objects

    def get_iter_count(self):
        """Returns the number of iterations this graph needs to perform.
        Iter count is determined by the shortest iter parameter on this object.
        """
        iter_count = 1
        iter_params = [p for p in self.get_params() if p.param_type == 'iter']
        if iter_params:
            iter_lengths = [len(p) for p in iter_params]
            iter_count = min(iter_lengths)
        return iter_count

    def get_action_count(self, exec_name='main', recursive=False):
        """Returns the number of actions in this graph.

        Args:
            exec_name (str): If not "main", only count actions that will
                be executed by this execution type.
            recursive (bool): Include actions in all sub-graphs.
        """
        count = 0
        iter_count = self.get_iter_count()

        if exec_name:
            objects = self.get_sorted_objects(skip_disabled=True)
        else:
            objects = self.iter_objects()

        for obj in objects:
            if not obj.is_graph:
                if exec_name != 'main' and \
                   not obj._get_custom_exec_method(exec_name):
                    continue
                if obj.get_status(exec_name) != const.ExecStatus.kSuccess:
                    count += iter_count
            elif recursive:
                count += obj.get_action_count(
                    exec_name=exec_name, recursive=recursive)

        return count

    def has_object(self, obj):
        """Checks if an object exists in this graph.

        Args:
            obj (Action or ActionGraph or str): An object to check, or its name.

        Returns:
            bool
        """
        if isinstance(obj, act.ActionBase):
            return obj.name in self.__object_dict
        return str(obj) in self.__object_dict

    def add_object(self, obj):
        """Adds an object to this graph.

        Once an app/DCC dependent object is added, only objects for the same
        app/DCC can be added in the future. This restriction is auto-removed
        once all objects for this app/DCC is removed.

        Args:
            obj (Action or ActionGraph): An object to add.

        Raises:
            ActionError: If this graph is referenced.
            ActionError: If the obj is not compatible with this graph.
        """
        if self.in_reference_graph or self.referenced:
            raise exp.ActionError(
                'Can\'t modify referenced graph: {}'.format(self))

        if not self.has_object(obj):
            if self.__app and obj.app and obj.app != self.__app:
                raise exp.ActionError(
                    'Target app conflits: {} ({}) - {} ({})'.format(
                        self, self.__app, obj, obj.app))

            if self.has_object(obj.name):
                obj.name = self._next_available_object_name(obj.name)
            if obj.graph and obj.graph != self:
                obj.graph.remove_object(obj)
            self.__object_dict[obj.name] = obj
            self.__object_ordered_dict[obj.uuid] = obj
            obj.graph = self
            if not self.__app and obj.app:
                self.__app = obj.app

    def move_objects(self, objects, target_object, after=True):
        """Moves one or more objects to before or after another
        object in this graph.

        Args:
            objects (str or Action or list): One or more objects to move.
            target_object (str or Action): The object to move to.
            after (bool): If True, move after the target object.
                Otherwise move before the target object.

        Returns:
            None
        """
        # validate the target object
        if not isinstance(target_object, act.ActionBase):
            target_object = self.get_object(target_object)
        if not self.has_object(target_object):
            raise ValueError(
                'Object {} is not in {}'.format(target_object, self))

        # validate the objects to move
        if not isinstance(objects, (list, tuple)):
            objects = [objects]
        valid_objects = []
        for o in objects:
            if not isinstance(o, act.ActionBase):
                o = self.get_object(o)
            if not self.has_object(o):
                self.warn('Object {} is not in {}'.format(o, self))
            else:
                valid_objects.append(o)
        if not valid_objects:
            return

        # make a new ordered dict with the requested order
        new_dict = OrderedDict()
        for uuid, obj in self.__object_ordered_dict.items():
            if obj in objects:
                continue
            elif obj == target_object:
                if after:
                    new_dict[uuid] = obj
                for o in objects:
                    new_dict[o.uuid] = o
                if not after:
                    new_dict[uuid] = obj
            else:
                new_dict[uuid] = obj

        self.__object_ordered_dict = new_dict

    def _sync_object_key(self, key):
        """Updates a parameter entry in the internal dict."""
        if key in self.__object_dict:
            obj = self.__object_dict.pop(key)
            self.__object_dict[obj.name] = obj

    def remove_object(self, obj, force=False):
        """Removes an object from this graph.

        Args:
            obj (str or Action or ActionGraph): An object to remove.
            force (bool): If True, raise error if this object has
                output connections.

        Returns:
            Action or ActionGraph: The removed object.

        Raises:
            ActionError: If this graph is referenced.
            ActionError: If the requested object is not found in this graph.
        """
        if self.in_reference_graph or self.referenced:
            raise exp.ActionError(
                'Can\'t modify referenced graph: {}'.format(self))

        if not self.has_object(obj):
            raise exp.ActionError(
                'Object {} not found in graph {}.'.format(obj, self))
        if not isinstance(obj, act.ActionBase):
            obj = self.get_object(str(obj))
            if not obj:
                raise exp.ActionError(
                    'Object {} not found in graph {}.'.format(obj, self))

        # warns about output connection
        outputs = obj.get_connected_objects(
            input_=False, output=True, as_set=True)
        if outputs and not force:
            raise exp.PConnectionError(
                '{} has outputs to: {}'.format(obj, outputs))

        obj = self.__object_dict.pop(obj.name)
        self.__object_ordered_dict.pop(obj.uuid)
        obj.graph = None

        # update the compatible app
        self.__app = None
        for _, o in self.__object_dict.items():
            if o.app:
                self.__app = o.app
                break

        return obj

    def clear_objects(self, force=False):
        """Clears all objects (actions and action graphs) in this graph.

        Args:
            force (bool):
                If True, raise error if any object has output connections.
        """
        objects = list(self.__object_dict.values())
        for obj in objects:
            self.remove_object(obj, force=force)

    # --- Data methods

    def _get_data(self):
        """Returns the serialized data of this object.

        Returns:
            dict
        """
        data = super(ActionGraph, self)._get_data()
        data['source'] = self.__source
        doc = self.__doc
        if doc and doc not in ('None', const.DEFAULT_DOC):
            data['doc'] = doc
        tags = self.__tags
        if tags:
            data['tags'] = tags
        ui_color = self.__ui_color
        if ui_color:
            data['ui_color'] = ui_color
        ui_icon = self.__ui_icon
        if ui_icon:
            data['ui_icon'] = ui_icon
        data['referenced'] = self.__referenced
        data['objects'] = []

        if not self.referenced:
            for obj in self.iter_objects(skip_self=True):
                data['objects'].append(obj._get_data())

        return data

    def _set_data(self, data, value=True, **kwargs):
        """Applies serialized data to this object.

        Args:
            data (dict): Serialized action graph data.
            value (bool): If False, skip setting value data.

        Returns:
            None
        """
        from mhy.protostar.lib import ActionLibrary as alib

        doc = data.get('doc')
        if not doc:
            doc = ''
        self.doc = doc

        tags = data.get('tags', [])
        self.tags = tags

        self.ui_color = data.get('ui_color')
        self.ui_icon = data.get('ui_icon')

        self.__source = data['source']
        self.__referenced = data['referenced']

        # load data for this graph
        # skip all value data
        # skip parameters completely if this graph is referenced
        super(ActionGraph, self)._set_data(
            data, param=not self.referenced, value=False)

        # load objects into this graph
        # skip all value data
        if not self.referenced:
            self.clear_objects(force=True)

            for odata in data['objects']:
                src = odata['source']
                is_graph = 'objects' in odata

                try:
                    if is_graph:
                        if not odata['referenced']:
                            src = None
                        if src and not alib.has_graph(src):
                            self.warn(
                                ('Graph "{}" not found! '
                                 'Loading "{}" as an empty graph.').format(
                                     src, odata['name']))
                            src = None
                            odata['source'] = None
                            odata['referenced'] = False
                        obj = alib.create_graph(
                            source=src, name=odata['name'], graph=self)
                    else:
                        if not alib.has_action(src):
                            self.warn(
                                ('Action "{}" not found! '
                                 'Loading "{}" as a NullAction.').format(
                                     src, odata['name']))
                            src = 'default:NullAction'
                        obj = alib.create_action(
                            src, name=odata['name'], graph=self)
                    obj._set_data(odata, value=False)
                except BaseException as e:
                    self.error(
                        'Failed loading {} {}'.format(
                            'graph' if is_graph else 'action',
                            src if src else odata['name']))
                    raise e

        # apply all value data after all objects are loaded
        # so that scripts can be properly resolved
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
        super(ActionGraph, self)._set_value_data(data)
        for odata in data['objects']:
            if self.has_object(odata['name']):
                obj = self.get_object(odata['name'])
                obj._set_value_data(odata)

    def write(self, path):
        """Serializes this graph and writes the data to a JSON file on disc.

        The file must use the custom extension ``.agraph``.

        Args:
            path (str): Path to a JSON file.

        Returns:
            None
        """
        if not path.endswith(const.GRAPH_EXT):
            raise exp.ActionError('Not an action graph file: {}'.format(path))
        else:
            data = self._get_data()
            d = os.path.split(path)[0]
            if not os.path.isdir(d):
                os.makedirs(d)
            with open(path, 'w+') as f:
                json.dump(data, f, indent=2)
                self.info(
                    'Saved action graph "{}" to {}'.format(self.name, path))

    def read(self, path):
        """Reads data from the given JSON file and applies it to this graph.

        Args:
            path (str): Path to a JSON file.

        Returns:
            None
        """
        if not path.endswith(const.GRAPH_EXT):
            self.warn('Not an action graph file: {}'.format(path))
            return
        if not os.path.isfile(path):
            self.warn('File not found: {}'.format(path))
            return

        with open(path, 'r') as f:
            data = json.load(f)
            try:
                self._set_data(data)
                self.info(
                    'Loaded action graph "{}" from {}'.format(self.name, path))
            except BaseException:
                traceback.print_exc()
                raise RuntimeError(
                    'Failed reading action graph: {}'.format(path))

    def print_detail(self, verbose=False):
        """Prints nicely formatted details about this graph.

        Args:
            verbose (bool): If True, print detailed doc and parameter status.
                Otherwise only print parameter name and type.

        Returns:
            None
        """
        super(ActionGraph, self).print_detail(verbose=verbose)
        for obj in self.iter_objects(skip_self=True):
            obj.print_detail(verbose=verbose)

    def is_equivalent(
            self, other, check_referenced=True, check_child=True, **kwargs):
        """Checks if this graph and an other graph is equivalent.
        Equivalent means the object type and parameters are the same for this
        graph all all objects owned.

        Returns:
            bool: The equivalent check result.
        """
        status = super(ActionGraph, self).is_equivalent(other)
        if status:
            if check_referenced and self.referenced != other.referenced:
                self.warn(
                    'Referenced state mismatched: {} - {}'.format(
                        self, other))
                return False
            if self.object_count != other.object_count:
                self.warn('Object count mismatched: {} - {}'.format(
                    self.long_name, other.long_name))
                return False
            if check_child:
                for obj in self.iter_objects():
                    if not other.has_object(obj.name):
                        self.warn('Object not found: {}.{}'.format(
                            other.long_name, obj.name))
                        return False
                    other_obj = other.get_object(obj.name)
                    if not obj.is_equivalent(
                            other_obj, check_referenced=check_referenced):
                        return False
        return status

    # --- abstract method implementation.

    def execute(self,
                exec_name='main',
                exec_progress=None,
                mode='new',
                no_break=False,
                *args, **kwargs):
        """Executes all the objects in this graph.
        The execution stops when any object fails.

        The execution order is determined by connection dependencies and
        creation order (connection dependencies takes higher priority):

            + If objA is depending on objB, then objB is executed first.
            + If both objA and objB are depending on objC, then objC is
              executed first. The exec order of objA and objB depends on
              which one is created first.

        If there's 1 or more iterator parameter on this graph,
        the graph will be executed n times (n = the shortest iter param length).

        Args:
            exec_name (str): Name of this execution.
                If "main", run the main execution. Otherwise finds the custom
                execution method matches this name and executes it.
            exec_progress (ExecProgress): An execution progress object to use.
            mode (str): Execution mode:
                + "new": A new execution that runs through all objects.
                + "resume": Pick up the execution from where it left last time.
                + "step": Execute the next object down the line.
            no_break (bool): If True, ignore break points.
            args: Arguments to pass into each object's execution method.
            kwargs: Keyword arguments to pass into each object's
                execution method.

        Returns:
            bool: True if the execution was successful.

        Raises:
            ActionError: If the execution mode is invalid.
        """
        # validate execution mode
        if mode not in ('new', 'resume', 'step'):
            raise exp.ActionError('Invalide execution mode: {}'.format(mode))

        # get the name of this graph to use in logs.
        info_name = str(self)
        if exec_name != 'main':
            info_name = '{}.{}'.format(info_name, exec_name)

        # reset force disabled states
        for each in self.iter_objects():
            each._force_disable = False

        # go through each switcher action and disabled unselected inputs
        switchers = self.find_actions(type_='SwitchAction', recursive=False)
        for each in switchers:
            each._disable_unselected_inputs()

        # reset all object status
        if mode == 'new':
            self.reset_status(exec_name)

        old_status = self.get_status(exec_name=exec_name)

        # if this is a root graph, make a new ExecProgress object.
        if not exec_progress and not self.graph:
            count = self.get_action_count(exec_name=exec_name, recursive=True)
            exec_progress = act.ExecProgress(count)

        # get iter params and iteration count
        iter_params = [p for p in self.get_params() if p.param_type == 'iter']
        iter_count = self.get_iter_count()

        is_first = True
        exec_objects = self.get_sorted_objects(skip_disabled=True)
        for i in range(iter_count):
            # update iter param values
            for param in iter_params:
                param.iter_id = i

            # reset object status
            if mode == 'new':
                self.reset_status(exec_name)

            # execute objects in dependency order
            for obj in exec_objects:
                status = obj.get_status(exec_name)
                if status == const.ExecStatus.kSuccess and mode != 'new':
                    continue

                # check break point
                if not no_break and obj.break_point.value and \
                   mode != 'step' and (mode == 'new' or not is_first):
                    obj.break_point_reached.emit()
                    self.warn(('Reached break point at {}. Graph '
                               'execution paused... {}').format(obj, info_name))
                    new_status = self.get_status(exec_name=exec_name)
                    if old_status != new_status:
                        self.status_changed.emit(exec_name, new_status)
                    return False

                is_first = False

                # gather exec kwargs
                obj_kwargs = kwargs.copy()
                obj_kwargs['exec_name'] = exec_name
                prog = None if mode == 'step' else exec_progress
                obj_kwargs['exec_progress'] = prog
                obj_kwargs['no_break'] = no_break

                # execute the object
                if obj.is_graph:
                    obj_kwargs['mode'] = mode
                    if not obj.execute(*args, **obj_kwargs):
                        new_status = self.get_status(exec_name=exec_name)
                        if old_status != new_status:
                            self.status_changed.emit(exec_name, new_status)
                        return False
                else:
                    status = obj.execute(*args, **obj_kwargs)
                    if status == const.ExecStatus.kSuccess:
                        exec_progress.increment()

                # check step execution
                if mode == 'step':
                    self.warn('Graph execution paused... {}'.format(info_name))
                    new_status = self.get_status(exec_name=exec_name)
                    if old_status != new_status:
                        self.status_changed.emit(exec_name, new_status)
                    return False

            info = 'Graph execution complete: {}'.format(info_name)
            if iter_count > 1:
                info += ' (Iteration {})'.format(i)
            self.info(info)

        new_status = self.get_status(exec_name=exec_name)
        if old_status != new_status:
            self.status_changed.emit(exec_name, new_status)
        return True
