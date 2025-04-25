# Getting Started

This page covers basic usage and concepts of Protostar.

## Basic Usage

### List Registered Actions and Graphs

To access registered actions and graphs, first import the Action Library
and refresh its content:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()
```

List actions in the library:

``` python
# list all actions:
alib.list_actions()
# example result:
# [teamA:ActionA, teamB:ActionB, fgame:MayaActionA, fgame:HoudiniActionA, ...]

# list actions by team:
alib.list_actions(team='fgame')
# example result >> [fgame:MayaActionA, fgame:HoudiniActionA, ...]

# list actions by team and DCC:
alib.list_actions(team='fgame', app='maya')
# example result >> [fgame:MayaActionA, ...]
```

Action graphs works in similar ways:

``` python
alib.list_graphs()
alib.list_graphs(team='fgame')
```

### Instantiate and Execute Actions and Graphs

There're 2 ways of instantiating a team-specific action:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# specify the team name by adding it as a prefix to the action type argument.
action = alib.create_action('fgame:MayaActionA', name='my_action')

# specify the team name using the "team" argument
action = alib.create_action('MayaActionA', team='fgame', name='my_action')
```

If team name is not specified, Action Library will search through all
actions and instantiate the first one found.

``` python
action = alib.create_action('MayaActionA', name='my_action')
```

Configure action parameters and execute it:

``` python
action.my_string_setting.value = 'some setting'
action.execute()
```

Action graph works in similar ways:

``` python
rig = alib.create_graph('fgame:biped_rig')
rig.execute()
```

### Make an Action Graph from Scratch

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# create an empty graph
rig = alib.create_graph(name='my_rig')

# add some actions into the graph
spine = alib.create_action('fgame:SpineRig', graph=rig)
arm = alib.create_action('fgame:ArmRig', graph=rig)

# make a simple connection
spine.chest_joint >> arm.parent

# execute the graph.
# spine is executed first as arm has an input connection from it.
rig.execute()
```

### Save and Load Action Graphs

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

path = 'path/to/a/graph/file.agraph'

# load a graph from file
graph = alib.create_graph(name='empty_graph')
graph.load(path)

# make some changes to the graph
alib.create_action('NullAction', name='just_for_fun', graph=graph)

# save this graph back to the same file
graph.write(path)
```

### Graph Execution Order

When we execute an action graph, all objects (actions and sub-graphs) in
this graph is executed in a specific order. The execution order is
determined by 2 factors:

+ **Creation order**: Whichever object gets created first is executed
    first.
+ **Connection Dependencies**: A connection is established when a
    parameter is referenced another parameter's script override. For
    example: `actionA.paramA.script = '{actionB.paramB} + {actionC.paramC}'`

When connections are preset, input actions are executed first so that
the dependent action can get the their output values. In the above
example, the input actions (actionB and actionC) is executed before
actionA. **Connection dependencies takes higher priority than creation
order.**

Given the above 2 factors, there are 2 ways to enforce execution order:

1. **Create actions in the desired order:**

    ``` python
    from mhy.protostar.lib import ActionLibrary as alib

    alib.refresh()

    graph = alib.create_graph(name='empty_graph')

    actionA = alib.create_action('NullAction', graph=graph)
    actionB = alib.create_action('NullAction', graph=graph)

    graph.execute()

    # execution order: actionA -> actionB
    ```

1. **Make a connection between them:**

    ``` python
    from mhy.protostar.lib import ActionLibrary as alib

    alib.refresh()

    graph = alib.create_graph(name='empty_graph')

    actionA = alib.create_action('NullAction', graph=graph)
    actionB = alib.create_action('NullAction', graph=graph)

    actionB.outputB = actionA.inputA

    graph.execute()

    # execution order: actionB -> actionA
    ```

**What if I want to make a connection but there's no data to pass?**
Don't worry, every action carries a default `message` parameter.
It has no value but can be used to introduce dependencies:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

graph = alib.create_graph(name='empty_graph')

actionA = alib.create_action('NullAction', graph=graph)
actionB = alib.create_action('NullAction', graph=graph)

actionB.message >> actionA.message

graph.execute()

# execution order: actionB -> actionA
```

## Advanced Features

### Iterator Graph

Sometimes we want to execute a graph multiple times with slightly
different settings (e.g. rig 10 arms). Of course we can always load the
same graph multiple times and set them up separately (time-consuming!),
a better way is to encapsulate the repetitive process in an iterator
graph.

Making an iterator graph is easy: just attach 1 or more iterator
parameters to an action graph to make it iterable.

Iterator parameter is a special list parameter. The number of iterations
of a graph is determined by the length of its shortest iterator
parameter. Before each execution, the graph will increment each iterator
parameter so that it yields the next value/setting.

Below is an example of creating a 5-finger rig with an iterator graph:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# create an empty graph
graph = alib.create_graph(name='empty_graph')

# add a iterator parameter to make this graph iterable
iter_param = graph.add_dynamic_param('iter', item_type='str', name='finger_name')

# set the values to iterate over
iter_param.value = ['index', 'middle', 'ring', 'pinky', 'thumb']

# create an action in the iterator graph and connect to the iter parameter
finger_rig = alib.create_action('fgame:FingerRig', graph=graph)
iter_param >> finger_rig.name

# execute the iterator graph. FingerRig is ran 5 times, each time with
# a different name value.
graph.execute()
```

### Action Graph Referencing

An action graph is referenced by default when first loaded from the
Action Library. (Think of graphs stored in the Action Library as HDAs in
Houdini.) Referenced graphs can NOT be modified but the user can set
their parameter values and make connections. Referencing a graph allows
you to get all the developer updates automatically.

+ As a developer, be extra careful when you make changes to an
  existing graph stored in the library, as it could potentially break
  other user's work.
+ As a user, you can import a graph at anytime to remove referencing
  and make changes. You can also revert a graph back to the referenced
  state at the cost of losing all custom changes.

Example:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

# load a graph from the library. The graph is referenced by default:
graph = alib.create_graph('fgame:some_graph')
print(graph.referenced)
# >> True

# The following operations cause errors as referenced graph can NOT be modified:
alib.create_action('NullAction', graph=graph)
graph.add_dynamic_param('int', name='new_param')

# you CAN set parameter values and make connections on the referenced graph:
graph.inputA.value = 'some_value'
actionA.outputA >> graph.inputB

# you can also de-reference a graph by importing it:
graph.import_reference()
print(graph.referenced)
# >> False

# once imported, you can modify the graph to your desire.
graph.add_dynamic_param('int', name='new_param')

# reverting a graph to the referenced state:
# be aware: all custom changes will be lost!
graph.revert_reference()
print(graph.referenced)
# >> True
print(graph.has_param('new_param'))
# >> False
```

## Help & Debugging

### Execution Break Point and Stepping

Protostar provides a few ways to step through an action graph execution.
You can:

1. Add a break point at an action or sub-graph to pause the execution
   at that position.

    ``` python
    from mhy.protostar.lib import ActionLibrary as alib

    alib.refresh()

    graph = alib.create_graph(name='my_graph')

    actionA = alib.create_action('NullAction', name='actionA', graph=graph)
    actionB = alib.create_action('NullAction', name='actionB', graph=graph)

    # This will pause graph execution after actionA is executed.
    actionA.break_point.value = True

    # "new" is the default execution mode, where a fresh execution
    # of all objects within the graph is triggered.
    graph.execute(mode='new')

    print(actionA.get_status())
    # >> ExecStatus.kSuccess
    print(actionB.get_status())
    # >> ExecStatus.kNone

    # using mode "resume" to continue the last execution.
    graph.execute(mode='resume')

    print(actionA.get_status())
    # >> ExecStatus.kSuccess
    print(actionB.get_status())
    # >> ExecStatus.kSuccess
    ```

1. Step through each object one at a time.

    ``` python
    from mhy.protostar.lib import ActionLibrary as alib

    alib.refresh()

    graph = alib.create_graph(name='my_graph')

    actionA = alib.create_action('NullAction', name='actionA', graph=graph)
    actionB = alib.create_action('NullAction', name='actionB', graph=graph)

    # using mode "step" to execute the next object in the graph
    graph.execute(mode='step')

    print(actionA.get_status())
    # >> ExecStatus.kSuccess
    print(actionB.get_status())
    # >> ExecStatus.kNone

    graph.execute(mode='step')

    print(actionA.get_status())
    # >> ExecStatus.kSuccess
    print(actionB.get_status())
    # >> ExecStatus.kSuccess
    ```

### Open Action Help Page

If the developer created a documentation page for an action, open it by:

``` python
action.open_help()
```

### Get Action Details

You can print action details by:

``` python
action.print_detail()

'''
>> example result:

>> root_graph:root_actionB (default:NullAction)
-- Input Parameters:
+ message (message)
+ enabled (bool)
+ break_point (bool)
-- Output Parameters:
... None
```

``` python

action.print_detail(verbose=True)

'''
>> example result:

>> root_graph:root_actionB (Action | default:NullAction)
   | A null/empty action that does nothing when executed.
   |
   | This action can be used as a container to carry user
   | data (via dynamic parameters) through out a graph.
   |
-- Input Parameters:
 + message (message) | (static)
   | A built-in message parameter in every action.
   |
   | This parameter has no value but can be referenced
   | in script overrides to represent the owner object itself.
   + Value (On): None
   + Script (Off): None
   |
 + enabled (bool) | (static)
   | The enabled state of this object.
   + Value (On): True
   + Script (Off): None
   |
 + break_point (bool) | (static)
   | If True, stop execution when this action is completed.
   + Value (On): False
   + Script (Off): None
   |
-- Output Parameters:
   ... None
'''
```
