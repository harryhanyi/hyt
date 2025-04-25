"""
Patch __import__ to allow skip import errors.
Useful for inspecting a module without actually using it.

Usage:

.. code:: python

    # this errors.
    import non.exist.module

    # no more error.
    with tryimport():
        import non.exist.module
"""

from contextlib import contextmanager
from types import ModuleType

# python2 and 3 compatible
    

try:
    import builtins as bt
    # Check if module has __import__ method in case
    # future package has installed aliases before 
    bt.__import__ 
except BaseException:
    import __builtin__ as bt


_TRY_IMPORT_ENABLED = False


class _DummyModule(ModuleType):
    def __getattr__(self, key):
        return _DummyModule(key)
    __all__ = []   # support wildcard imports


def __tryimport__(*args, **kwargs):
    if _TRY_IMPORT_ENABLED:
        try:
            return old_import(*args, **kwargs)
        except BaseException:
            return _DummyModule(args[0])
    else:
        return old_import(*args, **kwargs)


old_import, bt.__import__ = bt.__import__, __tryimport__


@contextmanager
def tryimport():
    """A contextmanager that allows an operation to be done without
    raising import errors."""
    global _TRY_IMPORT_ENABLED
    _TRY_IMPORT_ENABLED = True
    yield
    _TRY_IMPORT_ENABLED = False
