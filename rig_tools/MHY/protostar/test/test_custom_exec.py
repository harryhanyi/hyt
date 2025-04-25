import os
import unittest

from mhy.protostar.core.action import custom_exec_method, Action
from mhy.protostar.constants import DEFAULT_TEAM, ExecStatus
from mhy.protostar.lib import LIB_ENV_VAR
from mhy.protostar.lib import ActionLibrary as alib


# Add the userlib path in this module
path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
path = os.path.join(path, 'py', 'mhy', 'protostar', 'userlib')
if LIB_ENV_VAR not in os.environ:
    os.environ[LIB_ENV_VAR] = path
else:
    os.environ[LIB_ENV_VAR] += os.pathsep + path


alib.refresh()


class TestActionCustomExecution(unittest.TestCase):
    """
    Test action custom executions
    """

    def test_custom_exec(self):

        class TestAction(Action):

            @custom_exec_method
            def my_custom_exec(self, a=1, b=2):
                pass

            def run(self):
                pass

        alib._ACTION_DICT[DEFAULT_TEAM]['TestAction'] = TestAction

        graph = alib.create_graph()

        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('TestAction', name='actionB', graph=graph)
        actionC = alib.create_action('TestAction', name='actionB', graph=graph)

        exec_name = 'my_custom_exec'

        self.assertEqual(actionB.get_custom_exec_names(), [exec_name])
        self.assertIsNone(actionA._get_custom_exec_method(exec_name))
        self.assertTrue(bool(actionB._get_custom_exec_method(exec_name)))
        self.assertTrue(bool(actionC._get_custom_exec_method(exec_name)))

        actionA.execute(exec_name=exec_name, a=1, b=2)
        self.assertEqual(actionA.get_status(exec_name), ExecStatus.kNone)
        actionB.execute(exec_name=exec_name, a=1, b=2)
        self.assertEqual(actionB.get_status(exec_name), ExecStatus.kSuccess)
        actionC.execute(exec_name=exec_name, a=1, b=2)
        self.assertEqual(actionC.get_status(exec_name), ExecStatus.kSuccess)

        graph.reset_status(exec_name=exec_name)
        self.assertEqual(actionA.get_status(exec_name), ExecStatus.kNone)
        self.assertEqual(actionB.get_status(exec_name), ExecStatus.kNone)
        self.assertEqual(actionC.get_status(exec_name), ExecStatus.kNone)

        graph.execute(exec_name=exec_name, a=1, b=2)
        self.assertEqual(actionA.get_status(exec_name), ExecStatus.kNone)
        self.assertEqual(actionB.get_status(exec_name), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(exec_name), ExecStatus.kSuccess)
        self.assertEqual(graph.get_status(exec_name), ExecStatus.kNone)
