import maya.cmds as cmds
# Stella has a custom legecy skeleton, which should be constrained to binding skeleton
def connect_deform_skeleton(bind_root = 'worldOffset_M_JNT', proxy_root = 'deform_skeleton'):    
    bind_list = []
    proxy_list = []
    cmds.select(bind_root, hierarchy=True, replace=True)
    for jnt in cmds.ls(sl=1):
        if cmds.objectType(jnt)=='joint' and '_R_' not in jnt:
            bind_list.append(jnt)

    cmds.select(proxy_root, hierarchy=True, replace=True)        
    for jnt in cmds.ls(sl=1):
        if cmds.objectType(jnt)=='joint' and '_R' not in jnt:
            proxy_list.append(jnt)
    dist = {}        
    for jnt_p in proxy_list:

        t_p = cmds.xform(jnt_p, q=1, ws=1, t=1)
        for jnt_b in bind_list:

            t_b = cmds.xform(jnt_b, q=1, ws=1, t=1)
            dis = 0
            for i in range(0,3):
                dis = dis + abs(t_p[i]-t_b[i])
            if dis < 0.05:
                dist[jnt_p] = jnt_b
                cmds.parentConstraint(jnt_b, jnt_p, maintainOffset=True)
                if '_L' in jnt_p:
                    cmds.parentConstraint(jnt_b.replace('_L_','_R_'), jnt_p.replace('_L','_R'), maintainOffset=True)
        if jnt_p not in dist:
            print(f"{jnt_p} has not found binding root")

        

    
