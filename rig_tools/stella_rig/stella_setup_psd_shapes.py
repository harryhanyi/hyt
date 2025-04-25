# Load latest rig file, import shapes
# Set left arm and leg to FK
# Select shape meshes and run create_invert_shapes

import maya.cmds as cmds
import mhy.maya.rig.marking_menu as mm
import stella_rig.pose_interpolator as pipt
import os
import weight_tools

_ctrl_dict = {"Hip_L": "leg_hip_L_FKCTRL", 
              "Knee_L": "leg_knee_L_FKCTRL",
              "Ankle_L": "leg_ankle_L_FKCTRL",
              "Ball_L": "foot_ball_L_FKCTRL",
              "Shoulder_L": "arm_shldr_L_FKCTRL",
              "Elbow_L": "arm_elbow_L_FKCTRL",
              "Wrist_L": "arm_wrist_L_FKCTRL",
              }

_twist_dict = {"Hip_L": "HipPart1_L",
               "Wrist_L": "ElbowPart1_L",
               "Shoulder_L":"ShoulderPart1_L" }

_geo_list = ["shirt_GEO", "body_GEO", "gloveBoots_GEO"]

def reset_rig():
    mm._reset_pose("RIG", selected=False)
    cmds.setAttr("arm_ROOT_L_LIMBShape.IKFKBlend", 0)
    cmds.setAttr("leg_ROOT_L_LIMBShape.IKFKBlend", 0)
    cmds.setAttr("arm_ROOT_R_LIMBShape.IKFKBlend", 0)
    cmds.setAttr("leg_ROOT_R_LIMBShape.IKFKBlend", 0)
    return


def unpack_name_tokens(name):
    tokens = name.split("_")
    geo_token = tokens[0]
    driver = f"{tokens[1]}_{tokens[2]}"
    rotation = []
    for element in [tokens[3], tokens[4], tokens[5]]:
        if "n" in element:
            rotation.append(int(element[1:])*-1)
        else:
            rotation.append(int(element))

    rig_mesh = f"{geo_token}_GEO"
    if rig_mesh not in _geo_list:
        print(f"{name} is not correctly named, rig mesh info is missing!")
        return
    if '_R' in driver:
        driver_mir = driver.replace('_R', '_L')
        try:
            ctrl_mir = _ctrl_dict[driver_mir]
        except:
            print(f"{driver} hasn't defined FKCTRL!")
            return
        ctrl = ctrl_mir.replace('_L', '_R')
    else:
        try:
            ctrl = _ctrl_dict[driver]
        except:
            print(f"{driver} hasn't defined FKCTRL!")
            return
    return rig_mesh, ctrl, rotation, driver

def tokenize_rotation(rotation):
    if type(rotation) == list:
        str_list=[]
        for element in rotation:
            element = int(element)
            if element < 0:
                element = f'n{element*-1}'
            str_list.append(element)
        t_rot = f'{str_list[0]}_{str_list[1]}_{str_list[2]}'
    elif type(rotation) == str:
        t_rot = []
        tokens = rotation.split('_')
        for element in tokens:
            if "n" in element:
                t_rot.append(int(element[1:])*-1)
            else:
                t_rot.append(int(element))

    return t_rot


def create_invert_shapes(meshes=None):
    # Turn rig to FK
    reset_rig()
    if not meshes:
        mesh_list = cmds.ls(sl=1)
    else:
        mesh_list = meshes
    invert_meshes = []
    for mesh in mesh_list:
        if ":" in mesh:
            name = mesh.split(":")[1]
            temp_mesh = cmds.rename(mesh, name)
        else:
            temp_mesh = mesh
        rig_mesh, ctrl, rotation, driver = unpack_name_tokens(temp_mesh)
        print(rig_mesh, ctrl, rotation, driver)
        # Move mesh to zero
        cmds.xform(temp_mesh, worldSpace=True, 
                   translation=[0,0,0], 
                   rotation=[0,0,0])
        # Reset rig
        mm._reset_pose("RIG", selected=False)
        # Set Pose
        cmds.xform(ctrl, objectSpace=True, rotation=rotation)
        invert_mesh = cmds.invertShape(rig_mesh, temp_mesh)
        invert_meshes.append(cmds.rename(invert_mesh, f'{mesh}_inv'))

    return invert_meshes

def setup_psd(meshes, mirror=True):
    # Create poseInterpolator if not exist and create pose, connect blendshapes
    invert_meshes = create_invert_shapes(meshes)

    for i in range(0,len(meshes)):
        rig_mesh, ctrl, rotation, driver = unpack_name_tokens(meshes[i])
        # Create interpolator node
        if rotation[0]==0:
            pose_type='swing'
        elif rotation[1]==0 and rotation[2]==0:
            pose_type='twist'
            if '_R' in driver:
                driver = _twist_dict[driver.replace('_R','_L')].replace('_L', '_R')
            else:
                driver = _twist_dict[driver]
        else:
            pose_type='swingandtwist'
        pl_name = f'{driver}_interpolator'
        if not pipt.isPoseInterpolator(pl_name):
            cmds.select(driver, r=1)
            tpl = pipt.createPoseInterpolatorNode(pl_name, 1, 0)
        else:
            tpl = pl_name
        # Create Blend shape node
        bls_node = f'{rig_mesh}_ps_blendShape'
        if not cmds.objExists(bls_node): 
            cmds.blendShape([invert_meshes[i], rig_mesh], name=bls_node, foc=True)
        elif not cmds.objExists(f'{bls_node}.{invert_meshes[i]}'):
            index = cmds.blendShape(bls_node, q=1, weightCount=True)
            cmds.blendShape(bls_node, edit=True, t=(rig_mesh, index, invert_meshes[i], 1.0))
        
        # Create Pose
        t_rot = tokenize_rotation(rotation)
        pose_name = f'{driver}_{t_rot}'
        if pose_name not in pipt.poseInterpolatorPoseNames(tpl):
            reset_rig()
            cmds.xform(ctrl, objectSpace=True, rotation=rotation)
            cmds.select(driver, r=1)
            pose_index = pipt.poseInterpolatorAddPose(tpl, pose_name)
        else:
            pose_index = pipt.poseInterpolatorPoseIndex(tpl, pose_name)
        
        try:
            cmds.connectAttr(f'{tpl}.output[{pose_index}]', f'{bls_node}.{invert_meshes[i]}')
            print(f'{tpl}.{pose_name} and {bls_node}.{invert_meshes[i]} is successfully setup!')
        except:
            print(f'{tpl}.{pose_name} and {bls_node}.{invert_meshes[i]} is already connected!')
            pass
        
        
        pipt.poseInterpolatorSetPoseType(tpl, pose_name, pose_type)

    
    
    if mirror:
        mm._reset_pose("RIG", selected=False)
        mir_meshes = []
        for inv_mesh in invert_meshes:
            if '_L_' in inv_mesh and inv_mesh.replace('_L_', '_R_') not in invert_meshes:
                mir_meshes.append(inv_mesh)

        mirror_meshes = mirror_shapes(mir_meshes)
        tpls = pipt.listPoseInterpolators()
        for tpl in tpls:
            poses = pipt.poseInterpolatorPoseNames(tpl)
            pipt.poseInterpolatorMirror(tpl, poses, '_L', '_R', 0, 0, 0)
        for inv_mesh in mirror_meshes:
            rig_mesh, ctrl, rotation, driver = unpack_name_tokens(inv_mesh)
            if rotation[1]==0 and rotation[2]==0:
                driver = _twist_dict[driver.replace('_R','_L')].replace('_L','_R')
            tpl = f'{driver}_interpolator'
            bls_node = bls_node = f'{rig_mesh}_ps_blendShape'
            index = cmds.blendShape(bls_node, q=1, weightCount=True)
            cmds.blendShape(bls_node, edit=True, t=(rig_mesh, index, inv_mesh, 1.0))
            t_rot = tokenize_rotation(rotation)
            pose_name = f'{driver}_{t_rot}'
            pose_index = pipt.poseInterpolatorPoseIndex(tpl, pose_name)
            try:
                cmds.connectAttr(f'{tpl}.output[{pose_index}]', f'{bls_node}.{inv_mesh}')
                print(f'{tpl}.{pose_name} and {bls_node}.{inv_mesh} is successfully setup!')
            except:
                print(f'{tpl}.{pose_name} and {bls_node}.{inv_mesh} is already connected!')
                pass

    return

def mirror_shapes(meshes):
    # Mirror shapes with slitly asymmetry
    rig_mesh_dict = {}
    for rig_mesh in _geo_list:
        cmds.select(cl=1)
        dup_base_mesh = cmds.duplicate(rig_mesh, name=f'{rig_mesh}_base')[0]
        dup_mirror_mesh = cmds.duplicate(rig_mesh, name=f'{rig_mesh}_mirror' )[0]
        cmds.setAttr(f'{dup_base_mesh}.scaleX', lock=False)
        cmds.setAttr(f'{dup_base_mesh}.scaleX', -1)
        cmds.select(dup_mirror_mesh, dup_base_mesh)
        cmds.CreateWrap(dup_mirror_mesh, dup_base_mesh)
        rig_mesh_dict[rig_mesh] = [dup_base_mesh, dup_mirror_mesh]
        cmds.parent(dup_base_mesh, world=True)
        cmds.parent(dup_mirror_mesh, world=True)
    mirror_list = []
    for mesh in meshes:    
        rig_mesh = unpack_name_tokens(mesh)[0]
        dup_base_mesh,dup_mirror_mesh = rig_mesh_dict[rig_mesh]
        temp_bld = f'{dup_base_mesh}_psd_mirror_temp_blendshape'
        if not cmds.objExists(temp_bld):
            cmds.blendShape(mesh, dup_base_mesh, name=temp_bld)
        elif not cmds.objExists(f'{temp_bld}.{mesh}'):
            cmds.select(cl=1)
            index = cmds.blendShape(temp_bld, q=1, weightCount=True)
            cmds.blendShape(temp_bld, edit=True, t=(dup_base_mesh, index, mesh, 1.0))
            print(temp_bld, dup_base_mesh, index, mesh)
        bld_weight = f'{temp_bld}.{mesh}'
        cmds.setAttr(bld_weight,1) 
        mirror_mesh = cmds.duplicate(dup_mirror_mesh, name=mesh.replace('_L_', '_R_'))[0]
        mirror_list.append(mirror_mesh)
        cmds.setAttr(bld_weight, 0)
    for key in rig_mesh_dict:
        cmds.delete(rig_mesh_dict[key])
    
    return mirror_list



def import_psd():
    """TO DO"""

def add_psd_pose(tpl):
    blend_shapes = pipt.poseInterpolatorConnectedShapeDeformers(tpl)
    driver = tpl.replace('_interpolator', '')
    ctrl = get_ctrl(driver)[0]

    rotation = cmds.xform(ctrl, objectSpace=True, q=1, rotation=1)
    if rotation[0]==0:
            pose_type='swing'
    elif rotation[1]==0 and rotation[2]==0:
        pose_type='twist'
    else:
        pose_type='swingandtwist'

    t_rot = tokenize_rotation(rotation)
    pose_name = f'{driver}_{t_rot}'
    
    index = pipt.poseInterpolatorAddShapePose(tpl, pose_name, pose_type, blend_shapes, 1)

    return index
    

def export_psd_shapes(asym_tpl=None):
    tpls = pipt.listPoseInterpolators()
    shape_list = []
    for tpl in tpls:
        if '_R' in tpl and tpl not in asym_tpl:
            pass
        else:
            poses = pipt.poseInterpolatorPoseNames(tpl)
            blend_shapes = pipt.poseInterpolatorConnectedShapeDeformers(tpl)
            rig_meshes = [cmds.blendShape(bl, q=1, g=1)[0] for bl in blend_shapes]
            driver = pipt.poseInterpolatorDrivers(tpl)[0]
            for index in range(3, len(poses)):
                mm._reset_pose("RIG", selected=False)
                t_rot = poses[index].replace(f'{driver}_','')
                rotation = tokenize_rotation(t_rot)
                ctrl, temp_driver = get_ctrl(driver)
                cmds.xform(ctrl, objectSpace=True, rotation=rotation)

                for mesh in rig_meshes:
                    mesh = mesh.replace('Shape','')
                    shape_name = f"{mesh.replace('GEO','')}{temp_driver}_{t_rot}"
                    dup_shape = cmds.duplicate(mesh, name = shape_name)[0]
                    cmds.parent(dup_shape, world=True)
                    shape_list.append(dup_shape)
    
    return shape_list

def get_ctrl(driver):
    mirror = 0
    if '_R' in driver:
        driver = driver.replace('_R', '_L')
        mirror = 1

    temp_driver = driver
    if driver not in _ctrl_dict:
        for item in _twist_dict.items():
            if item[1] == driver:
                temp_driver = item[0]
            else:
                pass
                        
    ctrl = _ctrl_dict[temp_driver]
    if mirror:
        temp_driver = temp_driver.replace('_L', '_R')
        ctrl = ctrl.replace('_L','_R')
    return ctrl, temp_driver

def setup_help_surf(surf, driver_list=None, mirror=False):
    # Surf name rule: rig_mesh (without GEO), driver, surf name, surf as extend
    tokens = surf.split('_')
    rig_mesh = f'{tokens[0]}_GEO'
    driver = f'{tokens[1]}_{tokens[2]}'
    side = tokens[2]
    surf_name = tokens[3]
    drivers = get_all_drivers(rig_mesh)
    if not driver_list:
        if cmds.objExists(driver):
            drivers = [driver]
    else:
        drivers = driver_list
        
    inter_geo = f'{surf_name}_{side}_dgeo'

    cmds.rebuildSurface(surf, ch=1, rpo=1, kr=0, end=1, kcp=1, kc=0, po=1, name=inter_geo)
    cons_nodes = cmds.listHistory(inter_geo)
    for obj in cons_nodes:
        if cmds.objectType(obj) == 'nurbsTessellate':
            cmds.setAttr(f'{obj}.format', 3)
    
    cmds.delete(inter_geo, constructionHistory=True)
    cmds.select(rig_mesh, inter_geo)
    # Transfer weight from rig_mesh to inter_geo
    wt = weight_tools.WeightTools()
    wt.transfer_skin()
    surf_connect(surf, inter_geo)
    for driver in drivers:
        tpl = f'{driver}_interpolator'
        if '_L' in driver:
            ctrl, temp_driver = get_ctrl(driver)
        elif '_R' in driver:
            ctrl, temp_driver = get_ctrl(driver.replace('_R','_L'))
            ctrl = ctrl.replace('_L','_R')
            temp_driver = temp_driver.replace('_L','_R')

        temp_geo = cmds.duplicate(inter_geo, name=f'{inter_geo}_temp')[0]
        try:
            cmds.parent(temp_geo, world=True)
        except:
            print(f'{temp_geo} is already unparented.')
        cmds.select(temp_geo, rig_mesh, r=1)
        cmds.CreateWrap(temp_geo, rig_mesh)

        poses = pipt.poseInterpolatorPoseNames(tpl)
        blend_shape = f'{surf_name}_{side}_psd_blendshape'
        temp_meshes=[temp_geo]
        for i in range(3,len(poses)):
            pose = poses[i]
            mm._reset_pose("RIG", selected=False)
            temp_tokens = pose.split('_')
            rot = f'{temp_tokens[2]}_{temp_tokens[3]}_{temp_tokens[4]}'
            rotation = tokenize_rotation(rot)
            cmds.xform(ctrl, objectSpace=True, rotation=rotation)
            dup_mesh = cmds.duplicate(temp_geo, name=f'{surf_name}_{temp_driver}_{rot}')[0]
            invert_mesh = cmds.invertShape(inter_geo, dup_mesh)
            shape_mesh = cmds.rename(invert_mesh, invert_mesh+'_inv')
            cmds.select(cl=True)
            # Setup blendshape
            if not cmds.objExists(blend_shape):
                cmds.blendShape(shape_mesh, inter_geo, name=blend_shape, foc=True)
                cmds.setAttr(f'{blend_shape}.envelope',0)
            else:
                index = cmds.blendShape(blend_shape, q=1, weightCount=True)
                cmds.blendShape(blend_shape, edit=True, t=(inter_geo, index, shape_mesh, 1.0))
                cmds.setAttr(f'{blend_shape}.envelope',0)

            index = pipt.poseInterpolatorPoseIndex(tpl,pose)
            cmds.connectAttr(f'{tpl}.output[{index}]', f'{blend_shape}.{shape_mesh}')
            temp_meshes.append(dup_mesh)
            temp_meshes.append(shape_mesh)
        
        cmds.delete(temp_meshes)
    cmds.setAttr(f'{blend_shape}.envelope', 1)
    if mirror:
        surf_mir = cmds.duplicate(surf, name=surf.replace('_L','_R'))
        for axis in 'xyz':
            for attr in 'trs':
                cmds.setAttr(f'{surf_mir}.{attr}{axis}', lock=False)
        cmds.setAttr(f'{surf_mir}.scaleX', -1)
        cmds.makeIdentity(surf_mir, apply=True, rotate=True, scale=True, translate=True)
        setup_help_surf(surf_mir, mirror=False)
    mm._reset_pose("RIG", selected=False)
    return

def get_all_drivers(rig_mesh):
    history = cmds.listHistory(rig_mesh)
    blendshape = cmds.ls(history, type='blendShape')[0]
    tpls = cmds.listConnections(blendshape, source=True, destination=False, type='poseInterpolator')
    drivers = []
    for tpl in tpls:
        driver = pipt.poseInterpolatorDriverName(tpl, 0)
        drivers.append(driver)
    return drivers

def surf_connect(surf, inter_geo):
    cvs = cmds.ls(f'{surf}.cv[*][*]', fl=1)
    vets = cmds.ls(f'{inter_geo}.vtx[*]', fl=1)
    for cv in cvs:
        u_num = cv.split('cv[')[-1].split('][')[0]
        v_num = cv.split('][')[-1].split(']')[0]
        cv_pos = cmds.pointPosition(cv, world=True)
        mini_dist = None
        sel_vet = None
        for vet in vets:
            vet_pos = cmds.pointPosition(vet, world=True)
            new_dist = (cv_pos[0]-vet_pos[0])**2 + (cv_pos[1]-vet_pos[1])**2 + (cv_pos[2]-vet_pos[2])**2 
            if mini_dist:
                if mini_dist > new_dist:
                    mini_dist = new_dist
                    sel_vet = vet
            else:
                mini_dist = new_dist
                sel_vet = vet

        cv_cls = cmds.cluster(cv, name=f'{surf}_{u_num}_{v_num}_cls')[1]
        temp_cns = cmds.pointOnPolyConstraint(inter_geo, cv_cls, maintainOffset=False)[0]
        uv_comp = cmds.polyListComponentConversion(sel_vet, toUV=1)[0]
        vet_uv = cmds.polyEditUV(uv_comp,q=1)
        cmds.setAttr(f'{temp_cns}.{inter_geo}U0', vet_uv[0])
        cmds.setAttr(f'{temp_cns}.{inter_geo}V0', vet_uv[1])
        vets.remove(sel_vet) 

    return

def run_setup_psd(shape_files):
    #set arm and leg to FK
    cmds.setAttr('leg_ROOT_L_LIMBShape.IKFKBlend',0)
    cmds.setAttr('arm_ROOT_L_LIMBShape.IKFKBlend',0)
    for file_path in shape_files:
        if os.path.exists(file_path):
            cmds.file(file_path, i=True, mergeNamespacesOnClash=False, usingNamespaces=False)











