"""
Register actions from MHY_RESOURCE_PATH environment
"""
import os
import json
import subprocess
import sys

import mhy.maya.startup.constants as constants

__all__ = ['load_actions', 'open_link', 'resolve_command_source', 'resolve_icon_path']

action_library = dict()


def load_actions():
    """
    Go through action.json file under MHY_RESOURCE_PATH, load and cache registered actions
    in the global action_library var

    """
    resource_path_var = os.environ.get(constants.resource_var)
    resource_paths = resource_path_var.split(os.pathsep)
    for path in resource_paths:
        file_path = os.path.join(path, constants.action_file_name)
        file_path = file_path.replace('\\', '/')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if data:
                    action_library.update(data)


def open_link(url):
    """
    Open an external url link
    Args:
        url(str):


    """
    if sys.platform == 'win32':
        os.startfile(url)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', url])
    else:
        try:
            subprocess.Popen(['xdg-open', url])
        except OSError:
            raise OSError('Please open a browser on: ' + url)


def resolve_command_source(command):
    """
    Resolve command string and source type from command config.
    The source type and command are assumed to be split by colon sign
    Args:
        command(str): A string representing source type and command. eg. "PY:print('Hello World')"

    Returns:
        tuple: command and source type(python or mel)

    """
    source_type = "python"
    if ':' in command:
        st, command = command.split(':', 1)
        if st.upper() == 'MEL':
            source_type = 'mel'
    return command, source_type


def resolve_icon_path(icon):
    """
    Resolve the icon path by merging the icon file name and XBMLANGPATH
    in environment if file exists. The first found path will be returned
    Args:
        icon(str): The icon file name

    Returns:
        str: Resolved icon path

    """
    env_vir = os.environ.get('XBMLANGPATH')
    if env_vir:
        split_paths = env_vir.split(os.pathsep)
        for p in split_paths:
            p = os.path.join(p, icon)
            if os.path.isfile(p):
                return p
