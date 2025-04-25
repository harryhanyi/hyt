import six
from maya import cmds, OpenMaya

import mhy.protostar.core.parameter as pa
from mhy.maya.rig.base_actions import BaseRigDataAction
from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
#from mhy.protostar.lib import ActionLibrary as alib
#alib.refresh()


class DuplicateObjects(BaseRigDataAction):
    
    @pa.list_param()
    def input_objects(self):
        """
        """
        
    @pa.list_param()
    def names(self):
        """
        """
        
    @pa.list_param(output=True)
    def output_objects(self):
        """
        """

    @pa.str_param(default=None)
    def parent_node(self):
        """
        """
    
    @pa.bool_param(default=True)
    def vis(self):
        """
        """
        

    def run(self):
        
        input_objs = self.input_objects.value
        output_names = self.names.value
        parent_node = self.parent_node.value
        vis = self.vis.value
        
        non_exists_objs = [obj for obj in input_objs if not cmds.objExists(obj)]
        if non_exists_objs:
            for item in non_exists_objs:
                OpenMaya.MGlobal.displayError("{} does not exists".format(item))
            return
        
        duplicated_objs=[]
        for bs_obj, name in zip(input_objs, output_names):
            
            dup_obj = Node(bs_obj).duplicate(n=name)[0]

            if parent_node:
                dup_obj.set_parent(parent_node)
            else:
                dup_obj.set_parent()
            
            dup_obj.v.value = vis
                
            duplicated_objs.append(dup_obj)
        
        self.output_objects.value = duplicated_objs

class SetupPSD(BaseRigDataAction):

    @pa.list_param()
    def mesh_list(self):
        """
        """

    def run(self):
        import stella_rig.stella_setup_psd_shapes as ssps
        import importlib
        importlib.reload(ssps)
        meshes = self.mesh_list.value
        ssps.setup_psd(meshes)

        return
    
class RigidOnPSD(BaseRigDataAction):
    @pa.list_param()
    def joint_list(self):
        """
            List of joints need to attach to surf
        """
    @pa.str_param()
    def surf(self):
        """
            Helping surf's name
        """

    @pa.bool_param(default=True)
    def mirror(self):
        """
        """

    def run(self):
        """
            1. Setup attachment locators on surface. (Use stella_setup_psd_shapes.setup_help_surf)
            2. Attach joints on locators. (Use stella_rigging_tools.setup_surf_constraints)
        """
        import stella_rig.stella_setup_psd_shapes as ssps
        import stella_rig.stella_rigging_tools as srt
        import importlib
        importlib.reload(ssps)
        importlib.reload(srt)
        surf_name = self.surf.value
        mirror = self.mirror.value
        joint_list = self.joint_list.value

        ssps.setup_help_surf(surf_name, mirror=mirror)
        srt.setup_surf_constraints(joint_list, surf_name, mirror=mirror)




