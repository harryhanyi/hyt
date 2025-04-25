import os

from mhy.protostar.core.action import Action
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp


class ScriptAction(Action):
    """This action uses all its dynamic parameters to execute a Python script.
    Use either ``input_script`` parameter or ``input_script_file`` parameter
    to define the script you wish to execute.

    + All input dynamic parameters will be passed into the script
      as local variables.
    + All output dynamic parameters will be updated to match
      variables with the same name in the script.

    **Note**: This action gives you the ultimate freedom to do anything with
    Python. However, with great power comes great responsibility. I recommend
    only use it for experimental purposes or one-off senarios, otherwise
    write a proper action.
    """

    _TAGS = ['util']

    @pa.str_param()
    def input_script(self):
        """A python script to run."""

    @pa.file_param(ext='py')
    def input_script_file(self):
        """An external script file to run."""

    def run(self):
        """Executes this action."""

        script = self.input_script.value
        script_file = self.input_script_file.value

        # validate script input
        if not script and not script_file:
            return
        elif script and script_file:
            raise exp.ParameterError(
                ('Both script and script_file are not empty, '
                 'use only one of them.'))
        elif script_file and not os.path.isfile(script_file):
            raise exp.ParameterError(
                'Script file not found: {}'.format(script_file))

        # get global variables from dynamic input parameters
        locals_ = {}
        for param in self.get_params(
                input_=True, output=False, static=False, dynamic=True):
            if param.script_enabled and param.script:
                locals_[param.name] = param.value
            elif param.param_type == 'iter':
                locals_[param.name] = param.iter_value
            else:
                locals_[param.name] = param.value

        # execute the script
        if script_file:
            script = open(script_file).read()
        exec(script, {}, locals_)

        # update dynamic output parameters
        for param in self.get_params(
                input_=False, output=True, static=False, dynamic=True):
            if param.name in locals_:
                param.value = locals_[param.name]
