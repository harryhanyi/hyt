# FAQ

## I registered my action properly, but it won't show up in the Action Library?

+ First of all, the Action Library needs to be refershed to find newly added content:

    ``` python
    from mhy.protostar.lib import ActionLibrary as alib
    alib.refresh()
    ```

+ If it still doesn't show up, check if the `run()` method is implemented.
    - `run()` is the only abstractmethod that you have to write.
    Without it your action class will stay abstract and the Action
    Library will ignore it.

## Setting a dict parameter's script override errors out?

Since Protostar uses `{}` for parameter value referencing, using it in a
dict parameter's script override causes conflits:

``` python
# this will error!
dict_param.script = '{keyA: valueA, keyB: valueB}'
```

The work around is to call dict constructor directly:

``` python
# this works
dict_param.script = 'dict(((keyA, valueB), (keyB, valueB)))'
```
