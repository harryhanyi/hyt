"""

For easier save and load controllers' attributes

"""


import os
import json
import maya.cmds as cmds
from pymel.util.enum import Enum
from pymel.core.system import sceneName

# Make a map for in-built attributes
shapeType = Enum('shapeType',
                 ['circle', 'cube', 'square', 'triangle', 'hexgram', 'donut', 'sphere', 'SphereCurve'])
controllerType = Enum('controllerType',
                      ['Locator', 'PoseController'])


class CtrlAttrsController(object):
    '''
    A static class to save and load ctrls' attributes
    '''
    serialized_attrs = {
        "localPositionX", "localPositionY", "localPositionZ",
        "localScaleX", "localScaleY", "localScaleZ",
        "localRotateX", "localRotateY", "localRotateZ",
        "colorR", "colorG", "colorB",
        "textPositionX", "textPositionY", "textPositionZ",
        "shapeType",
        "controllerType",
        "xrayMode"}

    def __init__(self):
        pass

    @staticmethod
    def get_all_ctrls():
        ctrl_list = cmds.ls('*CTRLShape')
        return ctrl_list

    @staticmethod
    def export_attrs(ctrl_list, filename=""):
        """
        export attributes to resources/ctrl_attrs.json
        Args:
            ctrl_list:
            filename:

        Returns:

        """
        attr_dict = {}
        for ctrl in ctrl_list:
            for attr in CtrlAttrsController.serialized_attrs:
                value = cmds.getAttr(ctrl + "." + attr)
                # If we want to serialize enum as a string
                if type(value) is int:
                    value = str(eval(attr)[value])

                if(attr_dict.has_key(ctrl) is False):
                    attr_dict[ctrl] = {}
                attr_dict[ctrl][attr] = value

        if filename == "":
            resource_path = os.environ.get('MHY_RESOURCE_PATH')
            scene_name = sceneName().split('/')[-1].split('.')[0]
            filename = resource_path+'/' + scene_name + '_ctrl_attrs.json'
        with open(filename, 'w') as attr_file:
            json.dump(attr_dict, attr_file, indent=4)
        print("exported to " + filename)

    @staticmethod
    def get_all_import_attrs(filename=""):
        '''
        import attributes from resources/ctrl_attrs.json
        '''
        
        if filename == "":
            resource_path = os.environ.get('MHY_RESOURCE_PATH')
            scene_name = sceneName().split('/')[-1].split('.')[0]
            filename = resource_path+'/' + scene_name + '_ctrl_attrs.json'
        with open(filename, 'r') as attr_file:
            attr_dict = json.load(attr_file)

        return attr_dict
    
    @staticmethod
    def import_attrs(ctrl_list, attr_dict):
        for ctrl in ctrl_list:
            for attr in CtrlAttrsController.serialized_attrs:
                value = attr_dict[ctrl][attr]
                # If we need to deserialize form a string to enum
                if type(value) is unicode:
                    value = getattr(eval(attr), value.decode()).index

                cmds.setAttr(ctrl + "." + attr, value)
