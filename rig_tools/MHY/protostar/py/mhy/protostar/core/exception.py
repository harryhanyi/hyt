"""
Exceptions
"""


class ActionError(Exception):
    """Generic action error."""
    pass


class ParameterError(Exception):
    """Generic parameter error."""
    pass


class PConnectionError(Exception):
    """Parameter connection error."""
    pass


class PScriptError(Exception):
    """Parameter script error."""
    pass
