import mhy.maya.rig.face.targets_to_influence as ti
import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.attribute import Attribute

import mhy.maya.rigtools.pose_editor.ui.manager as manager
import mhy.maya.rigtools.pose_editor.ui.actions as actions
from mhy.maya.rig.utils import add_influence_tag_attribute

# Variable user need to set
target_list = ['MouthCorner_UpBack_L', 'MouthCorner_UpBack_R']
namespace = 'result2:'

pose_list = []


def snap_to_target(target_joints):
    to_sel = []
    for i in target_joints:
        inst = ti.TracerHierarchy(i.replace(namespace, ""))
        inst.match_to_target_joint(i, True)
        tracer = inst.get_tracer()
        if tracer:
            to_sel.append(tracer.name)
        ctr = inst.get_fk_ctrl()
        if tracer:
            to_sel.append(ctr.name)
    cmds.select(to_sel)

    filter_sel = []
    for i in to_sel:
        item = Node(i)
        test = False
        if i.endswith('_TRACER'):
            orig_u = item.originU.value
            orig_v = item.originV.value
            current_u = item.parameterU.value
            current_v = item.parameterV.value
            if abs(current_u) > 0.01 or abs(current_v) > 0.001:
                filter_sel.append(i)
        else:
            for a in 'tr':
                for b in 'xyz':
                    if a == 't':
                        threshold = 0.01
                    if a == 'r':
                        threshold = 5
                    if abs(round(item.get_attr(a + b), 5)) > threshold:
                        test = True
                        filter_sel.append(i)
                        break
                if test:
                    break
    updated_objects = list(set(filter_sel))
    cmds.select(updated_objects)
    return updated_objects


def reset_position(obj):
    for i in 'tr':
        for j in 'xyz':
            attr = Attribute(obj + '.' + i + j)
            if attr.is_free_to_change:
                attr.value = 0


# clean up
for i in cmds.ls(type='joint'):
    if Node(i).has_attr('nodezoo_custom_type'):
        Node(i).attr('nodezoo_custom_type').locked = False
        cmds.deleteAttr("{}.nodezoo_custom_type".format(i))

for i in cmds.ls('*_TRACER'):
    driven_attr_value = {}

    val = Node(i).get_attr('originU')
    driven_attr_value['parameterU'] = {'neutral': 0}
    val = Node(i).get_attr('originV')
    driven_attr_value['parameterV'] = {'neutral': 0}

    add_influence_tag_attribute(i, driven_attr_value)

fbx_mesh = Node('{}FaceShape'.format(namespace))
skin = fbx_mesh.get_deformers(type_=['skinCluster'])[0]

target_joints = [i for i in skin.influences]

my_dict = {tgt: idx for idx, tgt in enumerate(target_list)}

poses_to_run = target_list

controller = manager.Pose_Model.controller
for target in target_list[::-1]:
    split = target.split('_')
if len(split) == 3 and split[1].isdigit():
    key_val = int(split[1])
target = "{}_{}".format(split[0], split[-1])
if not controller.find_pose(target):
    manager.Pose_Model.create_pose(target, manager.Pose_Model.root_item)

manager.main_window.do_reset_all_poses()
full_length = len(target_list)
for target in poses_to_run:
    idx = my_dict.get(target)
cmds.currentTime(idx + 2)

split = target.split('_')
key_val = 10
if len(split) == 3 and split[1].isdigit():
    key_val = 10 * float(split[1]) / 100.0
target = "{}_{}".format(split[0], split[-1])
manager.Pose_View.select_pose(target)
if target not in pose_list:
    manager.main_window.weight_slider.do_reset_pose(prompt=False)

updated_objects = snap_to_target(target_joints)
actions.do_influences_add()
manager.main_window.weight_slider.slider_widget.slider.setValue(key_val * 100)
for obj in updated_objects:
    reset_position(obj)
updated_objects = snap_to_target(target_joints)
manager.main_window.weight_slider.do_key_current_pose()
manager.main_window.do_reset_all_poses()
cmds.dgdirty(cmds.ls(type='blendWeighted'))
pose_list.append(target)
print 'In Progress: {}/{}'.format(idx + 1, full_length)
print 'Done!!'
cmds.dgdirty(cmds.ls(type='blendWeighted'))

# C:\Users\admin\Documents\dem-bones\build\Release\DemBones.exe --nWeightsIters=0 -i=C:\Users\admin\Desktop\skin.fbx -a=C:\Users\admin\Desktop\target_anim2.abc -o=C:\Users\admin\Desktop\result2.fbx