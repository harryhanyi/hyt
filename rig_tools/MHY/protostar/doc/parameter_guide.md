# Parameter Guide

Actions and action graphs often come with built-in parameters.
Parameters are used to receive user inputs and pass data through the
graph.

## Input Parameter vs Output Parameter

Input parameters are used to receive user inputs and connections.
Output parameters updated by the action at the end of its execution.
They are NOT settable by the user. Parameters can be connected by
`output_param >> input_param`, or `input_param >> input_param`.

## Static Parameter vs Dynamic Parameter

Static parameters are built-in parameters in an action. Dynamic
parameters are created by the user at runtime. It allows the user to
pass extra user data through the graph.

## Default Parameters

All actions and graphs comes with 3 default parameters:

+ **message** A built-in message parameter in every action.
  This parameter has no value but can be referenced
  in script overrides to represent the owner object itself.
  (see also: [Graph Execution Order](getting_started.html#graph-execution-order))

+ **enabled** A Boolean parameter that controls the enabled state of an action
  or graph. Disabling an object will also disable all downstream objects that
  depends on it.

+ **break_point** A Boolean parameter that holds the break_point state of an
  action or graph. if True, the main execution will be paused after the execution
  of this action or graph.

## Set or Connect Parameter Values

Set a parameter's value using its `value` property:

``` python
action.param_name.value = 'some_value'
```

Create dynamic parameters:

``` python
dyn_param = action.add_dynamic_parameter(
    'int', name='dyn_param_name',
    default=2, min_value=1, max_value=3)
dyn_param.value = 4
print(dyn_param.value)
# >> 3
# the value is clamped to maximum 3
```

Connect parameters

``` python
# the following 3 approaches for establishing connections are equivalent:
actionA.output_param >> actionB.input_param
actionA.output_param.connect(actionB.input_param)
actionA.connect('output_param' actionB, 'input_param')
```

## Parameter Script Override

User can override parameter values with Python scripts. Protostar
supports 2 types of Python scripts: **single-line expressions** and
**multi-line code blocks**.

+ Examples of single-line expression:
  + `int_param.script = '1 + 2'` (equivalent to `int_param.value = 3`)
  + `my_param.script = '{actionA.paramA}'` (equivalent to
        `actionA.paramA >> my_param`)
  + `my_param.script = '{actionA.paramA} + {actionB.paramB}'`
+ Examples of multi-line code block (written as a function body):

    ``` python
    my_param.script = """
    if {actionA.paramA} > 0:
        return 'foo'
    return 'bar'
    """
    ```

Note that `{}` is used to reference other parameters in a script
override. Protostar allows 2 types of value referencing:

+ Reference parameters within the same action graph:
    `{ACTION_SHORT_NAME.PARAMETER_NAME}`
+ Reference environment variables: `{$ENV_VARIABLE_NAME}`

## Passing Data in and out of Sub-graphs

Parameter connections are only allowed within a given action graph. Here
is how to pass data into a sub-graph:

1. Promote desired parameters from sub-actions onto the sub-graph.
   This will copy the parameter and form a connection:
   `sub-graph.promoted_param >> sub-action.promoted_param`
1. Make connections in the parent graph:
   `action_in_parent_graph.param >> sub-graph.promoted_param`

Example:

``` python
from mhy.protostar.lib import ActionLibrary as alib

alib.refresh()

root_graph = alib.create_graph(name='root_graph')
root_action = alib.create_action('some_action', name='root_action', graph=root_graph)

sub_graph = alib.create_graph(name='sub_graph', graph=root_graph)
sub_action = alib.create_action('some_action', name='sub_action', graph=sub_graph)

# this will error - Connecting parameters between 2 graphs are now allowed.
root_action.output_param >> sub_action.input_param

# the correct way: going through a promoted parameter on the sub-graph:
sub_action.promote('input_param')
root_action.output_param >> sub_graph.input_param

# we can also promote output parameters to pass data back into the root graph:
sub_action.promote('other_output_param')
other_root_action = alib.create_action('some_action', name='other_root_action', graph=root_graph)
sub_graph.other_output_param >> other_root_action.input_param
```

You might be wondering, why can't I just connect `root_action` and `sub_action` directly?

Well, we need to ensure graphs are self-contained, this is essential for
allowing graph sharing and referencing. Check out [the graph referencing
documentation](getting_started.html#action-graph-referencing) for more
examples.

## Primitive Parameter Types

+ **message**: Message parameters have no value but can be referenced
  in script overrides to represent the owner object itself.
+ **bool**: Boolean type parameter
+ **vector2**: Vector2 type parameter
+ **vector3**: Vector3 type parameter
+ **rgb**: Color RGB type parameter, range from 0 - 255.
+ **int**: Integer type parameter
+ **float**: Float type parameter
+ **enum**: Enum type parameter. Usage example:

    ``` python
    action.add_dynamic_param(
        'bool', name='my_param', items=('optionA', 'optionB'), default=0)
    print(action.my_param.value)
    # >> 0
    print(action.my_param.enum_value)
    # >> 'optionA'
    ```

+ **str**: string type parameter
+ **dir**: directory path parameter
  + Works the same way as string parameter.
  + Ensures the value is a directory path.
+ **file**: file path parameter
  + Works the same way as string parameter.
  + Ensures the value is a file path.
  + You can specify the file extension as well:
    `action.add_dynamic_param('file', ext='json')`.
+ **callback**: Callback parameter. Used to call a method in the owner
    object, or call a partial object directly.
  + Callback parameters can ONLY be static.

## Item Parameter Types

### List Parameter

A list parameter is essentially a container of sub-parameters(items) of
a given type. Protostar allows accessing the list parameter as a whole
or accessing each item separately.

Create a list parameter of int type:

``` python
list_param = action.add_dynamic_param('list', item_type='int', name='my_list')
```

Create a list parameter with length requirement but no enforced type:

``` python
list_param = action.add_dynamic_param('list', name='my_list', min_count=1, max_count=3)
```

Append items

``` python
value = 10
list_param.append(value)
list_param.append(value)
print(list_param.value)
# >> [10, 10]
```

Set list value directly:

``` python
list_param.value = (0, 1, 2)
```

2 ways to access list values:

``` python
print(list_param.value)
# >> [0, 1, 2]
print(list_param[1])
# >> 1
```

Script-override a list parameter:

``` python
list_param.script = '{other_action.other_list_param}'
```

Reference an list item:

``` python
param.script = '{other_action.list_param}[1]'
```

### Iterator Parameter

Iterator parameter is a special list parameter. It is used to make a
graph iterable. Check out the [Iterator Graph](getting_started.html#iterator-graph)
section for more info.

### Dict Parameter

A dict parameter is a container for key:item pairs. OrderedDict is used internally
to enforce key orders.

Example:

Create a dict parameter with enforced key and item types:

``` python
dict_param = action.add_dynamic_param('dict', key_type='int', item_type='str', name='my_dict')
```

Create a dict parameter with length requirement but no enforced types:

``` python
dict_param = action.add_dynamic_param('dict', min_count=1, max_count=3, name='my_dict')
```

Add items into the dict parameter:

``` python
dict_param['a'] = 'item_a'
dict_param[1] = 'item_b'
```

Set dict value directly:

``` python
dict_param.value = {'a': 'item_a', 1: 'item_b'}
```

2 ways to access dict values:

``` python
print(dict_param.value)
# >> OrderedDict((('a', 'item_a'), (1, 'item_b')))
print(dict_param[1])
# >> 'item_b'
```

Script-override a dict parameter:

``` python
dict_param.script = '{other_action.other_dict_param}'
```

Reference a dict item:

``` python
param.script = '{other_action.dict_param}["key"]'
```
