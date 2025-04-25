"""

Skin Cluster node zoo class

"""
from six import string_types

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMaya as OpenMaya

import mhy.python.core.utils as pyutil
from mhy.maya.nodezoo.node import Node, GeometryFilter, DependencyNode, DagNode
from mhy.maya.nodezoo.constant import DataFormat, SurfaceAssociation
from mhy.maya.nodezoo.node.mesh import Mesh


MISSING_INF_GRP = '__MISSING_INFS__'


class SkinCluster(GeometryFilter):
    __NODETYPE__ = 'skinCluster'
    __FNCLS__ = OpenMayaAnim.MFnSkinCluster

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create skin cluster instance. Before calling maya built-in creation
        function, this method will check existence of each none key word argument
        and filter out objects not in current scene.
        Args:
            *args:
            **kwargs:

        Returns:
            SkinCluster: Created instance

        """
        filter_args = list()
        args = pyutil.flatten_list(args)
        for item in args:
            if cmds.objExists(item):
                filter_args.append(item)
            else:
                OpenMaya.MGlobal.displayWarning("Skipped none exists item {}".format(item))

        node_name = cmds.skinCluster(*filter_args, **kwargs)[0]
        node = Node(node_name)
        return node

    @classmethod
    def find_skin_cluster(cls, obj):
        if isinstance(obj, (OpenMaya.MObject, OpenMaya.MObjectHandle)):
            obj = Node(obj)
        if isinstance(obj, DependencyNode):
            obj = obj.name
        assert isinstance(obj, string_types)
        skin = mel.eval('findRelatedSkinCluster {}'.format(obj))
        if not skin:
            return
        return SkinCluster(skin)

    @property
    def influences(self):
        dat_path_array = OpenMaya.MDagPathArray()
        self.fn_node.influenceObjects(dat_path_array)
        num = dat_path_array.length()
        if num:
            return [dat_path_array[i].partialPathName() for i in range(num)]
        return []

    def add_influence(self, influence, weight=0):
        if cmds.objExists(influence):
            cmds.skinCluster(
                self.name,
                edit=True,
                addInfluence=influence,
                weight=weight
            )
            return self.influence_index(influence)

    def remove_influence(self, influence):
        """
        Remove influence from this skin cluster
        Args:
            influence(list): A list of influence

        """
        cmds.skinCluster(
            self.name,
            edit=True,
            removeInfluence=influence
        )

    def clear_influence(self):
        """
        Remove all influences
        Returns:

        """
        for inf in self.influences:
            self.remove_influence(inf)

    def influence_index(self, influence):
        if isinstance(influence, DagNode):
            influence = influence.dag_path
        elif isinstance(influence, string_types):
            node = DagNode(influence)
            influence = node.dag_path
        index = self.fn_node.indexForInfluenceObject(influence)
        return index

    def influence_indexes(self):
        indexes = []
        for inf in self.influences:
            idx = self.influence_index(inf)
            indexes.append(idx)
        return indexes

    def copy_weight_to(self, destination_skin, surface_association=None, copy_mirror=None, **kwargs):
        """
        Wrapper method over maya native copy skin weight command to copy weight from this
        node to another skin cluster
        Args:
            destination_skin(str or SkinCluster):
            surface_association(str or None): If None,  closest point association will be default.
            copy_mirror: If True, copy then mirror weights on the destination skin cluster. (updated by Adrian)
            **kwargs:

        """
        if not copy_mirror:
            copy_mirror = False
        
        destination_skin = Node(destination_skin)
        kwargs = {
            "sourceSkin": self.name,
            "destinationSkin": destination_skin.name,
            "surfaceAssociation": surface_association or SurfaceAssociation.closest_point,
            "noMirror": True
        }

        if surface_association == SurfaceAssociation.uv:
            kwargs['surfaceAssociation'] = SurfaceAssociation.closest_point
            destination_shape = destination_skin.output_objects[0]
            if not isinstance(destination_shape, Mesh):
                OpenMaya.MGlobal.displayWarning("Target object '{}' has no uv sets."
                                                " Roll back to use point "
                                                "distance instead".format(destination_shape.name))

            else:
                source_shape = self.output_objects[0]
                source_uvs = source_shape.get_current_uv_set()
                target_uvs = destination_shape.get_current_uv_set()
                if not source_uvs or not target_uvs:
                    OpenMaya.MGlobal.displayWarning("Target object '{}' or '{}' has no uv sets."
                                                    " Roll back to use distance "
                                                    "instead".format(source_shape.name,
                                                                     destination_shape.name))
                else:
                    kwargs['uvSpace'] = (source_uvs, target_uvs)

        cmds.copySkinWeights(**kwargs)
        
        if copy_mirror:
            kwargs = {
                "sourceSkin": destination_skin.name,
                "destinationSkin": destination_skin.name,
                "mirrorMode": "YZ",
                "influenceAssociation": "oneToOne",
                "influenceAssociation": "closestJoint"
            }
            cmds.copySkinWeights(**kwargs)
            

    def sync_influences_and_order(self, influence_names, influence_index):
        """
        Update the influences objects to be the same as in the data. This is necessary
        before loading data.
        Args:
            influence_names(list):
            influence_index(list):
        Returns:

        """
        current_inf_names = self.influences
        current_inf_indexes = self.influence_indexes()
        index_map = {}

        if (influence_names, influence_index) != (current_inf_names, current_inf_indexes):
            # Need to make sure the influences and indexes are the same
            OpenMaya.MGlobal.displayWarning("Current influences are not the "
                                            "same as the data. Need to recreate influences")
            for inf, old_index in zip(influence_names, influence_index):
                if inf not in current_inf_names:
                    # If influence is not one of current influences, try to add it
                    if not cmds.objExists(inf):
                        # If the influence object is missing, create a dummy
                        # joint to ensure the joint weights are not normalized
                        if not cmds.objExists(MISSING_INF_GRP):
                            cmds.group(name=MISSING_INF_GRP, empty=True)
                        cmds.select(cl=True)
                        inf = cmds.joint(name=inf)
                        cmds.parent(inf, MISSING_INF_GRP)
                        OpenMaya.MGlobal.displayWarning(
                            "Created dummy joint '{}' "
                            "as a placeholder of missing influence".format(inf))
                    idx = self.add_influence(inf, weight=0)
                    if idx is not None:
                        index_map[old_index] = idx
                else:
                    # if the index is the same, skip add mapping
                    idx = current_inf_names.index(inf)
                    idx = current_inf_indexes[idx]
                    if old_index == idx:
                        continue
                    else:
                        index_map[old_index] = idx
            # We have to remove influences which are not in the data dict
            influences_to_remove = [inf for inf in current_inf_names if inf not in influence_names]
            for inf in influences_to_remove:
                self.remove_influence(inf)
        return index_map

    @staticmethod
    def update_data_with_index_map(data, index_map):
        # with the index map, we just edit the data before load into the attributes
        for attr in data['attributes']:
            if attr['name'] == 'weightList':
                weight_array = attr.get('array')
                if not weight_array:
                    break
                for i in attr['array']:
                    children_data = i['children']
                    for child in children_data:
                        if child['name'] == 'weights':
                            weight_array = child.get('array', [])
                            for weight_data in weight_array:
                                idx = int(weight_data['index'])
                                if idx in index_map:
                                    weight_data['index'] = index_map[idx]
        return data

    @property
    def attributes_to_export(self):
        attrs = ['skinningMethod', 'bindMethod', 'dropoffRate',
                 'normalizeWeights', 'maxInfluences']
        return attrs

    def export_creation_data(self):
        data = super(SkinCluster, self).export_creation_data()
        args = data.get('_args', [])
        influences_names = [i for i in self.influences]
        args.extend(influences_names)
        # Need to make sure use only the joints in the creation data to create skin
        # instead of adding all the hierarchy
        data['_args'] = args
        data['toSelectedBones'] = True
        return data

    def export(self, connection_data=True, creation_data=True,
               additional_data=True, data_format=DataFormat.kJson,
               weight_only=False, *args, **kwargs):
        """
        This is the entry point when exporting data of a dependency node and its child classes.

        Args:
            connection_data(bool):  If export connection data when calling
            creation_data(bool): If export creation data when calling
            additional_data(bool): If export additional data when calling
            data_format(bool): For now only json data format is supported
            weight_only(bool): Export only the weight data from this node

        Returns:
            (dict)

        """
        data = {}
        if not weight_only:
            data = super(SkinCluster, self).export(
                connection_data=connection_data,
                creation_data=creation_data,
                additional_data=additional_data,
                data_format=data_format,
                weight_only=weight_only)

        influences = self.influences
        influences_names = [i for i in influences]
        indexes = self.influence_indexes()
        data['influences'] = (influences_names, indexes)
        data['weights'] = self.get_weights_data()

        return data

    def get_weights_data(self):
        dag = self.output_objects[0].dag_path
        num_influences = len(self.influences)
        inf_count_util = OpenMaya.MScriptUtil(num_influences)
        inf_count_ptr = inf_count_util.asUintPtr()
        weights = OpenMaya.MDoubleArray()
        empty_object = OpenMaya.MObject()
        self.fn_node.getWeights(dag, empty_object, weights, inf_count_ptr)
        out_data = []
        for i in range(weights.length()):
            out_data.append(weights[i])
        return out_data

    def load(self, data, make_connections=True, rename=False, **kwargs):
        influences = data.get('influences')
        index_map = None
        if influences:
            influence_names, influence_index = influences
            index_map = self.sync_influences_and_order(influence_names,
                                                       influence_index)

        surface_association = kwargs.get('surface_association', SurfaceAssociation.vertex_id)
        weights = data.get('weights')

        if surface_association == SurfaceAssociation.vertex_id:
            self.set_weight_data(weights, influences, index_map)
        else:
            dummy_mesh, dummy_deformer = self.create_dummy_deformer(data)

            if not dummy_mesh or not dummy_deformer:
                OpenMaya.MGlobal.displayWarning("Failed to find source geometry info. "
                                                "Roll back to using vertex association")
                self.set_weight_data(weights, influences, index_map)

                return
            try:
                dummy_deformer.copy_weight_to(destination_skin=self,
                                              **kwargs)
            except Exception as e:
                raise Exception(str(e))
            finally:
                cmds.delete(dummy_deformer.name)
                dummy_mesh.destruct()
            new_name = data.get('name')
            if new_name and rename:
                self.name = new_name

    def set_weight_data(self, data, influences, index_map=None):
        """
        Set weight data to skin cluster
        Args:
            data(list): A list of weights of length (num_components * num_influences)
            influences(tuple): Influence tuple: influence names and indexes
            index_map(None or dict):
        Returns:

        """
        influence_names, influences_indexes = influences
        if not influence_names:
            return
        num_influences = len(influence_names)
        num_components = int(len(data)/num_influences)

        weight_list_attr = self.weightList
        for child in weight_list_attr:
            child.remove()
        weight_list_attr_plug = weight_list_attr.__plug__

        for i in range(num_components):
            weights_plug = weight_list_attr_plug.elementByLogicalIndex(i)
            child_plug = weights_plug.child(0)

            for j, (_, idx) in enumerate(zip(influence_names, influences_indexes)):
                w = data[i * num_influences + j]
                if w == 0.0:
                    continue
                if index_map and idx in index_map:
                    idx = index_map[idx]
                weight_plug = child_plug.elementByLogicalIndex(idx)
                weight_plug.setFloat(w)

    def merge(self, data, name_map=None, filter_func=None, normalize=True, weight_threshold=None):
        """
        This method merge weights from a data to this skin cluster node.
        If the influence has no already been added, add influence to this skin
        Args:
            data:
            name_map:
            filter_func(callable): A callable object will be used to check the influence as filter
            normalize(bool): If true, will assign weight using maya.cmds.skinPercent
            so the weight will be normalized automatically
            weight_threshold(float): Skip setting weight under a given value

        """
        if isinstance(data, list):
            data = data[0]

        inf_idx_lists = data.get('influences')

        if not inf_idx_lists:
            return

        weight_list_data = data.get('weights')
        if not weight_list_data:
            OpenMaya.MGlobal.displayError("Failed to find weightList data")
            return

        influence_map = {inf: idx for inf, idx in zip(inf_idx_lists[0], inf_idx_lists[1])}
        num_inf = len(influence_map)
        outputs = self.output_objects
        if not outputs:
            return

        for key, idx in influence_map.items():
            if filter_func is not None and not filter_func(key):
                continue
            influences = self.influences
            if name_map is not None:
                key = name_map.get(key, key)

            if not cmds.objExists(key):
                # If the influence object is not in the scene, skip
                continue

            if key in influences:
                # If the influence is already driving this skin, set the weights
                index = influences.index(key)
                target_index = self.influence_indexes()[index]
            else:
                target_index = self.add_influence(key)

            joint_index = inf_idx_lists[0].index(key)
            for vtx_index in range(outputs[0].num_vertices):
                value = weight_list_data[vtx_index*num_inf + joint_index]
                if weight_threshold is not None and value < weight_threshold:
                    continue
                if normalize:
                    # print('vtx index', vtx_index)
                    cmds.skinPercent(
                        self.name,
                        '{}.vtx[{}]'.format(outputs[0], vtx_index),
                        transformValue=[(key, value)])
                else:
                    self.weightList[vtx_index].weights[target_index].value = value

    @classmethod
    def _pre_creation_callback(cls, *args, **kwargs):
        return args, kwargs

    def clean_up(self, tol=.001):
        """Cleans up this skinCluster node by removing
        tiny weights and unused influences.

        Args:
            tol (float): The tolerance for pruning small weights.

        Returns:
            None
        """
        cmds.skinCluster(self, edit=True, forceNormalizeWeights=True)
        geom = cmds.skinCluster(self, query=True, geometry=True)[0]
        cmds.skinPercent(self, geom, normalize=True)
        cmds.skinPercent(self, geom, pruneWeights=tol, normalize=True)
        infs = set(cmds.skinCluster(self, query=True, influence=True) or []) - \
            set(cmds.skinCluster(self, query=True, weightedInfluence=True) or [])
        for each in infs:
            cmds.skinCluster(self, edit=True, removeInfluence=each)

    def smooth_weights(self, tolerance=0.5):
        """
        This flag is used to detect sudden jumps in skin weight values, which often indicates bad weighting,
        and then smooth out those jaggies in skin weights.

        Args:
            tolerance(float): The argument is the error tolerance ranging from 0 to 1.
            A value of 1 means that the algorithm will smooth a vertex only if there is a 100% change in weight values
            from its neighbors. The recommended default to use is 0.5 (50% change in weight value from the neighbors).

        """
        cmds.skinCluster(self.name, edit=True, smoothWeights=tolerance)
