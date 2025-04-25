"""

Initialize maya shelf at startup

"""
import os
import sys
import json
import maya.cmds as cmds
from PySide2 import QtWidgets, QtGui
import maya.OpenMayaUI as OpenMayaUI
import shiboken2

import mhy.maya.startup.constants as constants
import mhy.maya.startup.action as action

__all__ = ['init_shelf', 'clear_existing_shelf']
menu_library = dict()


def init_shelf():
    """
    Go through shelf.json file under MHY_RESOURCE_PATH, register shelf and shelf buttons

    """
    print('[MHY] initializing shelf...')
    global menu_library
    resource_path_var = os.environ.get(constants.resource_var)
    resource_paths = resource_path_var.split(os.pathsep)
    for path in resource_paths:
        file_path = os.path.join(path, constants.shelf_file_name)
        file_path = file_path.replace('\\', '/')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                if not f:
                    continue
                data = json.load(f)
                if data:
                    for key, val in data.items():
                        current_val = menu_library.get(key, [])
                        if isinstance(val, list):
                            current_val.extend(val)
                        else:
                            current_val.append(val)
                        menu_library[key] = current_val

    for shelf_name, data in menu_library.items():
        clear_existing_shelf(shelf_name)
        for button_data in data:
            if 'action' not in button_data:
                continue
            action_name = button_data.pop('action')
            if not action_name:
                continue
            action_data = action.action_library.get(action_name)
            if not action_data:
                continue
            cmds.setParent(shelf_name)
            button_data = {str(key): val for key, val in button_data.items()}
            command = action_data.get('command', "")

            icon = action_data.get('icon', "")

            command, source_type = action.resolve_command_source(command)

            button_data['command'] = command
            button_data['sourceType'] = source_type
            if icon:
                button_data['image'] = icon

            annotation = button_data.get('annotation')
            if not annotation:
                annotation = action_data.get('annotation')

            if not annotation:
                annotation = action_name

            button_data['annotation'] = annotation
            menu_item = list()
            menu_item_python = list()
            menu_icons = list()

            children_actions = list()
            if 'children' in button_data:
                children_actions = button_data.pop('children')
            if children_actions:
                for child in children_actions:
                    child_action_name = child.pop('action')
                    child_action_data = action.action_library.get(child_action_name)
                    if not child_action_data:
                        continue
                    child_command = child_action_data.get('command')
                    if not child_command:
                        continue

                    child_command, child_source_type = action.resolve_command_source(child_command)

                    icon = child_action_data.get('icon')
                    if icon:
                        icon = action.resolve_icon_path(icon)
                    menu_item.append([child_action_name, child_command])
                    menu_item_python.append(child_source_type == 'python')
                    menu_icons.append(icon)

            help_link = action_data.get('help_link')
            if help_link:
                menu_item.append(['Help',
                                  "from mhy.maya.startup.action import open_link; open_link('{}')".format(help_link)])
                menu_item_python.append(True)
                menu_icons.append(action.resolve_icon_path('help.png'))

            menu_item_python = [idx for idx, i in enumerate(menu_item_python) if i]

            button_data['menuItemPython'] = menu_item_python
            button_data['menuItem'] = menu_item
            shelf_button = cmds.shelfButton(**button_data)
            pop_menu = cmds.shelfButton(shelf_button, query=True, popupMenuArray=True)
            if pop_menu:
                pop_menu = pop_menu[0]
                sb_control = OpenMayaUI.MQtUtil.findControl(pop_menu)
                if sys.version_info[0] == 3:
                    menu_widget = shiboken2.wrapInstance(int(sb_control), QtWidgets.QMenu)
                else:
                    menu_widget = shiboken2.wrapInstance(long(sb_control), QtWidgets.QMenu)
                actions = menu_widget.actions()
                for action_inst, icon in zip(actions, menu_icons):
                    if icon:
                        action_inst.setIcon(QtGui.QIcon(icon))


def clear_existing_shelf(name):
    """
    Clear existing shelf of the givn name
    Args:
        name(str): A shelf name

    """
    if cmds.shelfLayout(name, exists=True):
        if cmds.shelfLayout(name, query=True, ca=True):
            for each in cmds.shelfLayout(name, query=True, childArray=True):
                cmds.deleteUI(each)
    else:
        cmds.shelfLayout(name, parent="ShelfLayout")
