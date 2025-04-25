"""
    Delta creating and editing
    turn the delta group visibility on to edit the delta,
    turn the delta group visibility off when finish the edit.
"""
import six
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from mhy.maya.rigtools.pose_editor.api.symmetry import Symmetry
import mhy.maya.rigtools.pose_editor.api.utils as utils
from mhy.maya.nodezoo.attribute import Attribute


class PoseTarget(object):
    __target_set = 'Targets_SET'

    def __init__(self, weight_attr, weight=1.0, pose=None):
        """

        Args:
            weight_attr(str or Attribute): Required argument the determines the target index on the blend shape node
            pose(Pose): The pose associated with this target. Pose is optional so target can still work independently
            from an weight attribute on a blend shape node
            weight(float): The weight value of this target range from 0.0 to 1.0

        """
        assert weight > 0.0, "The neutral pose can't have a delta pose."
        self.weight_attribute = weight_attr
        if isinstance(self.weight_attribute, six.string_types):
            self.weight_attribute = Attribute(self.weight_attribute)

        self.__pose = pose
        self.__weight = weight

        if self.pose:
            prefix = self.pose.name
        else:
            prefix = self.weight_attribute.name.replace('.', '_')

        self.name = prefix + "_" + self._decorate_name(weight)

    def __repr__(self):
        if self.pose:
            pose_name = self.pose.name
        else:
            pose_name = ""

        return "<PoseEditor.{0}: '{1}_{2}' at <{3}>>".format(
            self.__class__.__name__,
            pose_name,
            self.__weight,
            hex(id(self))
        )

    @property
    def blend_shape(self):
        return self.weight_attribute.node

    @property
    def output_mesh(self):
        """
        Get the output mesh from this target instance

        Returns:
            Mesh: The output mesh
            None: This target has no output mesh
        """
        out_objects = self.blend_shape.output_objects
        if not out_objects:
            return
        return out_objects[0]

    @property
    def neutral_mesh(self):
        """
        Get neutral mesh from this target instance if exists
        Returns:
            Mesh: The intermediate mesh
        """
        out_mesh = self.output_mesh
        intermediate = out_mesh.get_intermediate_sibling()
        if intermediate:
            return intermediate

    @property
    def weight(self):
        return self.__weight

    @property
    def in_between_index(self):
        return int(5000 + self.weight * 1000)

    @property
    def pose(self):
        return self.__pose

    @property
    def symmetric_table(self):
        if self.controller:
            return self.controller.symmetric_table
        else:
            neutral_mesh = self.neutral_mesh
            if not neutral_mesh:
                return
            table = utils.create_mirror_list([self.neutral_mesh.name])
            return table

    @property
    def index(self):
        """
        Get the index on weight plug for this pose target
        Returns:

        """
        idx = self.weight_attribute.index
        return idx

    @property
    def target_name(self):
        return self.weight_attribute.alias

    @property
    def target_group_attr(self):
        idx = self.index
        return self.blend_shape.inputTarget[0].inputTargetGroup[idx]

    @property
    def mesh_delta(self):
        """
        Get the delta information from input points target attribute
        Returns:
            list: A list of point data
        """
        target_attr = self.target_group_attr.inputTargetItem[self.in_between_index]
        return target_attr.inputPointsTarget.value

    @mesh_delta.setter
    def mesh_delta(self, value):
        """
        Set mesh delta value
        Args:
            value(list): A list of point data

        """
        target_attr = self.target_group_attr.inputTargetItem[self.in_between_index]
        target_attr.inputPointsTarget.value = value

    @property
    def target_components(self):
        """
        Get the delta information from input points target attribute
        Returns:
            list: A list of point data
        """
        target_attr = self.target_group_attr.inputTargetItem[self.in_between_index]
        return target_attr.inputComponentsTarget.value

    @target_components.setter
    def target_components(self, value):
        """
        Get the delta information from input points target attribute
        Returns:
            list: A list of point data
        """
        target_attr = self.target_group_attr.inputTargetItem[self.in_between_index]
        target_attr.inputComponentsTarget.value = value

    def destroy(self):
        """
        Remove this target from blend shape node

        """
        target_item = self.target_group_attr.inputTargetItem[self.in_between_index]
        target_item.remove()

        if not self.target_group_attr.inputTargetItem.indices:
            weight_attr = self.blend_shape.weight[self.index]
            source_node = weight_attr.source_node
            if source_node and source_node.type_name.startswith('animCurve'):
                source_node.delete()
            weight_attr.alias = None
            weight_attr.remove()

    def mirror(self, source=Symmetry.LEFT, mirror_plane='YZ',  flip=False, dry_run=False):
        """
        Mirror target data
        Args:
            source(int): The source side: LEFT = 1, RIGHT = 2
            mirror_plane:
            flip:
            dry_run:

        Returns:

        """
        symmetric_table = self.symmetric_table
        if not symmetric_table:
            OpenMaya.MGlobal.displayError("Failed to get symmetric table for mirroring")
            return

        n_axis = utils.mirror_plane_return(mirror_plane, mode='nAxis')
        z_axis = utils.mirror_plane_return(mirror_plane, mode='zAxis')

        # combine point and index into sub lists (X, Y, Z, vtxNumber), ex: (-0.2749, 0.22717, 0.0, 92)
        point_index = utils.combine_point_index(self.blend_shape.name, self.index, self.in_between_index)

        positive_index = []
        for i in symmetric_table:
            if i[0] != i[1]:
                positive_index.append(i[0])

        # Gets all index from the data acquired of the corrective
        delta_index = []
        for u in point_index:
            delta_index.append(int(u[-1]))

        # Separating what is positive, negative or middle based on position of the
        # index of the sub list and if they are the same result the middle.
        # Left > Post // Right > Neg
        # Ex: [[15, 13], [3, 1], [10, 10],...]  the number 15, 3 are Positive while
        # 13, 1 are Negative and the 10 is the middle
        pos_index = []
        neg_index = []
        zero_index = []
        for x in range(len(delta_index)):
            if delta_index[x] in positive_index:
                pos_index.append(delta_index[x])
            else:
                for mi in symmetric_table:
                    if mi[0] != mi[1]:
                        if delta_index[x] == mi[1]:
                            neg_index.append(delta_index[x])
                            break
                    else:
                        zero_index.append(delta_index[x])
                        break

        # Check if the mirror is from left to right and set side index as pos or neg index
        if flip:
            # Flip everything no matter the option of PosToNeg checkBox
            side_index = pos_index + neg_index + zero_index
        else:
            # Else, check if the posToNeg is to continue the sideIndx as pos or neg index
            if source == Symmetry.LEFT:
                side_index = pos_index + zero_index
            else:
                side_index = pos_index + zero_index

        point_index_mirrored = []
        # loop at the length of the pointIndex (See annotation above)
        if not flip:
            # MIRROR MODE
            for pi in range(len(point_index)):
                if point_index[pi][3] in side_index:
                    checked_index = point_index[pi][3]
                    # Check in the mirror List
                    for mi in symmetric_table:
                        if source == Symmetry.LEFT:
                            if mi[0] == checked_index:
                                if mi[1] != mi[0]:
                                    point_index_mirrored.append(
                                        utils.mirror_point_index(point_index[pi], mi[1], n_axis))

                                    point_index_mirrored.append(
                                        utils.mirror_point_index(point_index[pi], mi[0], n_axis=None))
                                    break
                                else:
                                    point_index_mirrored.append(
                                        utils.mirror_point_index(point_index[pi], point_index[pi][3], z_axis))
                                    break

                        else:
                            if mi[1] == checked_index:
                                if mi[1] != mi[0]:
                                    point_index_mirrored.append(
                                        utils.mirror_point_index(
                                            point_index[pi], mi[0], n_axis))

                                    point_index_mirrored.append(
                                        utils.mirror_point_index(
                                            point_index[pi], mi[1], n_axis=None))
                                    break
                                else:
                                    point_index_mirrored.append(
                                        utils.mirror_point_index(
                                            point_index[pi], point_index[pi][3], z_axis))
                                    break
        else:
            # FLIP MODE
            for pi in range(len(point_index)):
                if point_index[pi][3] in side_index:
                    checked_index = point_index[pi][3]
                    for mi in symmetric_table:
                        if mi[0] == checked_index:
                            point_index_mirrored.append(
                                utils.mirror_point_index(point_index[pi], mi[1], n_axis))
                            break
                        elif mi[1] == checked_index:
                            point_index_mirrored.append(
                                utils.mirror_point_index(point_index[pi], mi[0], n_axis))
                            break

        # Ordering and preparing list to be applied after
        delta, components = utils.index_point_to_delta_data(point_index_list=point_index_mirrored)

        num_vtx = self.output_mesh.num_vertices

        # Need to fill in the missing components and put delta data in order
        flatten_list = list()
        for comp in components:
            split = comp[comp.index('[') + 1:-1].split(":")
            if split[0] == '*':
                flatten_list.extend(list(range(num_vtx)))
            elif len(split) == 1:
                flatten_list.append(int(split[0]))
            else:
                flatten_list.extend(list(range(int(split[0]), int(split[1]) + 1)))

        data_map = {idx: pnt for idx, pnt in zip(flatten_list, delta)}

        delta = [[0, 0, 0, 1]] * num_vtx
        for idx, pnt in data_map.items():
            delta[idx] = pnt

        components = ['vtx[{}]'.format(i) for i in range(num_vtx)]

        if not dry_run:
            self.mesh_delta = delta
            self.target_components = components
        return delta, components

    def save_sculpt_to_target(self, target_points, threshold=0.001):
        """
        Save the sculpt
        Args:
            target_points:
            threshold:

        Returns:

        """
        bs_node = self.blend_shape
        if not bs_node:
            return
        in_between = int(5000 + 1000*self.weight)

        bs_node.decompose_pose_space_delta(
            target_points,
            self.index,
            inbetween_val=in_between,
            threshold=threshold)

    @staticmethod
    def _decorate_name(data):
        str_name = str(data)
        if isinstance(data, float):
            if '.' in str_name:
                return str_name.replace('.', '_')
            else:
                return str_name+'_0'
        else:
            raise(Exception("The pose target's weight must be float."))

    def _make_sets(self):
        """
        Create a set storing all the sculpt meshes
        Returns:
            str: The name of created sets
        """
        if cmds.objExists(self.__target_set):
            return self.__target_set
        self.__target_set = cmds.sets(name=self.__target_set)
        return self.__target_set

    @property
    def target_set(self):
        """
        Get the target set. If not exists, create one
        Returns:
            str: The name of target mesh set
        """
        if not cmds.objExists(self.__target_set):
            return self._make_sets()
        return self.__target_set

    @property
    def target_mesh(self):
        """
        Get the target mesh from the pose controller by a message attribute connection
        Returns:
            str: The name of target mesh
        """
        if self.controller:
            return self.controller.target_mesh
        else:
            bs_node = self.blend_shape
            outputs = bs_node.out_objects
            if outputs:
                return outputs[0].name

    @property
    def mesh_size(self):
        """
        Get the size of target mesh
         Returns:
            list: The size of the bounding box of mesh
             in x, y, z axises
        """
        return utils.mesh_size(self.target_mesh)

    @property
    def controller(self):
        if self.pose:
            return self.pose.controller

    @property
    def target_blendshape(self):
        return self.weight_attribute.node.name

    def reset(self):
        """
        Reset the sculpt pose, all the sculpt modification will be lost.
        """
        # this code could be faster if we use maya.API.OpenMaya
        # use MDataBock to nuke all the attribute of Float3 Array to zero.
        skin_mesh = self.output_mesh
        num_vtx = skin_mesh.num_vertices
        neutral_points = [(0, 0, 0)]*num_vtx
        target_attr = self.target_group_attr.inputTargetItem[self.in_between_index]
        target_attr.inputPointsTarget.value = neutral_points

    def get_data(self):
        """
        Reset the sculpt pose, all the sculpt modification will be lost.
        """
        # this code could be faster if we use maya.API.OpenMaya
        # use MDataBock to nuke all the attribute of Float3 Array to zero.
        data = {}
        mesh_delta = self.mesh_delta
        data['index'] = self.index
        data['weight'] = self.weight
        data['delta'] = self.mesh_delta
        data['alias'] = self.target_name
        data['delta'] = mesh_delta
        return data

    def set_data(self, data):
        """
        Set the target data to this target object.
        Args:
            data:

        Returns:

        """
        delta_info = data.get('delta')
        self.mesh_delta = delta_info
        vtx_count = self.output_mesh.num_vertices
        component_data = ['vtx[{}]'.format(i) for i in range(vtx_count)]
        # component_data = data.get('components')
        self.target_components = component_data
