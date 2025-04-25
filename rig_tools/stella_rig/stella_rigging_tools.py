import maya.cmds as cmds
import json
import sys
import os
import maya.api.OpenMaya as om


_project_path = 'D:/workarea/rigs/stella_body'
_asset_path = 'assets/bodyRigAssets/connections'
_file_name = 'connection_data.json'
_connection_types = ['parentConstraint', 'pointConstraint', 'orientConstraint']

def export_connection_data(project_path=_project_path, asset_path=_asset_path, file_name=_file_name, selection=False, types=_connection_types):
    # Export parentConstraints of the deform skeleton skeleton
    cons_dict ={}
    data = {}
    if selection==False:
        deform_root = 'deform_skeleton'
        for type in types:
        # Get deform_skeleton and joints:
            temp_constraints = cmds.listRelatives(deform_root, ad=1, type=type)
            if temp_constraints:
                cons_dict[type]=temp_constraints
    else:
        objs = cmds.ls(sl=1)
        for type in types:
            temp_constraints=[]
            for obj in objs:
                constraints = cmds.listRelatives(obj, children=1, type=type)
                if constraints:
                    temp_constraints.append(constraints[0])
            cons_dict[type] = temp_constraints

    list = []
    for type in types:
        for con in cons_dict[type]:
            driven = cmds.listRelatives(con, parent=True)[0]
            driver = cmds.listConnections(f'{con}.target', source=True, destination=False)[0]
            list.append([driver, driven])
        
        data[type] = list

    json_file_path = f"{project_path}/{asset_path}/{file_name}"

    # Write the dictionary to a JSON file
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)  
        # `indent=4` makes it readable

    print(f"JSON file saved at: {json_file_path}")

def setup_surf_constraints(surf, joint_list=[], mirror=True):
    if joint_list==[]:
        joints = cmds.ls(sl=1, type='joint')
    else:
        joints = joint_list
    # Get the MObject of the surface
    sel = om.MSelectionList()
    sel.add(surf)
    surface_obj = sel.getDagPath(0)
    surface_fn = om.MFnNurbsSurface(surface_obj)
    geo_info = cmds.createNode('mhyGeometryInfo')

    cmds.connectAttr(f'{surf}.worldSpace',f'{geo_info}.targetGeometry')
    cmds.connectAttr(f'{surf}.worldMatrix',f'{geo_info}.targetMatrix')

    for index in range(0, len(joints)):
        # Select your surface and point (or provide names)
        pos = cmds.xform(joints[index], q=1, ws=1, t=1)
        point = om.MPoint(pos)
        # Get closest UV
        result = surface_fn.closestPoint(point, space=om.MSpace.kWorld)
        loc = cmds.group(name=f'{joints[index]}_loc', em=1)        
        cmds.connectAttr(f'{geo_info}.rotate[{index}]',f'{loc}.rotate')
        cmds.connectAttr(f'{geo_info}.translate[{index}]',f'{loc}.translate')
        cmds.setAttr(f'{geo_info}.coord[{index}].u', result[1])
        cmds.setAttr(f'{geo_info}.coord[{index}].v', result[2])
        cmds.setAttr(f'{geo_info}.coord[{index}].w', 1)
        cmds.parentConstraint(loc, joints[index], mo=True)

    if mirror:
        m_joints=[]
        for jnt in joints:
            m_joints.append(jnt.replace('_L','_R'))
        m_surf = surf.replace('_L','_R')
        setup_surf_constraints(m_joints, m_surf, mirror=False)

def setup_blendshape_weightmap(blendshape, joints=[]):
    # Setup blendshape weightmap with jont weight to isolate the deform
    # While vertex controlled by certain joints will be removed from blendshape
    rig_mesh = cmds.blendShape(blendshape, q=1,g=1)[0]
    history = cmds.listHistory(rig_mesh)
    skin = cmds.ls(history, type='skinCluster')[0]
    vers = cmds.ls(f'{rig_mesh}.vtx[*]', fl=1)
    if joints == []:
        _joints = cmds.ls(sl=1, type='joint')
    else:
        _joints = joints
    for vtx in vers:
        index = int(vtx.split('[')[-1].split(']')[0])
        value = 0
        for jnt in _joints:
            value = value + cmds.skinPercent(skin, vtx, transform=jnt, q=1)
        cmds.setAttr(f'{blendshape}.it[0].bw[{index}]', 1-value)
    return

def setup_RTRIG():
    main_dict = {'Root_M': 'stella_rig:body_M_FKCTRL', 'env_dummy': 'stella_rig:worldoffset_02_M_CTRL'}    
    dict = {'Spine1_M': 'stella_rig:spine_00_M_FKCTRL', 
        'Spine2_M': 'stella_rig:spine_01_M_FKCTRL', 'Spine3_M': 'stella_rig:spine_02_M_FKCTRL', 'Breast1_R': 'stella_rig:breast_R_FKCTRL', 
        'Breast1_L': 'stella_rig:breast_L_FKCTRL', 'Chest_M': 'stella_rig:spine_03_M_FKCTRL', 'Neck_M': 'stella_rig:neck_00_M_FKCTRL', 
        'NeckPart1_M': 'stella_rig:neck_01_M_FKCTRL', 'NeckPart2_M': 'stella_rig:neck_02_M_FKCTRL', 'Head_M': 'stella_rig:head_M_FKCTRL', 
        'Scapula_L': 'stella_rig:clavicle_FK_L_FKCTRL', 'Shoulder_L': 'stella_rig:arm_shldr_L_FKCTRL', 'Elbow_L': 'stella_rig:arm_elbow_L_FKCTRL', 
        'Wrist_L': 'stella_rig:arm_wrist_L_FKCTRL', 'IndexFinger0_L': 'stella_rig:hand_index_00_L_FKCTRL', 'IndexFinger1_L': 'stella_rig:hand_index_01_L_FKCTRL', 
        'IndexFinger2_L': 'stella_rig:hand_index_02_L_FKCTRL', 'IndexFinger3_L': 'stella_rig:hand_index_03_L_FKCTRL', 
        'MiddleFinger0_L': 'stella_rig:hand_middle_00_L_FKCTRL', 'MiddleFinger1_L': 'stella_rig:hand_middle_01_L_FKCTRL', 
        'MiddleFinger2_L': 'stella_rig:hand_middle_02_L_FKCTRL', 'MiddleFinger3_L': 'stella_rig:hand_middle_03_L_FKCTRL', 
        'RingFinger0_L': 'stella_rig:hand_ring_00_L_FKCTRL', 'RingFinger1_L': 'stella_rig:hand_ring_01_L_FKCTRL', 'RingFinger2_L': 'stella_rig:hand_ring_02_L_FKCTRL', 
        'RingFinger3_L': 'stella_rig:hand_ring_03_L_FKCTRL', 'PinkyFinger0_L': 'stella_rig:hand_pinky_00_L_FKCTRL', 'PinkyFinger1_L': 'stella_rig:hand_pinky_01_L_FKCTRL', 
        'PinkyFinger2_L': 'stella_rig:hand_pinky_02_L_FKCTRL', 'PinkyFinger3_L': 'stella_rig:hand_pinky_03_L_FKCTRL', 
        'ThumbFinger1_L': 'stella_rig:hand_thumb_00_L_FKCTRL', 'ThumbFinger2_L': 'stella_rig:hand_thumb_01_L_FKCTRL', 'ThumbFinger3_L': 'stella_rig:hand_thumb_02_L_FKCTRL',
        'Hip_L': 'stella_rig:leg_hip_L_FKCTRL', 'Knee_L': 'stella_rig:leg_knee_L_FKCTRL', 'Ankle_L': 'stella_rig:leg_ankle_L_FKCTRL', 'Toes_L': 'stella_rig:foot_ball_L_FKCTRL'}
        
    for jnt in dict:
        cmds.orientConstraint(jnt, dict[jnt], mo=True)
        if '_L' in jnt:
            cmds.orientConstraint(jnt.replace('_L','_R'), dict[jnt].replace('_L','_R'), mo=True)
    for jnt in main_dict:
        cmds.parentConstraint(jnt, main_dict[jnt], mo=True)

def connect_deform_skeleton(bind_root = 'worldOffset_M_JNT', proxy_root = 'deform_skeleton', constraint=0, exclude=[]):
    """Constraint: 0 parentConstraint
                   1 orientConstraint"""    
    bind_list = []
    proxy_list = []
    cmds.select(bind_root, hierarchy=True, replace=True)
    for jnt in cmds.ls(sl=1):
        if cmds.objectType(jnt)=='joint' and jnt not in exclude:
            bind_list.append(jnt)

    cmds.select(proxy_root, hierarchy=True, replace=True)        
    for jnt in cmds.ls(sl=1):
        if cmds.objectType(jnt)=='joint' and jnt not in exclude:
            proxy_list.append(jnt)

    for jnt_p in proxy_list:

        t_p = cmds.xform(jnt_p, q=1, ws=1, t=1)
        dist = None
        for jnt_b in bind_list:

            t_b = cmds.xform(jnt_b, q=1, ws=1, t=1)
            temp_dist = (t_p[0]-t_b[0])**2 + (t_p[1]-t_b[1])**2 + (t_p[2]-t_b[2])**2
            if dist == None:           
                dist = temp_dist
                closest_jnt = jnt_b
            elif temp_dist < dist:
                dist = temp_dist
                closest_jnt = jnt_b

        if constraint == 0:
            cmds.parentConstraint(closest_jnt, jnt_p, maintainOffset=True)
        elif constraint==1:
            cmds.orientConstraint(closest_jnt, jnt_p, maintainOffset=True)

def setup_driven_attrs(driver, driven, minValue=None, maxValue=None, defaultValue=None):
    driven_obj, driven_attr = driven.split('.')
    if not cmds.objExists(driven):
        cmds.addAttr(driven_obj, 
                     ln=driven_attr, 
                     attributeType='float', 
                     minValue=-1.0, 
                     maxValue=1.0, 
                     defaultValue=0.0, 
                     keyable=True)
    if minValue!=None:
        cmds.setDrivenKeyframe(driven_obj, attribute=driven_attr,
                            currentDriver=driver,
                            driverValue=minValue,
                            value=-1.0,
                            )
    if defaultValue!=None:
        cmds.setDrivenKeyframe(driven_obj, attribute=driven_attr,
                            currentDriver=driver,
                            driverValue=defaultValue,
                            value=0.0,
                            )
    if maxValue!=None:
        cmds.setDrivenKeyframe(driven_obj, attribute=driven_attr,
                            currentDriver=driver,
                            driverValue=maxValue,
                            value=1.0,
                            )
    return





        