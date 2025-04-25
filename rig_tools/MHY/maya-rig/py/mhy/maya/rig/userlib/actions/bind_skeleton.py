"""
bind skeleton actions
"""
import os
import json
import copy
from collections import OrderedDict

from maya import cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
from mhy.maya.scene import safe_open
import mhy.maya.maya_math as mmath

from mhy.maya.rig.base_actions import BaseRigSkelAction
import mhy.maya.rig.constants as const
import mhy.maya.rig.joint_utils as jutil


class CreateBindSkeleton(BaseRigSkelAction):
    """
    Creates a fresh set of bind skeleton from the tagged
    rig joints in the scene.
    """

    @pa.bool_param(default=True)
    def attach(self):
        """If True, attach the bind skeleton to the rig via constraints."""

    @pa.bool_param(default=False)
    def add_tweaker_ctrls(self):
        """If True, attach the bind skeleton to the rig via constraints."""

    def run(self):
        """Executes this action."""
        jutil.create_bind_skeleton(
            attach=self.attach.value,
            tweaker_ctrls=self.add_tweaker_ctrls.value)


def _fill_map_data(map_data):
    filled_data = copy.deepcopy(map_data)
    for k in ('name_map', 'inherit', 'orient_override'):
        if k not in map_data:
            map_data[k] = {}
            continue
        for key, val in map_data[k].items():
            fkey = NodeName.flip_node_name(key)
            if key != fkey and fkey not in filled_data[k]:
                fval = NodeName.flip_node_name(val) if val else val
                filled_data[k][fkey] = fval

    if 'aim_override' not in map_data:
        map_data['aim_override'] = {}
    for key, val in map_data['aim_override'].items():
        fkey = NodeName.flip_node_name(key)
        if key != fkey and fkey not in filled_data['aim_override']:
            val = copy.deepcopy(val)
            val['target'] = NodeName.flip_node_name(val['target'])
            faxis = val['aim_axis']
            if len(faxis) == 2:
                val['aim_axis'] = faxis[-1]
            else:
                val['aim_axis'] = '-' + faxis
            filled_data['aim_override'][fkey] = val

    to_remove = []
    for k in filled_data['inherit'].keys():
        if k in filled_data['name_map']:
            to_remove.append(k)
    for k in to_remove:
        filled_data.pop('name_map')

    return filled_data


def _flip_dict(dct):
    fdict = {}
    for key, val in dct.items():
        fdict[val] = key
    return fdict


class ImportBindSkeleton(BaseRigSkelAction):
    """
    Imports a pre-built bind skeleton and fit it onto
    the rig according to a mapping JSON file.

    Mapping JSON file keys:

        + *name_map*:
            Maps each bind joint onto a proper rig joint.
            Each bind joint inherits the rig joint's world matrix.
        + *aim_override*:
            Overrides a bind joints orientation by aimming it to
            a target rig joint. Supportted keys are:

                + target: The target rig joint.
                + aim_axis: The axis to aim.
                + flatten: If True, flatten the orientation to world space.

        + *orient_override*:
            Overrides a bind joints orientation by applying
            world space rotation values.
        + *inherit*:
            Bind joint on the left side directly inherits the transform
            from the bind joint on the right side.

    Mapping JSON file example:

    .. code-block:: json

        {
            "name_map": {
                "bind_joint_a": "rig_joint_a",
                "bind_joint_b": "rig_joint_b"
            },
            "aim_override": {
                "bind_joint": {
                    "target": "rig_joint",
                    "aim_axis": "-y",
                    "flatten": true
                }
            },
            "orient_override": {
                "bind_joint": [-90, 0, 0]
            },
            "inherit": {
                "bind_joint_a": "bind_joint_b",
            }
        }
    """

    @pa.file_param(ext=('ma', 'mb', 'fbx'))
    def skeleton_file(self):
        """The skeleton file to import."""

    @pa.file_param(ext='json')
    def map_file(self):
        """The mapping JSON file."""

    @pa.bool_param(default=True)
    def attach(self):
        """If True, attach the bind skeleton to the rig via constraints."""

    @pa.bool_param(default=True)
    def auto_create_joint(self):
        """ If True, the action will auto generate mission bones."""

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If the given skeleton file is not found.
            ActionError: If the given mapping file is not found.
        """
        skel_file = self.skeleton_file.value
        if not skel_file or not os.path.isfile(skel_file):
            raise exp.ActionError(
                'Skeleton file empty or not found: {}'.format(skel_file))

        map_file = self.map_file.value
        if not map_file or not os.path.isfile(map_file):
            raise exp.ActionError(
                'Mapping file empty or not found: {}'.format(map_file))

        # import joints
        imp_nodes = safe_open(skel_file, i=True, returnNewNodes=True)
        joints = None
        if imp_nodes:
            joints = cmds.ls(imp_nodes, long=True, type='joint')
            sorted(joints).reverse()
        if not joints:
            raise exp.ActionError('No joints found in: {}'.format(skel_file))

        # load mapping data
        map_data = {}
        with open(map_file, 'r') as f:
            map_data = json.load(f)
        map_data = _fill_map_data(map_data)

        # establish rig joint to bind joint mapping
        node_map = OrderedDict()
        for joint in joints:
            if not cmds.objExists(joint):
                raise exp.ActionError('Joint not found: {}'.format(joint))
            joint = Node(joint)
            target = map_data['name_map'].get(joint.name)
            if target and cmds.objExists(target):
                target = Node(target)
            else:
                target = None
            node_map[joint] = target

            '''
            # get the aim relationship
            nodes = joint.get_children(type_='transform')
            nodes.append(joint.get_parent())
            joint_pos = joint.get_translation(space='world', as_tuple=False)
            found = False
            for axis in ('x', '-x', 'y', '-y', 'z', '-z'):
                vec = mmath.axis_to_vector(joint, axis)
                for node in nodes:
                    pos = node.get_translation(space='world', as_tuple=False)
                    aim_vec = (pos - joint_pos)
                    aim_vec.normalize()
                    if vec.isEquivalent(aim_vec, 0.001):
                        aim_map[joint] = (node, axis, False)
                        found = True
                        break
                if found:
                    break

            if not found:
                aim_data = map_data['aim_override'].get(joint.name)
                if not aim_data:
                    fjoint = NodeName.flip_node_name(joint)
                    aim_data = map_data['aim_override'].get(fjoint.name)
                    if aim_data:
                        aim_data = aim_data[:]
                        aim_data[0] = NodeName.flip_node_name(aim_data[0])
                        if len(aim_data[1]) == 2:
                            aim_data[1] = aim_data[1][-1]
                        else:
                            aim_data[1] = '-' + aim_data[1]
                if aim_data and cmds.objExists(aim_data[0]):
                    aim_data = aim_data[:]
                    aim_data[0] = Node(aim_data[0])
                    aim_map[joint] = aim_data
            '''

        for joint, target in node_map.items():
            if not target:
                continue

            # align bind joints to rig joints
            mat = target.get_matrix(space='world')
            joint.set_matrix(mat, space='world')
            joint.make_identity(apply=True, scale=True)

            # apply aim override
            aim_override = map_data['aim_override'].get(joint.name)
            if aim_override:
                aim_axis = aim_override['aim_axis']
                aim_vec = mmath.world_axis_to_vector(aim_axis).as_tuple()
                up_axis = mmath.closest_axis(
                    joint, target, 'z', exclude_axis=aim_axis)
                up_vec = mmath.world_axis_to_vector(up_axis).as_tuple()

                children = joint.get_children(type_='transform')
                for c in children:
                    c.set_parent(None)
                cns = joint.constrain(
                    'aim', aim_override['target'],
                    maintainOffset=False,
                    aimVector=aim_vec,
                    upVector=up_vec,
                    worldUpType='objectrotation',
                    worldUpObject=target,
                    worldUpVector=(0, 0, 1))
                cmds.delete(cns)
                if aim_override['flatten']:
                    mmath.flatten_orientation(joint, aim_axis)
                for c in children:
                    c.set_parent(joint)

            # apply orient override
            orient_override = map_data['orient_override'].get(joint.name)
            if orient_override:
                joint.set_rotation(orient_override, space='world')

            joint.make_identity(apply=True, rotate=True)

            # embed bind joint
            jutil.set_bind_joint(target, joint)

        # direct inherit joints
        for joint, target in map_data['inherit'].items():
            for j in (joint, target):
                if not cmds.objExists(j):
                    raise exp.ActionError('Joint not found: {}'.format(j))

            joint = Node(joint)
            mat = Node(target).get_matrix(space='world')
            joint.set_matrix(mat, space='world')
            joint.make_identity(apply=True, rotate=True, scale=True)

        # attach bind skel to rig
        if self.attach.value:
            for joint, target in node_map.items():
                if not target:
                    continue
                joint.constrain('parent', target, maintainOffset=True)
                joint.constrain('scale', target, maintainOffset=True)

            for joint, target in map_data['inherit'].items():
                target = node_map.get(Node(target))
                if not target:
                    continue
                joint = Node(joint)
                joint.constrain('parent', target, maintainOffset=True)
                joint.constrain('scale', target, maintainOffset=True)

        # parent joints to bind skeleton root
        if cmds.objExists(const.BIND_SKEL_ROOT):
            roots = []
            for node in imp_nodes:
                if 'transform' in cmds.nodeType(node, inherited=True) and \
                   not cmds.listRelatives(node, parent=True):
                    roots.append(node)
            if roots:
                cmds.parent(roots, const.BIND_SKEL_ROOT)

        # build missing bind joints
        if self.auto_create_joint.value:
            name_dict = _flip_dict(map_data['name_map'])
            jutil.create_bind_skeleton(
                attach=self.attach.value,
                name_dict=name_dict,
                name_rule=map_data.get('name_rule'),
                tweaker_ctrls=False)
