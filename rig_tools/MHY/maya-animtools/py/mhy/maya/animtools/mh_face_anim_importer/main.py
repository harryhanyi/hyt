import os, sys
import maya.cmds as cmds
import imp

def mgApplyFaceMocap():
    # Get namespace of the referenced rig
    referenced_rigs = []
    all_nodes = cmds.ls()

    for node in all_nodes:
        # Check if the node is part of a reference
        if cmds.referenceQuery(node, isNodeReferenced=True):
            reference_file = cmds.referenceQuery(node, filename=True)
            namespace = cmds.referenceQuery(node, namespace=True)
            if (reference_file, namespace) not in referenced_rigs:
                referenced_rigs.append((reference_file, namespace))

    namespace = ''
    if len(referenced_rigs) > 0:
        namespace = referenced_rigs[0][1] + ':'
    
    # Load animation json
    filePath = cmds.fileDialog2(fileMode=1, caption="Import Metahuman Face Animation")[0]
    anim_keys_file = imp.load_source('', filePath)
    anim_keys = anim_keys_file.anim_keys_dict
    
    for dict_key in anim_keys:
        keyframes_list = anim_keys[dict_key]
        ctrl = dict_key
        attr = 'translateY'
        if '.' in ctrl:
            ctrl_string_list = ctrl.split('.')
            ctrl = ctrl_string_list[0]
            if len(ctrl_string_list)>2:
                attr = ctrl_string_list[1].replace('Location', 'translate').replace('Rotation', 'rotate').replace('Scale', 'scale') + ctrl_string_list[-1].upper()
            else:
                attr = 'translate' + ctrl_string_list[-1].upper()

        # check for numbers at the end of cntrl name
        
        ctrl_name = ctrl
        if ctrl_name.split('_')[-1].isdigit():
            ctrl_name = ctrl_name.replace('_' + ctrl_name.split('_')[-1], '')
        ctrl_name = namespace + ctrl_name

        if cmds.objExists(ctrl_name):
            for key_num in range(0,len(keyframes_list)):
                key_val = keyframes_list[key_num]
                cmds.setKeyframe(ctrl_name, attribute=attr, v = key_val[0], t=key_val[1] )
        else:
            print('Skipping ' + ctrl_name + ' as no such object exists.')
            
    print('Applied Animation to Face Rig.')

