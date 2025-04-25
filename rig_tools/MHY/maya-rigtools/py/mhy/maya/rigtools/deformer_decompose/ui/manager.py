import os
import maya.cmds as cmds
import json


def get_config_path():
    mayaVersion = cmds.about(version=True)
    appDir = os.environ.get('MAYA_APP_DIR')
    configPath = os.path.join(appDir, mayaVersion, "prefs", "nodezooui.config")
    configPath = configPath.replace('\\', '/')
    return configPath


def read_config():
    filePath = get_config_path()
    if os.path.isfile(filePath):
        with open(filePath, 'r') as f:
            config = json.load(f)
            return config
    else:
        return Default_Config


def write_config(config):
    filePath = get_config_path()
    dirPath = os.path.dirname(filePath)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    with open(filePath, 'w') as f:
        json.dump(config, f)


Node_List_View = None
call_back_ids = []

Default_Config = {
    "export":
        {
            "weightsOnly": 0,
            "connection": 1,
            "compress": 1,
            "multipleFiles": 0
        },
    "import":
        {
            "weightsOnly": 0,
            "connection": 1,
            "creationData": 1,
            "nameMap": {},
            "namespaceMap": (),
        },
    "transfer":
        {
            "surfaceAssociation": "closestPoint",
            "influenceAssociation": None,
            "normalize": True,
        },
}

Current_Config = read_config()
