"""
This action is setting up the texture driver based on maya dx11 shader
"""
from maya import cmds, OpenMaya
import os
import json
import mhy.protostar.core.parameter as pa
from mhy.maya.nodezoo.node import Node
from mhy.protostar.core.action import MayaAction
from mhy.maya.rig.data import import_texture_shader_data


class TextureDriver(MayaAction):
    """
    A joint-based ingame face rig.
    """

    # -- input parameters
    @pa.str_param()
    def mesh_object(self):
        """The mesh object the shader will be applied to"""

    @pa.file_param(ext='json')
    def shader_data_file(self):
        """The fx shader file path."""

    @pa.str_param(default='face_MAT')
    def shader_name(self):
        """Name of the shader node."""

    @pa.pyobject_param(output=True)
    def shader_node(self):
        """
        Created shader node

        """
    @pa.pyobject_param(output=True)
    def shader_group(self):
        """
        Created shader group associated with the shader node

        """
    @pa.list_param()
    def pose_nodes(self):
        """Pose nod the texture will be connected to"""

    # --- end of parameter definition

    def load_plugin(self):
        """
        Load dx11Shader plugin before execution the action
        Returns:
            bool: The result if plugin is loaded correctly
        """
        plugin = 'dx11Shader'
        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            try:
                cmds.loadPlugin(plugin, quiet=True)
                return True
            except BaseException:
                self.error('Failed loading plugin {}'.format(plugin))
                return False
        return True

    def from_json_get_dict(self, json_path):
        """
        Get dictionary data from a json file
        Args:
            json_path(str): A file path

        Returns:
            dict: Dictionary data

        """
        if os.path.exists(json_path):
            with open(json_path, 'r') as jsonfile:
                json_dict = json.load(jsonfile)
            return json_dict
        else:
            self.error("Json file is not exists from function from_json_get_dict.")

    def create_shader(self, name, mesh):
        """
        Create the shader node and apply to target mesh
        Returns:
            str: The name of shader node
        """
        shader = cmds.shadingNode('dx11Shader', asShader=True, name=name)
        set_name = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='{}_SG'.format(shader))
        cmds.connectAttr("{}.outColor".format(shader), "{}.surfaceShader".format(set_name), force=True)

        cmds.sets(mesh, edit=True, forceElement=set_name)
        self.shader_node.value = Node(shader)
        self.shader_group.value = Node(set_name)

    def connect_material(self):
        """
        Connect attributes from pose node to shader node

        """
        def check_pose_attribute(pose_node_name, attr_name):
            if not cmds.objExists('{}.{}'.format(pose_node_name, attr_name)):
                OpenMaya.MGlobal.displayWarning('Pose {} does not exist on pose node'.format(attr_name, pose_node_name))
                return False
            return True

        json_file = self.shader_data_file.value
        if not os.path.exists(json_file):
            self.warn('json file : {0} is not exist!'.format(json_file))
            return

        if not self.pose_nodes.value:
            self.warn('Pose node has not been provided')
            return

        pose_node = Node(self.pose_nodes.value[0])

        shader_dict = self.from_json_get_dict(json_path=json_file)
        if not shader_dict:
            return

        pose_map_data = shader_dict.get('pose_map', dict())
        shader_node = self.shader_node.value
        if not shader_node:
            self.error("Failed to create shader node")
            return
        for mt_attr, driven in pose_map_data.items():
            drive_count = len(driven)
            sr_node = Node.create('setRange', name='{0}_SR'.format(mt_attr))

            sr_node.set_attr('minX', 0)
            sr_node.set_attr('maxX', 1)
            sr_node.set_attr('oldMinX', 0)
            sr_node.set_attr('oldMaxX', 10)

            if drive_count > 1:
                pma_node = Node.create('plusMinusAverage', name='{0}_PMA'.format(mt_attr))
                missing_pose = False
                for i, attr in enumerate(driven):
                    if not check_pose_attribute(pose_node.name, attr):
                        missing_pose = True
                        break
                    pose_output = pose_node.attr(attr)
                    if not pose_output:
                        self.warn("There's not attribute called {} on pose node {}".format(attr, pose_node))
                        continue
                    pose_output.connect(pma_node.attr('input1D[{}]'.format(i)), force=True)
                if not missing_pose:
                    pma_node.attr('output1D').connect(sr_node.attr('valueX'), force=True)

            elif drive_count == 1:
                if not check_pose_attribute(pose_node.name, driven[0]):
                    continue
                pose_output = pose_node.attr(driven[0])
                pose_output.connect(sr_node.attr('valueX'), force=True)

            sr_node.attr('outValueX').connect(shader_node.attr(mt_attr), force=True)

    def import_shader_data(self):
        """
        Import shader data to this shader node. This process
        will set fx shader path and map paths.
        Returns:

        """
        if not self.shader_node.value:
            self.warn("Failed to create shader node, skipped importing shader data")
            return

        self.debug("Import shader data to, {}".format(self.shader_node.value.name))
        self.debug("Import shader data from, {}".format(self.shader_data_file.value))
        import_texture_shader_data(self.shader_node.value.name, self.shader_data_file.value)

    def run(self):
        """Core execution method."""
        status = self.load_plugin()
        if not status:
            return

        shader_name = self.shader_name.value
        mesh = self.mesh_object.value

        if not mesh:
            self.error("No mesh provided")
            return
        if not cmds.objExists(mesh):
            self.error("{} does not exist".format(mesh))
            return

        self.create_shader(shader_name, mesh)

        self.import_shader_data()
        self.connect_material()


