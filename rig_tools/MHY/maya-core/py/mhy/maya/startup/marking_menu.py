import os
import json
import traceback
from shutil import copyfile


from maya import cmds, mel, OpenMaya

import mhy.maya.nodezoo.constant as const


__all__ = ['init', 'register_marking_menu', 'toggle_marking_menu', 'ActionItem', 'MMENU_DATA']


_MMENU_ENV_VAR = 'MHY_RESOURCE_PATH'
_MMENU_ENABLED_OPT = 'MHY_Marking_Menu_Enabled'
MMENU_DATA = {}


def init():
    """Maya startup initialization."""
    register_marking_menu()
    state = marking_menu_enabled()
    if state:
        toggle_marking_menu(state)


def register_marking_menu():
    """Registers all marking menus in the marking menu environment variable."""
    env_path = os.getenv(_MMENU_ENV_VAR)
    if not env_path:
        return

    for path in set(env_path.split(os.pathsep)):
        mm_file = os.path.join(path, 'marking_menu.json')
        if not os.path.isfile(mm_file):
            continue

        with open(mm_file, 'r') as f:
            data = json.load(f)
        if data:
            if not isinstance(data, (list, tuple)):
                data = [data]
            for each in data:
                MMENU_DATA[each['menu_name']] = each['item_command']


def marking_menu_enabled():
    """Returns the current enabled state of MHY marking menu."""
    return cmds.optionVar(query=_MMENU_ENABLED_OPT)


def toggle_marking_menu(state=None):
    """Toggles or sets the enabled state of the RMB marking menu.

    Args:
        state (bool): If not None, directly set to this state.
            Otherwise toggles the enabled state.

    Returns:
        None
    """
    # find the script override based on maya version
    ver = cmds.about(version=True).split()[0]
    root_path = os.environ['MHY_MEL_OVERRIDE_PATH']
    user_path = cmds.internalVar(userScriptDir=True)
    target_paths = ['{}dagMenuProc.mel'.format(user_path), '{}contextToolsMM.mel'.format(user_path)]

    # resolve the enabled state
    if state is None:
        state = not marking_menu_enabled()

    # figure out which file to copy
    if state:
        file_paths = ['dagMenuProc_{}_mhy'.format(ver), 'contextToolsMM_{}_mhy'.format(ver)]
    else:
        file_paths = ['dagMenuProc_{}'.format(ver), 'contextToolsMM_{}'.format(ver)]

    for i, file_name in enumerate(file_paths):
        file_path = os.path.join(
            root_path, file_name + '.mel').replace('\\', '/')
        if not os.path.isfile(file_path):
            cmds.warning(
                'MHY Marking menu doesn\'t support Maya {} yet.'.format(ver))
            return
        file_paths[i] = file_path

    # copy the override file to the users script path.
    #
    # why not source the override file directly? you might ask...
    # it won't work as many internal scripts will try to source the
    # original dagMenuProc.mel and revert the override.
    #
    # copying it to a maya script path with the same name as the original
    # ensures it's always sourced. This is because Maya searches scripts
    # from interal paths to user paths and source the last one found.
    for copy_file, target_file in zip(file_paths, target_paths):
        copyfile(copy_file, target_file)
        mel.eval('source "{}"'.format(target_file))
    cmds.optionVar(intValue=(_MMENU_ENABLED_OPT, int(state)))
    OpenMaya.MGlobal.displayInfo(
        'MHY marking menun ' + ('enabled.' if state else 'disabled.'))


def create_menu_items(obj):
    """Creates marking menu items."""
    sel = cmds.ls(selection=True, type='dagNode')
    if not obj and sel:
        obj = sel[0]

    mods = cmds.getModifiers()
    mod = ''
    if (mods & 1) > 0:
        mod = '_shift'
    if (mods & 4) > 0:
        mod = '_ctrl'

    attr = '{}.{}'.format(obj, const.nodezoo_mm_attr + mod)
    if not cmds.objExists(attr):
        return

    menu_names = cmds.getAttr(attr)
    for menu_name in menu_names.split(';'):
        item_command = MMENU_DATA.get(menu_name)
        if not item_command:
            cmds.warning(
                'Marking menu not registered: {}'.format(menu_name))
            return

        try:
            exec(item_command.format(NODE='"{}"'.format(obj)))
        except BaseException as e:
            traceback.print_exc()
            cmds.warning(
                'Failed building marking menu {}: {}'.format(menu_name, e))


class ActionItem(object):
    """
    This class is a wrapper around maya.cmds.menuItem that
    register item under a namespace of a specific marking menu module.
    A dry run option is supported to cache the creation argument
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.__item = None

        dry_run = False
        col = None
        if 'dry_run' in kwargs:
            dry_run = kwargs.pop('dry_run')
        if 'collection' in kwargs:
            col = kwargs.pop('collection')

        if not dry_run:
            self.__item = cmds.menuItem(*args, **kwargs)
        if isinstance(col, list):
            col.append(self)

    def __str__(self):
        return self.__item

    @property
    def command(self):
        command = self.kwargs.get('command')
        if not command:
            command = self.kwargs.get('c')
        return command

    @property
    def label(self):
        label = self.kwargs.get('label')
        if not label:
            label = self.kwargs.get('l')
        return label
