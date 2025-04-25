from mhy.protostar.core.action import Action


class _TestABC(Action):
    """A test action.
    """
    pass


class NullAction(Action):
    """A null/empty action that does nothing when executed.

    This action can be used as a container for user data
    (via dynamic parameters).
    """

    _TAGS = ['util']

    def run(self):
        """ Null action doesn't do anything. """
        pass
