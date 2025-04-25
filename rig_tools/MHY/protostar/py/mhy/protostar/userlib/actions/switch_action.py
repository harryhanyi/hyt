from mhy.protostar.core.action import Action, ActionBase
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp


def _skip_object(obj, skipped_actions):
    obj._force_disable = True
    skipped_actions.add(obj)

    for upstream in obj.get_connected_objects(
            input_=True, output=False):
        if upstream.graph != obj.graph:
            continue

        downstream = upstream.get_connected_objects(
            input_=False, output=True, as_set=True)
        if not (downstream - skipped_actions):
            _skip_object(upstream, skipped_actions)


class SwitchAction(Action):
    """An action that switches a list of input values
    base on a selector index.

    If the input values are connected to other action/graph's
    built-in "message" parameters, the unselected input actions
    will be skipped at execution time.
    """

    _TAGS = ['util']

    @pa.int_param(default=0, min_value=0)
    def selector(self):
        """The selector index."""

    @pa.list_param()
    def inputs(self):
        """A list of input values to switch."""

    @pa.pyobject_param(output=True)
    def output(self):
        """The output value (selected input)."""

    def _validate_selector(self):
        """Checks if the current selector index is out of range."""
        i = self.selector.value
        value_len = len(self.inputs)

        if value_len == 0:
            return
        if i > value_len - 1:
            raise exp.ActionError('Selector value out of range.')

    def _disable_unselected_inputs(self):
        """Force disable unselected input networks, if we're
        switching between actions."""
        self._validate_selector()
        index = self.selector.value

        skipped_actions = set()
        for i, each in enumerate(self.inputs.value):
            if not isinstance(each, ActionBase) or i == index:
                continue
            _skip_object(each, skipped_actions)

    def run(self):
        """Executes this action."""
        self._validate_selector()
        self.output.value = self.inputs[self.selector.value]
