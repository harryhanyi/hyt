"""
Global constants.
"""
import os

# Action namespace separator
SEP = ':'

ROOT_GRAPH = '__ROOT_GRAPH__'
GRAPH_EXT = '.agraph'
DEFAULT_TEAM = 'default'

DEFAULT_DOC = 'No documentation.'
DEFAULT_ACTION_UI_COLOR = (56, 55, 53)
DEFAULT_GRAPH_UI_COLOR = (49, 45, 64)

# Parameter attrs default values
PARAM_CATTR_DEFAULT = {
    'default': None,
    'dynamic': False,
    'doc': None,
    'output': False,
    'editable': True,

    'group': None,
    'priority': 0,

    'min_value': None,
    'max_value': None,
    'items': ['none'],
    'ext': None,

    'min_count': None,
    'max_count': None,
    'item_type': None,
    'key_type': None,

    'ui_label': None,
    'ui_visible': True,
}

GROUP_DEFAULT = 'Basics'
GROUP_OUTPUT = 'Outputs'
SELF_PARAM_NAME = 'message'
EXEC_PARAM_NAME = 'execution'


ICON_EXT = ('jpg', 'png', 'svg')
path = os.path.split(__file__)[0]
for i in range(3):
    path = os.path.split(path)[0]
DEF_ACTION_ICON = os.path.join(
    path, 'resource', 'icons', 'default_action.png').replace('\\', '/')
DEF_GRAPH_ICON = os.path.join(
    path, 'resource', 'icons', 'default_graph.png').replace('\\', '/')


TAG_ACTION = 'action'
TAG_GRAPH = 'action graph'


class ExecStatus():
    """Execution status enum."""

    kNone = 0
    kRunning = 1
    kSuccess = 2
    kFail = 3
