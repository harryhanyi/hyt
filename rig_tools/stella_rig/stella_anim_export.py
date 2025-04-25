import maya.cmds as cmds
import json

class AnimExpImp():
        
    def __init__(self, file_path=None, objects=None, prefix=None):
        self.path = file_path
        if objects:
            self.objects = objects
        else:
            self.objects = cmds.ls(sl=1)
        if prefix:
            self.prefix = prefix
        self.anim_data={}

    def get_anim_curves(self):
        self.anim_data = {}
        start_frame = cmds.playbackOptions(query=True, minTime=True)
        end_frame = cmds.playbackOptions(query=True, maxTime=True)
        for obj in self.objects:
            connect_objs = cmds.listConnections(obj, source=True, destination=False) or []
            for obj in connect_objs:
                attrs = cmds.listConnections(obj, plugs=True, source=False, destination=True)  # Get connected attributes
                for attr in attrs:
                    if self.prefix in attr:
                        value_list = []
                        for key in range(int(start_frame), int(end_frame)+1):
                            value = cmds.getAttr(attr, time=key)
                            value_list.append([key, value])
                        if self.prefix:
                            attr = attr.replace(f"{self.prefix}:","")
                        self.anim_data[attr] = value_list
        
        return

    def apply_anim(self):
        for attr in self.anim_data:
            if self.prefix:
                p_attr = f"{self.prefix}:{attr}"
            else:
                p_attr = attr
            for item in self.anim_data[attr]:
                try:
                    cmds.setKeyframe(p_attr, time=item[0], value=item[1])
                except:
                    print(f"{p_attr} is not in scene!")
                    break
        return

    def export_anim(self):
        self.get_anim_curves()
        with open(self.path, "w") as f:
            json.dump(self.anim_data, f, indent=4)
        return

    def import_anim(self):
        with open(self.path, "r") as f:
            self.anim_data = json.load(f)
        self.apply_anim()
        return



