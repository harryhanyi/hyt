import os
import unittest

from mhy.protostar.lib import LIB_ENV_VAR
from mhy.protostar.lib import ActionLibrary as alib

# Add the userlib path in this module
this_dir = os.path.dirname(os.path.realpath(__file__))
path = os.path.split(this_dir)[0]
path = os.path.join(path, 'py', 'mhy', 'protostar', 'userlib')
if LIB_ENV_VAR not in os.environ:
    os.environ[LIB_ENV_VAR] = path
else:
    os.environ[LIB_ENV_VAR] += os.pathsep + path


alib.refresh()


class TestBuiltins(unittest.TestCase):

    def test_script_action(self):
        graph = alib.create_graph()
        script = alib.create_action('ScriptAction', name='script', graph=graph)
        script.add_dynamic_param('int', name='x', default=2)
        script.add_dynamic_param('float', name='y', default=4.3)
        script.add_dynamic_param('float', name='z', output=True)

        script.input_script.value = """
def sum(a, b):
    return a + b

z = sum(x, y)
"""
        graph.execute()
        self.assertEqual(script.z.value, 6.3)

        script.input_script_file.value = os.path.join(this_dir, 'runtime_script.py')
        script.input_script.value = ''
        graph.execute()
        self.assertEqual(script.z.value, 106.3)
