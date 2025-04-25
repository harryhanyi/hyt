import maya.cmds as cmds

joint_list = [['Shoulder_L', 'Elbow_L'], ['Hip_L','Knee_L']]



def fix_rotation(root_jnt, mid_jnt, start_frame, end_frame):
    # Get end_jnt
    end_jnt = cmds.listRelatives(mid_jnt, children=True)[0]
    # Create Locators
    root_loc_shape = cmds.createNode('locator')
    mid_loc_shape = cmds.createNode('locator')
    mid_vec_shape = cmds.createNode('locator')
    end_loc_shape = cmds.createNode('locator')
    root_loc = cmds.listRelatives(root_loc_shape, parent=True)[0]
    mid_loc = cmds.listRelatives(mid_loc_shape, parent=True)[0]
    mid_vec = cmds.listRelatives(mid_vec_shape, parent=True)[0]
    end_loc = cmds.listRelatives(end_loc_shape, parent=True)[0]
    cmds.parent(mid_vec, mid_loc)
    # Setup pole vector
    dist = cmds.createNode('distanceBetween')
    cmds.connectAttr(f"{root_loc}.worldMatrix", f"{dist}.inMatrix1")
    cmds.connectAttr(f"{end_loc}.worldMatrix", f"{dist}.inMatrix2")
    length = abs(cmds.getAttr(f"{mid_jnt}.tx")) + abs(cmds.getAttr(f"{end_jnt}.tx"))
    cmds.setDrivenKeyframe(mid_vec, attribute='ty', currentDriver=f"{dist}.distance", driverValue=length*0.95, value=0)
    cmds.setDrivenKeyframe(mid_vec, attribute='ty', currentDriver=f"{dist}.distance", driverValue=length, value=5)
    # Bake forearm locator
    temp_cns_0 = cmds.parentConstraint(mid_jnt, mid_loc, maintainOffset=False)[0]
    temp_cns_1 = cmds.parentConstraint(end_jnt, end_loc, maintainOffset=False)[0]
    temp_cns_2 = cmds.parentConstraint(root_jnt, root_loc, maintainOffset=False)[0]
    bake_sim([mid_loc, end_loc, root_loc], start_frame, end_frame)
    cmds.delete(temp_cns_0, temp_cns_1, temp_cns_2)

    # Setup IK
    ik_handle = cmds.ikHandle(startJoint=root_jnt, endEffector=end_jnt, solver='ikRPsolver')[0]
    root_cns = cmds.pointConstraint(root_loc, root_jnt, maintainOffset=False)[0]
    end_cns = cmds.pointConstraint(end_loc, ik_handle, maintainOffset=False)[0]
    cmds.poleVectorConstraint(mid_vec, ik_handle)
    bake_sim([root_jnt, mid_jnt, end_jnt], start_frame, end_frame)
    cmds.delete(root_cns, root_loc, mid_loc, end_loc, ik_handle)

    return

def bake_sim(objects, start, end):
    cmds.bakeResults(objects, 
                     simulation=True, 
                     time=(start, end), 
                     sampleBy=1, 
                     disableImplicitControl=True, 
                     preserveOutsideKeys=False, 
                     sparseAnimCurveBake=False, 
                     at=["translateX", "translateY", "translateZ",
                         "rotateX", "rotateY", "rotateZ"])
    return

def run(mirror=True):
    # Get start and end of timeslider
    start = cmds.playbackOptions(query=True, minTime=True)
    end = cmds.playbackOptions(query=True, maxTime=True)
    for jnts in joint_list:
        fix_rotation(jnts[0], jnts[1], start, end)
    if mirror == True:
        for jnts in joint_list:
            fix_rotation(jnts[0].replace('_L','_R'), jnts[1].replace('_L','_R'), 
                         start, end)
    else:
        return
    return

