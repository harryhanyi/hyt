"""
Utility functions that helps you write compatible code for Python2 and Python3.
"""
import os
import sys
import inspect
import gzip
from functools import partial

PYTHON_VER = sys.version_info[0]
if PYTHON_VER >= 3:
    import importlib
    import builtins
else:
    import __builtin__ as builtins
    import imp
    import importlib


def long(val):
    """Returns a long integer."""
    if PYTHON_VER >= 3:
        return builtins.int(val)
    return builtins.long(val)


def reload(module):
    """Reloads a given module."""
    if PYTHON_VER >= 3:
        importlib.reload(module)
    else:
        builtins.reload(module)


class classproperty(property):
    """Combines @classmethod and @property."""
    def __get__(self, instance, owner):
        return self.fget(owner)


class partialmethod(partial):
    """A custom partialmethod implementation.
    partialmethod is not avaialbe until Python3.4
    Copied from: https://gist.github.com/carymrobbins/8940382
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self.func, instance,
                       *(self.args or ()), **(self.keywords or {}))


# def module_exists(module_name):
#     """Checks if a module exists in the current Python environment.
#     This does **NOT** support dotted imports yet.
#     """
#     if PYTHON_VER >= 3:
#         try:
#             return importlib.util.find_spec(module_name) is not None
#         except BaseException:
#             pass
#     else:
#         try:
#             imp.find_module(module_name)
#             return True
#         except BaseException:
#             pass

#     return False


def import_module_from_path(module_path):
    """A wrapper function for importing a python module from a file path.
    Compatible with python2 and python3.5+

    Args:
        module_path (str): A path to a Python module file.

    Returns:
        module: The imported module.
    """
    tokens = os.path.splitext(module_path)[0].replace('\\', '/').split('/')

    # get all python path
    pypath = set()
    for path in os.environ.get('PYTHONPATH', '').split(os.pathsep):
        if path:
            pypath.add(path.replace('\\', '/'))

    # check if this is an existing module
    if pypath:
        root_id = None
        for i in range(1, len(tokens), 1):
            path = '/'.join(tokens[0:i])
            if path in pypath:
                root_id = i
                break

        # if the module exists, use the built-in import
        if root_id is not None and root_id < len(tokens):
            module_name = '.'.join(tokens[root_id:])
            return importlib.import_module(module_name)

    module_name = tokens[-1]
    if PYTHON_VER >= 3:
        loader = importlib.machinery.SourceFileLoader(module_name, module_path)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
    else:
        module = imp.load_source(module_name, module_path)

    return module


def filter_args(func, args, kwargs):
    """Given a function, filters a set of args and kwargs
    to make sure they can be passed in.

    Args:
        func (function): A function to work with.
        args (tuple): A list of arguments to filter.
        kwargs (dict): A dict of keyword arguments to filter.

    Returns:
        tuple: (filtered_args, filtered_kwargs)
    """
    filtered_args = args[:]
    if PYTHON_VER >= 3:
        args, varargs, varkw, _, _, _, _ = inspect.getfullargspec(func)
    else:
        args, varargs, varkw, _ = inspect.getargspec(func)

    if args and args[0] in ('self', 'cls'):
        args.pop(0)
    if not varargs:
        valid_arg_count = len(args)
        arg_count = len(filtered_args)
        if arg_count > valid_arg_count:
            filtered_args = filtered_args[:(valid_arg_count - arg_count)]

    if not varkw:
        filtered_kwargs = {}
        for key, val in kwargs.items():
            if key in args:
                filtered_kwargs[key] = val
    else:
        filtered_kwargs = kwargs

    return filtered_args, filtered_kwargs


def validate_args(func, args, kwargs):
    """Given a function, checks if args and kwargs can be passed in.

    Args:
        func (function): A function to work with.
        args (tuple): A list of arguments to check.
        kwargs (dict): A dict of keyword arguments to check.

    Returns:
        bool
    """
    if PYTHON_VER >= 3:
        args_, varargs, varkw, defaults, _, _, _ = inspect.getfullargspec(func)
    else:
        args_, varargs, varkw, defaults = inspect.getargspec(func)

    if args_ and args_[0] in ('self', 'cls'):
        args_.pop(0)

    valid_arg_len = None
    if not varargs:
        valid_arg_len = len(args_)
        if defaults:
            valid_arg_len -= len(defaults)

    valid_kwarg_len = None
    if not varkw:
        valid_kwarg_len = len(defaults) if defaults else 0

    arg_len = len(args) if args else 0
    kwarg_len = len(kwargs) if kwargs else 0

    if valid_arg_len is not None and valid_arg_len != arg_len:
        return False
    elif valid_kwarg_len is not None and valid_kwarg_len != kwarg_len:
        return False

    return True


def gzip_export(data, file_path):
    """
    Export string typed data to a file path using gzip compression
    Args:
        data(str): String typed data
        file_path(str): File path to export data to

    """
    if PYTHON_VER >= 3:
        with gzip.open(file_path, "wt") as f:
            f.write(data)
    else:
        bytes_data = data.decode('utf-8')
        with gzip.open(file_path, "w") as f:
            f.write(bytes_data)


def format_arg_spec(func):
    """
    Format the signature of a callable function
    Args:
        func(builtin_function_or_method): A function to inspect

    Returns:
        str: Formatted argument inspect
    """
    if PYTHON_VER < 3:
        return inspect.formatargspec(*inspect.getargspec(func))
    elif sys.version_info[0] > 4:
        return str(inspect.signature(func))
    else:
        return inspect.formatargspec(*inspect.getfullargspec(func))
