import os
import unittest

from mhy.protostar.lib import LIB_ENV_VAR
from mhy.protostar.lib import ActionLibrary as alib

# Add the userlib path in this module
path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
root = os.path.dirname(path)
path1 = os.path.join(root, 'protostar', 'py', 'mhy', 'protostar', 'userlib')
path2 = os.path.join(root, 'maya-rig', 'py', 'mhy', 'maya', 'rig', 'userlib')
if LIB_ENV_VAR not in os.environ:
    os.environ[LIB_ENV_VAR] = path1
else:
    os.environ[LIB_ENV_VAR] += os.pathsep + path1


@unittest.skipIf(not os.path.isdir(path2), 'maya-rig not found.')
class TestImport(unittest.TestCase):

    def setUp(self):
        os.environ[LIB_ENV_VAR] += os.pathsep + path2

    def test_tryimport(self):
        alib.refresh()
        # with tryimp.tryimport():
        #     from mhy.maya.nodezoo.attribute import Attribute
        self.assertTrue('mhy' in alib._ACTION_DICT)
        self.assertTrue('WorldOffset' in alib._ACTION_DICT['mhy'])

    def tearDown(self):
        os.environ[LIB_ENV_VAR] = os.environ[LIB_ENV_VAR].replace(
            os.pathsep + path2, '')
