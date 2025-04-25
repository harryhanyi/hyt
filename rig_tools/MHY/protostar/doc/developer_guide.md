# Developer Guide

This page demonstrates the workflow of making custom actions and action
graphs.

## Write an Action Class

Actions are written as Python classes by extending the generic base `Action`
class, or a DCC-specific base action class. Here is a simple example:

``` python
import maya.cmds as cmds

from mhy.protostar.core.action import MayaAction
import mhy.protostar.core.parameter as pa


class MakeSphere(MayaAction):
    """A simple action that makes a sphere in Maya
    with a specified radius.
    """

    # a link to the help page
    _HELP_URL = 'https://link/to/my/help/page'

    # --- input parameters

    @pa.float_param(default=2, min_value=0, max_value=5)
    def input_radius(self):
        """The input radius of the sphere."""

    # --- output parameters

    @pa.str_param(output=True)
    def output_sphere(self):
        """Name of the sphere created by this action."""

    # --- mandatory execution method

    def run(self):
        """The core execution code."""
        # get input parameter values
        radius = self.input_radius.value

        # Make the sphere!
        sphere = cmds.polySphere(radius=radius, ch=False)

        # set the output parameter values
        self.output_sphere.value = sphere

    # --- optional execution methods

    def start(self):
        """This method is executed before run()."""
        print('My execution is about to start!')

    def end(self):
        """This method is executed after run()."""
        print('My execution is finished!')
```

When the user call `action.execute()`, the 3 execution methods are ran
in the order of `start()` -> `run()` -> `end()`. The execution
status is updated after the execution:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

action = alib.create_action('MakeSphere', name='my_action')
action.execute()
print(action.get_status())
# >> ExecStatus.kSuccess
```

**What if I need a secondary execution process outside of the main `execute()`?**

We got you covered! You can implement custom execution methods on an
action by simply tagging a method with the `custom_exec_method`
decorator.

``` python
from mhy.protostar.core.action import Action, custom_exec_method


class MyAction(Action):

    def run(self):
        """This is the mandatory execution method."""
        print('this is the mandatory execution!')

    @custom_exec_method
    def my_exec(self, a, b=1):
        """This is a custom execution method."""
        print('this is my custom execution!')
```

A custom execution method can be called from the action directly, or
from the parent graph. When called from the graph, all action with this
method implemented will be called and status tracked.

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# make an empty graph
graph = alib.create_graph(name='root_graph')

null = alib.create_action('NullAction', graph=graph)
customA = alib.create_action('MyAction', graph=graph)
customB = alib.create_action('MyAction', graph=graph)

# trigger the main execution
graph.execute()
print(null.get_status(), customA.get_status(), customB.get_status())
# >> ExecStatus.kSuccess, ExecStatus.kSuccess, ExecStatus.kSuccess
# all 3 actions are executed successfully.

# trigger the custom execution
graph.execute(exec_name='my_exec', a=1, b=2)
print(null.get_status('my_exec'), customA.get_status('my_exec'), customB.get_status('my_exec'))
# >> ExecStatus.kNone, ExecStatus.kSuccess, ExecStatus.kSuccess
# null is skipped as it doesn't have custom execution method ``my_exec()``
```

## Make a Library Graph

Library graphs are action graphs stored in a Protostar library path discoverable
by the ActionLibrary class. This allows users to use them in their graphs through
referencing or importing. The idea of library graph is very similar to HDAs in Houdini.

Below are the steps of making a library graph:

1. Make an action graph to encapsulate a desired process.
1. [Optional] Promote certain input and output parameters from the
   objects to the graph.
    + This allows the user to pass data in and out of the graph.
1. Save the graph in a registered userlib path.
    + See [the next section](#register-actions-and-graphs) to learn more.

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# make an empty graph
my_graph = alib.create_graph(name='my_graph')

# create a procedure in the graph
actionA = alib.create_action('MakeSphere', graph=my_graph)
actionB = alib.create_action('AssignShader', graph=my_graph)
actionA.output_sphere >> actionB.input_object

# promote parameters for the user to access
actionA.promote('input_radius')
actionB.promote('output_shader')

# save the graph in userlib
my_graph.write('some/userlib/file/path/make_colored_sphere.agraph')
```

Once saved, you can access this library graph from the Action Library:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# load my library graph and adjust settings
my_graph = alib.create_graph('make_colored_sphere')
my_graph.input_radius.value = 10

# execute to make a colored sphere!
my_graph.execute()
```

## Register Actions and Graphs

Actions and graphs are NOT accessible by the user until they're
registered in the Action Library. Here's the register process:

1. Create a `userlib` folder in your code repository. Store actions and
   graphs following this folder structure:

    ```
    ../userlib/actions/my_action_A.py
    ../userlib/actions/my_action_B.py
    ../userlib/graphs/my_graph_A.agraph
    ../userlib/graphs/my_graph_B.agraph
    ```

1. Add the `userlib` path to environment variable `PROTOSTAR_LIB_PATH`.
   If you're using the MHY launcher, add it to your package's `env.json`:

    ``` json
    {
        "PROTOSTAR_LIB_PATH": "./py/mhy/protostar/userlib"
    }
    ```

1. [Optional] Create a team config file under `userlib` called
   `team_config.json`. Specify your `team_name` in here:

    ``` json
    {
        "team_name": "fgame"
    }
    ```

    If `team_name` is not specified, all actions and graphs will be added to
    a default team called `default`. `team_name` is the only team config
    setting we have at the moment.

Once complete, your actions and graphs will be accessible from the
Action Library.
