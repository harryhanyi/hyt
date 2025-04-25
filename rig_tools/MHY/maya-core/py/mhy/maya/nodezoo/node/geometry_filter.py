"""
Geometry filter nodezoo class

"""
from six import string_types

import maya.cmds as cmds
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMaya as OpenMaya
from copy import deepcopy

from mhy.python.core.utils import increment_name
from mhy.maya.nodezoo.node import Node, DependencyNode
from mhy.maya.nodezoo.node.mesh import Mesh
from mhy.maya.nodezoo.constant import DataFormat, SurfaceAssociation


class GeometryFilter(DependencyNode):
    __NODETYPE__ = 'geometryFilter'
    __FNCLS__ = OpenMayaAnim.MFnGeometryFilter

    @classmethod
    def create_on_geometry(cls, creation_data, geometry=None, rename=None):
        if not creation_data:
            OpenMaya.MGlobal.displayError("Not valid creation data:"
                                          " for creating deformer on geometry")

            return

        creation_data = deepcopy(creation_data)
        if creation_data:
            args = creation_data.get('_args', [])
            if args:
                if not isinstance(geometry, list):
                    geometry = [geometry]
                args[0] = geometry
            else:
                OpenMaya.MGlobal.displayError("Not valid args: for creating deformer on geometry".format(args))
                return

        if rename and isinstance(rename, string_types):
            current_name = rename
        else:
            current_name = creation_data.get('name', cls.__NODETYPE__)
        while cmds.objExists(current_name):
            current_name = increment_name(current_name)
        creation_data['name'] = current_name

        args = creation_data.get('_args', [])
        kwargs = {str(key): creation_data[key] for
                  key in creation_data if key != '_args'}

        node = cls.import_create(*args, **kwargs)
        return node

    @classmethod
    def create_dummy_deformer(cls, node_data):
        # Need to create the a dummy mesh of orig mesh from the data
        additional_data = node_data.get('additional')
        if not additional_data:
            return None, None
        out_object_info = additional_data['out_object_info']
        mesh_data = None
        if out_object_info:
            values = [i for i in out_object_info.values()]
            mesh_data = values[0]
        if not mesh_data:
            return None, None
        mesh_creation_data = mesh_data.get('creation')
        dummy_mesh = Mesh.create(**mesh_creation_data)
        dummy_mesh.load(mesh_data)
        node_creation_data = node_data.get('creation')
        dummy_deformer = cls.create_on_geometry(node_creation_data,
                                                geometry=dummy_mesh.name)
        dummy_deformer.load(node_data)
        return dummy_mesh, dummy_deformer

    @property
    def output_objects(self):
        """

        Returns:
            list: Get the names of influence objects in a list

        """
        obj_list = OpenMaya.MObjectArray()
        self.fn_node.getOutputGeometry(obj_list)

        nodes = []
        for i in range(obj_list.length()):
            fn_node = OpenMaya.MFnDagNode(obj_list[i])
            nodes.append(Node(fn_node.partialPathName()))
        return nodes

    @property
    def attributes_to_export(self):
        return ['envelope', 'weightList']

    def export_creation_data(self):
        data = super(GeometryFilter, self).export_creation_data()
        args = data.get('_args', [])
        args.append(self.get_deformed_members())
        data['_args'] = args
        return data

    def export_additional_data(self):
        data = super(GeometryFilter, self).export_additional_data()
        out_object_info = {}
        for idx, out in enumerate(self.output_objects):
            transform = out.get_parent()
            if transform:
                for child in transform.get_children():
                    if child.is_intermediate:
                        child_data = child.export()
                        out_object_info[idx] = child_data
                        break
        data['out_object_info'] = out_object_info
        return data

    def export(self, connection_data=True, creation_data=True,
               additional_data=True, data_format=DataFormat.kJson,
               weight_only=False, *args, **kwargs):
        if weight_only:
            if data_format == DataFormat.kJson:
                data = {'name': self.name, 'type': self.type_name}
                attr_data = self.export_weights()
                data['attributes'] = attr_data
                return data
        else:
            return super(GeometryFilter, self).export(connection_data=connection_data,
                                                      creation_data=creation_data,
                                                      additional_data=additional_data,
                                                      data_format=data_format)

    def load(self, data, make_connections=True, rename=False, *args, **kwargs):
        """
        Load data to this node.
        Args:
            data:
            make_connections:
            rename:
            *args:
            **kwargs:

        Returns:

        """
        surface_association = kwargs.get('surface_association', SurfaceAssociation.vertex_id)
        if surface_association == SurfaceAssociation.vertex_id:
            super(GeometryFilter, self).load(data)
        else:
            dummy_mesh, dummy_deformer = self.create_dummy_deformer(data)
            if not dummy_mesh or not dummy_deformer:
                OpenMaya.MGlobal.displayWarning("Failed to find source geometry info. "
                                                "Roll back to using vertex association")
                super(GeometryFilter, self).load(data)

                return

            new_name = data.get('name')
            if new_name and rename:
                self.name = new_name
            output_objects = self.output_objects

            try:
                for i in output_objects:
                    dummy_deformer.copy_weight_to(source_shape=dummy_mesh,
                                                  destination_deformer=self,
                                                  destination_shape=i,
                                                  **kwargs)
            except Exception as e:
                raise Exception(str(e))
            finally:
                cmds.delete(dummy_deformer.name)
                cmds.delete(dummy_mesh.name)

    def export_weights(self):
        """
        This is a convenient method to export weights from this deformer.
        Since weights data are also attributes data, this method will return
        it as value of attribute dictionary
        Returns:
            dict: Weight list plug attribute data
        """
        data = []
        weight_list = self.weightList
        weight_list_data = weight_list.export(withConnection=False)
        data.append(weight_list_data)
        return data

    def copy_weight_to(
            self,
            destination_deformer,
            source_shape=None,
            destination_shape=None,
            surface_association=None):
        """
        Copy deformer weight to another deformer and shape based on
        given association method
        Args:
            source_shape(DependencyNode):
            destination_shape(DependencyNode):
            destination_deformer(GeometryFilter):
            surface_association(str):

        """
        if not destination_shape:
            target_geos = destination_deformer.output_objects
            if not target_geos:
                OpenMaya.MGlobal.displayWarning("{} has no output object, "
                                                "skipped".format(destination_deformer.name))
                return
            destination_shape = target_geos[0].name
        destination_shape = Node(destination_shape).name
        if not source_shape:
            target_geos = self.output_objects
            if not target_geos:
                OpenMaya.MGlobal.displayWarning("{} has no output object, "
                                                "skipped".format(destination_deformer.name))
                return
            source_shape = target_geos[0].name
        source_shape = Node(source_shape).name
        if isinstance(destination_deformer, DependencyNode):
            destination_deformer = destination_deformer.name

        kwargs = {
            "sourceShape": source_shape,
            "destinationShape": destination_shape,
            "sourceDeformer": self.name,
            "destinationDeformer": destination_deformer,
            "surfaceAssociation": surface_association or SurfaceAssociation.closest_point,
            "noMirror": True
        }

        if surface_association == SurfaceAssociation.uv:
            kwargs['surfaceAssociation'] = SurfaceAssociation.closest_point

            if not isinstance(destination_shape, Mesh):
                OpenMaya.MGlobal.displayWarning("Target object '{}' has no uv sets."
                                                " Roll back to use point "
                                                "distance instead".format(destination_shape))

            else:
                source_uvs = source_shape.get_current_uv_set()
                target_uvs = destination_shape.get_current_uv_set()
                if not source_uvs or not target_uvs:
                    OpenMaya.MGlobal.displayWarning("Target object '{}' or '{}' has no uv sets."
                                                    " Roll back to use distance "
                                                    "instead".format(source_shape,
                                                                     destination_shape))
                else:
                    kwargs['uvSpace'] = (source_uvs, target_uvs)
        cmds.copyDeformerWeights(**kwargs)

    def get_deformed_members(self):
        """
        Get deformed components from the deformer set

        Returns:
            list: A list of components names
        """
        version = int(cmds.about(version=True))
        if version < 2022:
            mObj = self.fn_node.deformerSet()
            deformer_set = Node(mObj)
            members = deformer_set.members or []
            return members
        else:
            out_objects = self.output_objects
            result = []
            for out in out_objects:
                if out.type_name == 'mesh':
                    name = out.outMesh.short_name
                    tags = cmds.geometryAttrInfo(name,componentTagNames=True)
                    if self.name not in tags:
                        components = ['vtx[:]']
                    else:
                        components = cmds.geometryAttrInfo(
                            name,
                            componentTagExpression=self.name,
                            components=True)
                    components = ['{}.{}'.format(out.name, i) for i in components]
                    result = result + components
            return result

    @classmethod
    def _pre_creation_callback(cls, *args, **kwargs):
        args = args[0]
        return args, kwargs
