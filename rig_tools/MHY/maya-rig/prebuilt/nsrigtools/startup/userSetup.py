import os
import maya.cmds as cmds
import maya.api.OpenMaya as om2

LOC_ENV_VAR = 'NSRIGTOOLS_LOCATION'
PLUGIN_DIR_NAME = 'plug-ins'
PLUGIN_EXTS = ['.mll', '.bundle', '.so']


def load_nsrigtools_plugins():
    root_dir = os.environ.get(LOC_ENV_VAR)
    # print('root_dir:', root_dir)

    if not root_dir:
        om2.MGlobal.displayWarning(
            "nsrigtools: Environment variable 'NSRIGTOOLS_LOCATION' is missing, 'nsrig' plugins won't be loaded at this point."
        )
        return

    plugin_dir = os.path.join(root_dir, PLUGIN_DIR_NAME)

    for f in os.listdir(plugin_dir):
        name, ext = os.path.splitext(f)
        # print(name, ext)

        if not ext in PLUGIN_EXTS:
            continue

        plugin_path = os.path.join(plugin_dir, f)
        isLoaded = cmds.loadPlugin(plugin_path)
        if not isLoaded:
            om2.MGlobal.displayWarning(
                "nsrigtools: Could not load plugin: %s" % plugin_path
            )
            continue

        plugin_ver = cmds.pluginInfo(plugin_path, q=1, v=1)
        om2.MGlobal.displayInfo('nsrigtools: %s %s loaded.' % (name, plugin_ver))


cmds.evalDeferred('load_nsrigtools_plugins()', lowestPriority=True)
