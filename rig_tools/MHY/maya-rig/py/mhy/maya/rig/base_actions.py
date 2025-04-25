"""
Base actions of various types
"""
from mhy.protostar.core.action import MayaAction


class BaseRigUtilAction(MayaAction):

    _TAGS = ['rig util']
    _UI_COLOR = (196, 176, 75)
    _UI_ICON = 'utility'


class BaseRigDataAction(MayaAction):

    _TAGS = ['rig data']
    _UI_COLOR = (61, 138, 104)
    _UI_ICON = 'data'


class BaseRigSkelAction(MayaAction):

    _TAGS = ['rig data']
    _UI_COLOR = (61, 138, 104)
    _UI_ICON = 'skeleton'


class BaseSceneAction(MayaAction):

    _TAGS = ['scene']
    # _UI_COLOR = (68, 68, 68)
    _UI_ICON = 'maya'
