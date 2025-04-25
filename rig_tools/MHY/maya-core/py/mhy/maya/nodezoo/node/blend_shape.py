"""
Node class for Blendshape
"""
from six import string_types
from copy import deepcopy
import maya.cmds as cmds
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.node import DependencyNode
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.node.mesh import Mesh
from mhy.maya.nodezoo.constant import DataFormat
from mhy.python.core.utils import increment_name


class BlendShape(DependencyNode):
    __NODETYPE__ = 'blendShape'
    __FNCLS__ = OpenMayaAnim.MFnBlendShapeDeformer

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create a blend shape node. Based on kwargs, the creation method will
        decide to use maya default blend shape creation command or create without
        existing target objects.
        Args:
            *args:
            **kwargs:

        Returns:
            BlendShape: A blend shape instance

        """
        bases = kwargs.get('bases')
        targets = kwargs.get('targets')

        if bases and targets:
            base = bases[0]
            return BlendShape.__create_with_target_names(base, targets, **kwargs)

        else:
            bs = cmds.blendShape(*args, **kwargs)
            if bs:
                return Node(bs[0])

    @classmethod
    def __create_with_target_names(cls, base, targets, **kwargs):
        """
        This creation method is to create a blend shape node and set up
        targets without existing target objects in the scene. It's user's
        responsible to load delta data if necessary
        Args:
            base(str): The base object name
            targets(list): A list of target names
            **kwargs:

        Returns:
            BlendShape: A blend shape instance
        """
        bs = cmds.blendShape(base, **kwargs)[0]
        for target, idx in targets:
            cmds.getAttr('{}.weight[{}]'.format(bs, idx))
            cmds.aliasAttr(target, '{}.weight[{}]'.format(bs, idx))
        return Node(bs)

    def add_target(self, target=None, index=None, in_between=1.0,
                   with_target_object=True):
        """
        Add a target entry on the next available index
        Args:
            target(DagNode or str): Deformable dagNode used as target object if with_target_object is True; otherwise
            used as the alias name for newly created weight attribute
            index(int or None): On which index the new target will be added to. If not provided, use the next
            available index on weight plug
            in_between(float): The in between value 0 - 1.0
            with_target_object(bool): If create with an existing target object.

        Returns:
            Attribute: Newly created target weight entry on weight attribute
            None: Failed to add target

        """
        if index is None:
            index = self.weight.minimum_available_index()
        if isinstance(target, DependencyNode):
            target = target.name

        if with_target_object:
            out_objects = self.output_objects
            if not out_objects:
                OpenMaya.MGlobal.displayError("This blend shape {} has not output objects".format(self.name))
                return
            out_obj = out_objects[0]
            cmds.blendShape(self.name, edit=True, target=(out_obj, index, target, in_between))
        else:
            cmds.getAttr('{}.weight[{}]'.format(self.name, index))
            if target:
                cmds.aliasAttr(target, '{}.weight[{}]'.format(self.name, index))
            target_item_attr = self.inputTarget[0].inputTargetGroup[index].inputTargetItem[int(1000*in_between + 5000)]

            # Force evaluate new entry on points and components child plug
            _ = target_item_attr.inputPointsTarget.value
            _ = target_item_attr.inputComponentsTarget.value

        return self.weight[index]

    @classmethod
    def create_on_geometry(cls, creation_data, geometry=None, rename=None):
        if not creation_data:
            OpenMaya.MGlobal.displayError("Not valid creation data:"
                                          " for creating deformer on geometry")

            return
        creation_data = deepcopy(creation_data)

        if creation_data:
            if not isinstance(geometry, list):
                creation_data["bases"] = [geometry]
            else:
                creation_data["bases"] = geometry

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
            mesh_data = out_object_info.values()[0]
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
        array = OpenMaya.MObjectArray()
        self.fn_node.getBaseObjects(array)
        objs = []
        for i in range(array.length()):
            base_obj_node = Node(array[0])
            objs.append(base_obj_node)
        return objs

    # ------------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------------

    @property
    def attributes_to_export(self):
        return ['envelope', 'inputTarget', 'weight']

    @property
    def attributes_to_ignore(self):
        return ['paintTargetWeights']

    def export_creation_data(self):
        data = DependencyNode.export_creation_data(self)
        # Need to make sure use only the joints in the creation data to create skin
        # instead pulling in all the hierarchy
        data['ignoreSelected'] = 1
        data['bases'] = [i.name for i in self.output_objects]
        data['targets'] = [(element.__plug__.partialName(False, False, False, True, False),
                            element.index) for element in self.weight]
        return data

    def export_additional_data(self):
        data = DependencyNode.export_additional_data(self)
        out_object_info = {}
        for idx, out in enumerate(self.output_objects):
            orig_obj = out.get_intermediate_sibling()
            if orig_obj:
                child_data = orig_obj.export()
                out_object_info[idx] = child_data
        data['out_object_info'] = out_object_info
        return data

    def export(self,
               connection_data=True,
               creation_data=True,
               additional_data=True,
               data_format=DataFormat.kJson,
               weight_only=False):
        """
        Export data from blend shape node
        Args:
            connection_data:
            creation_data:
            additional_data:
            data_format:
            weight_only:

        Returns:

        """
        if weight_only:
            if data_format == DataFormat.kJson:
                data = {'name': self.name, 'type': self.type_name}
                attr_data = self.export_weights()
                data['attributes'] = attr_data
                return data
        else:
            return DependencyNode.export(self,
                                         connection_data=connection_data,
                                         creation_data=creation_data,
                                         additional_data=additional_data,
                                         data_format=data_format)

    def export_weights(self):
        """
        This is a convenient method to export weights from this blend shape.
        Since weights data are also attributes data, this method will return
        it as value of attribute dictionary
        Returns:
            dict: Weight list plug attribute data
        """
        data = []
        target_weight_data = self.inputTarget.export(ignore=['paintTargetWeights'],
                                                     filter=['inputTargetGroup', 'Weights'])
        data.append(target_weight_data)
        return data

    def _pre_export_callback(self):
        """
        Have to force evaluate this node to make sure some attributes are initialized for
        the first time. For example: inputComponentsTarget
        """
        self.force_evaluate()

    def add_in_between(self, index, target=None, value=1.0):
        """
        Add an in between target for pose @index at @value
        Args:
            index(int): The integer of pose target
            target(str or DagNode): A deformable object as in between target
            value(float): A in between value in the range 0 to 1
        Returns:
            Attribute: The new inputTargetItem element attribute added by this action
        """

        if isinstance(target, DependencyNode):
            target = target.name

        out_objects = self.output_objects
        if not out_objects:
            OpenMaya.MGlobal.displayError("Blend shape {} has no output objects".format(self.name))
            return
        out_object = out_objects[0]
        value_index = int(value * 1000 + 5000)
        if target:
            cmds.blendShape(self.name, edit=True, inBetween=True, target=(out_object.name, index, target, value))
        else:
            num_vtx = out_object.num_vertices
            item_attr = self.inputTarget[0].inputTargetGroup[index].inputTargetItem[value_index]
            # Force add an element at given index
            item_attr.inputPointsTarget.value = [[0, 0, 0, 0]]*num_vtx
            item_attr.inputComponentsTarget.value = ['vtx[0:{}]'.format(num_vtx)]
        return self.inputTarget[0].inputTargetGroup[index].inputTargetItem[value_index]

    def force_evaluate(self):
        current = self.envelope.value
        if_auto_key = cmds.autoKeyframe(state=True, q=True)
        cmds.autoKeyframe(state=False)
        self.envelope.value = 1 if current else 0
        self.envelope.value = current
        cmds.autoKeyframe(state=if_auto_key)

    def get_history_order(self):
        """

        Returns:

        """
        return self.fn_node.historyLocation()

    def get_targets(self):
        """
        Get targets objects

        Returns:
            list: A list of target Nodes

        """
        base_objects = self.output_objects
        if not base_objects:
            return
        obj_array = OpenMaya.MObjectArray()
        targets = []
        base_obj = base_objects[0].object()

        for idx in self.get_weight_index_list():
            self.fn_node.getTargets(base_obj, idx, obj_array)
            for i in range(obj_array.length()):
                targets.append(Node(obj_array[i]))
        return targets

    def get_weight_index_list(self):
        """
        Get the index of valid targets from the weight list plug
        Returns:
            list: The list of target index
        """
        int_array = OpenMaya.MIntArray()
        self.fn_node.weightIndexList(int_array)
        return [int_array[i] for i in range(int_array.length())]

    def set_target_weight(self, target, val):
        """
        Set the weight to the given target. Accepted target is either the index or the name
        Args:
            target(str or int): Target physical index or target name
            val(float): Weight value

        """
        if isinstance(target, string_types):
            self.set_attr(target, val)
        elif isinstance(target, int):
            self.weight[target].value = val
        else:
            OpenMaya.MGlobal.displayError("Unsupported target value: {}".format(target))

    def import_target_weight_from_skin(self, data):
        """
        Import skin cluster weight data to blend shape target weights by
        matching influence index order to target order

        Args:
            data(dict):

        Returns:

        """
        num_targets = len(self.inputTarget[0].inputTargetGroup.indices)
        inf_idx_lists = data.get('influences')
        weight_list_data = data.get('weights')
        if not weight_list_data:
            OpenMaya.MGlobal.displayError("Failed to find weightList data")
            return
        num_inf = len(inf_idx_lists[0])
        if not num_inf:
            return
        vtx_count = len(weight_list_data)/num_inf

        joint_weight_map = {k: [0] * vtx_count for k in range(num_targets)}

        num_of_weights = len(weight_list_data)
        for vtx_index in range(vtx_count):
            for joint_index in range(num_targets):
                idx = vtx_index*num_inf + joint_index
                if idx < num_of_weights:
                    joint_weight_map[joint_index][vtx_index] = weight_list_data[idx]
        # Now we set the value back to blend shape
        for jnt_index, v in joint_weight_map.items():
            for vtx_index, val in enumerate(v):
                self.inputTarget[0].inputTargetGroup[jnt_index].targetWeights[vtx_index].value = val
        return joint_weight_map

    def decompose_pose_space_delta(self, target_points, target_group, inbetween_val=6000, threshold=0.001):
        """
        This method will set up pose space delta based on a target_mesh to make sure the output geo matching
        the target_mesh.
        Args:
            target_points(list): The sculpt target points
            target_group(int): The index of pose group on blend shape
            inbetween_val(int): The inbetwwn value. Blend shapes takes 5000 - 6000 as the range from 0 - 1
            threshold(float): The minimum delta value that will be valid for calculation

        """
        def __get_delta_result_list(num_vertex, offset, vertex_indexes,
                                    points_attribute, mesh, original_points):
            """

            Args:
                num_vertex:
                offset:
                vertex_indexes:
                points_attribute:
                mesh:
                original_points:

            Returns:

            """
            pnt_array = [offset]*num_vertex
            points_attribute.value = pnt_array
            delta_vectors = mesh.get_points(space='object')

            for vtx_id in vertex_indexes:
                delta = [dv-ov for dv, ov in zip(delta_vectors[vtx_id],
                                                 original_points[vtx_id])]
                delta_vectors[vtx_id] = delta
            return delta_vectors

        # 1. Reset the target input points to default value
        out_objects = self.output_objects
        if not out_objects:
            OpenMaya.MGlobal.displayError(
                "Blend shape {} has no output objects".format(self.name))
            return
        skin_mesh = out_objects[0]
        if not skin_mesh.type_name == "mesh":
            OpenMaya.MGlobal.displayError(
                "Blend shape output object {} is not mesh type".format(
                    skin_mesh.name))
            return

        target_item_attr = self.inputTarget[0].inputTargetGroup[target_group].inputTargetItem[inbetween_val]
        component_attr = target_item_attr.inputComponentsTarget
        points_attr = target_item_attr.inputPointsTarget

        num_vtx = skin_mesh.num_vertices
        neutral_points = [(0, 0, 0)]*num_vtx
        points_attr.value = neutral_points

        # set the component targets to default vtx[1:numVtx]
        component_attr.value = ["vtx[{}]".format(i) for i in range(num_vtx)]

        # extract point arrays from orig mesh, skin mesh and target mesh
        base_mesh = skin_mesh.get_intermediate_sibling()
        base_points = base_mesh.get_points(space='object')
        skin_points = skin_mesh.get_points(space='object')

        # make a copy of the base mesh for restoring the data
        copy_base_points = [pnt for pnt in base_points]
        vtx_list = []
        for idx, (skin_pnt, tgt_pnt) in enumerate(zip(skin_points, target_points)):

        # filter out the points in the target geo which are
        # identical to the skinned geo
            dist = pow(sum([(a - b)*(a - b) for a, b in zip(skin_pnt, tgt_pnt)]), 0.5)
            if dist > threshold:
                vtx_list.append(idx)

        x_delta_vectors = __get_delta_result_list(
            num_vtx,
            (1, 0, 0),
            vtx_list,
            points_attr,
            skin_mesh,
            skin_points)
        y_delta_vectors = __get_delta_result_list(
            num_vtx,
            (0, 1, 0),
            vtx_list,
            points_attr,
            skin_mesh,
            skin_points)

        z_delta_vectors = __get_delta_result_list(
            num_vtx,
            (0, 0, 1),
            vtx_list,
            points_attr,
            skin_mesh,
            skin_points)

        util = OpenMaya.MScriptUtil()
        orig_matrix = OpenMaya.MMatrix()
        target_matrix = OpenMaya.MMatrix()

        result_point_array = []
        result_component_list = []
        for i in vtx_list:
            orig_matrix_list = [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                base_points[i][0], base_points[i][1], base_points[i][2], 1.0
            ]
            util.createMatrixFromList(orig_matrix_list, orig_matrix)

            target_matrix_list = [
                x_delta_vectors[i][0], x_delta_vectors[i][1], x_delta_vectors[i][2], 0.0,
                y_delta_vectors[i][0], y_delta_vectors[i][1], y_delta_vectors[i][2], 0.0,
                z_delta_vectors[i][0], z_delta_vectors[i][1], z_delta_vectors[i][2], 0.0,
                skin_points[i][0], skin_points[i][1], skin_points[i][2], 1.0
            ]
            util.createMatrixFromList(target_matrix_list, target_matrix)
            target_point = OpenMaya.MPoint(*target_points[i])
            point = target_point * target_matrix.inverse() * orig_matrix
            base_points[i] = [point.x, point.y, point.z]

            result_component_list.append("vtx[{}]".format(i))

            result_point_array.append(
                [base_points[i][0] - copy_base_points[i][0],
                 base_points[i][1] - copy_base_points[i][1],
                 base_points[i][2] - copy_base_points[i][2]]
            )

        flatten_list = list()
        for comp in result_component_list:
            split = comp[comp.index('[') + 1:-1].split(":")
            if split[0] == '*':
                flatten_list.extend(list(range(num_vtx)))
            elif len(split) == 1:
                flatten_list.append(int(split[0]))
            else:
                flatten_list.extend(list(range(int(split[0]), int(split[1]) + 1)))
        data_map = {idx: pnt for idx, pnt in zip(flatten_list, result_point_array)}
        result_point_array = [[0, 0, 0, 1]] * num_vtx
        for idx, pnt in data_map.items():
            result_point_array[idx] = pnt

        result_component_list = ['vtx[{}]'.format(i) for i in range(num_vtx)]
        points_attr.value = result_point_array
        component_attr.value = result_component_list

