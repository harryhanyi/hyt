class NodeClassInitError(Exception):
    """
    Raised when initialize Node class using factory logic
    """


class MayaObjectError(Exception):
    """
    Raised when dealing with MObject
    """


class MayaAttributeError(Exception):
    """
    Error occurred about maya attribute
    """


class ObjectNotFoundError(Exception):
    """ An error raised when failed to find maya object """
