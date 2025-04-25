import mhy.maya.nodezoo.data._patch


def refresh():
    """
    Refresh all registered nodezoo classes

    """
    import sys
    import imp
    import inspect
    from mhy.maya.nodezoo._manager import _NODE_TYPE_LIB

    root_module = 'mhy.maya.nodezoo'
    _NODE_TYPE_LIB.clear()
    for key, value in sys.modules.items():
        if value:
            if root_module in key and key != "mhy.maya.nodezoo._manager" and key != "mhy.maya.nodezoo.data._patch":
                # Need to exclude _manager because it will empty factory cache
                imp.reload(value)
            else:
                for name, obj in inspect.getmembers(value):
                    if obj and inspect.isclass(obj):
                        if root_module in repr(obj):
                            imp.reload(value)
                            break
                        bases = obj.__bases__
                        if bases and root_module in repr(bases[0]):
                            imp.reload(value)
                            break
