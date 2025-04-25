import os
import json
import maya.cmds as cmds

import mhy.maya.startup.constants as constants
import mhy.maya.startup.action as action

hot_key_library = dict()
hot_key_set_name = 'MHY_hotkey'

__all__ = ['init_hot_key']


def init_hot_key(blacklist=None):
    """
    Go through hot_key.json file under MHY_RESOURCE_PATH, register hot keys
    under MHY_hotkey hot key set

    Args:
        blacklist(None or list): Skip hot keys in the black list if given

    """

    print('[MHY] initializing hot key...')
    global hot_key_library
    resource_path_var = os.environ.get(constants.resource_var)
    resource_paths = resource_path_var.split(os.pathsep)
    for path in resource_paths:
        file_path = os.path.join(path, constants.hot_key_file_name)
        file_path = file_path.replace('\\', '/')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                if not f:
                    continue
                data = json.load(f)
                if data:
                    for key, val in data.items():
                        current_val = hot_key_library.get(key, [])
                        if isinstance(val, list):
                            current_val.extend(val)
                        else:
                            current_val.append(val)
                        hot_key_library[key] = current_val

    if not cmds.hotkeySet(hot_key_set_name, exists=True):
        cmds.hotkeySet(hot_key_set_name, current=True)

    for hot_key_group, hot_key_data_list in hot_key_library.items():
        if blacklist and hot_key_group in blacklist:
            continue

        for hot_key_data in hot_key_data_list:
            action_name = hot_key_data.get('action')
            if not action:
                continue
            action_data = action.action_library.get(action_name)
            if not action_data:
                continue
            command = action_data.get('command')
            if not command:
                continue
            source_type = "python"
            if ':' in command:
                st, command = command.split(':', 1)
                if st.upper() == 'MEL':
                    source_type = 'mel'

            key_shot = hot_key_data.get('key')
            annotation = action_data.get('annotation')
            if cmds.runTimeCommand(action_name, exists=True, query=True):
                cmds.runTimeCommand(action_name, delete=True, edit=True)
            cmds.runTimeCommand(
                action_name,
                commandLanguage=source_type,
                command=command,
                annotation=annotation,
                category=hot_key_group,
            )

            name_command = cmds.nameCommand(
                '{}Command'.format(action_name),
                annotation=annotation,
                sourceType=source_type,
                command=action_name)

            release_mode = hot_key_data.get('release')
            if release_mode:
                cmds.hotkey(keyShortcut=key_shot, releaseName=name_command)
            else:
                cmds.hotkey(keyShortcut=key_shot, name=name_command)
