import maya.cmds as cmds

total_match_dist = {'Hip_L':'leg_hip_L_RIGJNT', 'Knee_L':'leg_knee_L_RIGJNT',
    'Toes_L':'foot_ball_L_RIGJNT','ToesEnd_L':'foot_toe_L_RIGJNT','Wrist_L':'hand_L_RIGJNT', 
    'MiddleFinger0_L':'hand_middle_00_L_RIGJNT', 'MiddleFinger1_L':'hand_middle_01_L_RIGJNT', 
    'MiddleFinger2_L':'hand_middle_02_L_RIGJNT', 'MiddleFinger3_L':'hand_middle_03_L_RIGJNT', 
    'MiddleFinger4_L':'hand_middle_04_L_RIGJNT', 'ThumbFinger1_L':'hand_thumb_00_L_RIGJNT', 
    'ThumbFinger2_L':'hand_thumb_01_L_RIGJNT', 'ThumbFinger3_L':'hand_thumb_02_L_RIGJNT', 
    'ThumbFinger4_L':'hand_thumb_03_L_RIGJNT', 'IndexFinger0_L':'hand_index_00_L_RIGJNT', 
    'IndexFinger1_L':'hand_index_01_L_RIGJNT', 'IndexFinger2_L':'hand_index_02_L_RIGJNT', 
    'IndexFinger3_L':'hand_index_03_L_RIGJNT', 'IndexFinger4_L':'hand_index_04_L_RIGJNT', 
    'PinkyFinger0_L':'hand_pinky_00_L_RIGJNT', 'PinkyFinger1_L':'hand_pinky_01_L_RIGJNT', 
    'PinkyFinger2_L':'hand_pinky_02_L_RIGJNT', 'PinkyFinger3_L':'hand_pinky_03_L_RIGJNT', 
    'PinkyFinger4_L':'hand_pinky_04_L_RIGJNT', 'RingFinger0_L':'hand_ring_00_L_RIGJNT', 
    'RingFinger1_L':'hand_ring_01_L_RIGJNT', 'RingFinger2_L':'hand_ring_02_L_RIGJNT', 
    'RingFinger3_L':'hand_ring_03_L_RIGJNT', 'RingFinger4_L':'hand_ring_04_L_RIGJNT'}

pos_match_dist = {'ElbowPart1_L':'arm_elbowTwist_00_L_RIGJNT','ElbowPart2_L':'arm_elbowTwist_01_L_RIGJNT',
    'HipPart1_L':'leg_hipTwist_01_L_RIGJNT','HipPart2_L':'leg_hipTwist_02_L_RIGJNT',
    'KneePart1_L':'leg_kneeTwist_00_L_RIGJNT','KneePart2_L':'leg_kneeTwist_01_L_RIGJNT',
    'Ankle_L':'foot_ankle_L_RIGJNT'}
     
def total_match(s_jnt, mhy_jnt):
    parent_jnt = cmds.listRelatives(s_jnt, parent=True)[0]
    cmds.parent(s_jnt,mhy_jnt)
    temp_parent = cmds.listRelatives(s_jnt, parent=True)[0]
    if cmds.objectType(temp_parent) != 'joint':
        cmds.xform(temp_parent, t=[0,0,0],ro=[0,0,0])
    cmds.xform(s_jnt, t=[0,0,0],ro=[0,0,0])
    cmds.setAttr(f'{s_jnt}.jointOrientX',0)
    cmds.setAttr(f'{s_jnt}.jointOrientY',0)
    cmds.setAttr(f'{s_jnt}.jointOrientZ',180)
    cmds.parent(s_jnt, parent_jnt)
    if cmds.objectType(cmds.listRelatives(s_jnt, parent=True)[0]) != 'joint':
        return s_jnt
    return
    
def pos_match(s_jnt, mhy_jnt):
    cnt = cmds.pointConstraint(mhy_jnt, s_jnt, maintainOffset=False)[0]
    cmds.delete(cnt)
    return

stella_root = 'Root_M'    
cmds.select(stella_root, hierarchy=True)
s_jnt_list = cmds.ls(sl=1)
for s_jnt in s_jnt_list:
    if s_jnt in total_match_dist:
        mhy_jnt = total_match_dist[s_jnt]
        total_match(s_jnt, mhy_jnt)
        if '_L' in s_jnt:
            s_jnt_r = s_jnt.replace('_L', '_R')
            mhy_jnt_r = mhy_jnt.replace('_L_', '_R_')
            total_match(s_jnt_r, mhy_jnt_r)
    elif s_jnt in pos_match_dist:
        mhy_jnt = pos_match_dist[s_jnt]
        pos_match(s_jnt, pos_match_dist[s_jnt])
        if '_L' in s_jnt:
            s_jnt_r = s_jnt.replace('_L', '_R')
            mhy_jnt_r = mhy_jnt.replace('_L_', '_R_')
            pos_match(s_jnt_r, mhy_jnt_r)
        
        

