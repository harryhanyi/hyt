# C:\Program Files\Autodesk\Maya2019\plug-ins\camd\scripts has all the mel script of pose editor
# This module will wrap all mel commands

import maya.cmds as cmds
import maya.mel as mel

def melArray(input_list):
    mel_array = '{'
    for i in range(len(input_list)):
        if type(input_list[i]) == str:
            item = f'"{input_list[i]}"'
        elif type(input_list[i]) == int:
            item = f'{input_list[i]}'

        if i == 0:
            mel_array = mel_array + item
        else:
            mel_array = mel_array + ',' + item
    mel_array = mel_array +'}'

    return mel_array
    



def createNeutralPoses(nodeName):
    result = mel.eval(f'createNeutralPoses "{nodeName}";')
    return result

def createPoseInterpolatorNode(nodeName, flagCreateNeutralPose, flagDriverTwistAxis):
    # Select the driver and run the func
    tpl = mel.eval(f'createPoseInterpolatorNode "{nodeName}" {flagCreateNeutralPose} {flagDriverTwistAxis};')
    return tpl

def deletePoseInterpolatorNode(tpl):
    result = mel.eval(f'deletePoseInterpolatorNode "{tpl}";')
    return result

def invertShapeInitStrings():
    mel.eval('invertShapeInitStrings;')
    return

def isPoseInterpolator(nodeName):
    result = mel.eval(f'isPoseInterpolator "{nodeName}";')
    return result

def listPoseInterpolators():
    tpls = mel.eval('listPoseInterpolators;')
    return tpls

def poseInterpolatorAddPose(tpl, poseName):
    poseIndex = mel.eval(f'poseInterpolatorAddPose "{tpl}" "{poseName}";')
    return poseIndex

def poseInterpolatorAddShapePose(tpl, poseName, poseType, blendShapes, startEdit):
    mel_array = melArray(blendShapes)
    poseIndex = mel.eval(f'poseInterpolatorAddShapePose "{tpl}" "{poseName}" "{poseType}" {mel_array} {startEdit};')
    return poseIndex

def poseInterpolatorCalcKernelFalloff(tpl, poseName):
    result = mel.eval(f'poseInterpolatorCalcKernelFalloff "{tpl}" "{poseName}";')
    return result

def poseInterpolatorConnectedShapeDeformers(tpl):
    result = mel.eval(f'poseInterpolatorConnectedShapeDeformers "{tpl}";')
    return result

def poseInterpolatorDeletePose(tpl, poseName):
    result = mel.eval(f'poseInterpolatorDeletePose "{tpl}" "{poseName}";')
    return result

def poseInterpolatorDriverIndex(tpl, driverName):
    result = mel.eval(f'poseInterpolatorDriverIndex "{tpl}" "{driverName}";')
    return result

def poseInterpolatorDriverName(tpl, index):
    result = mel.eval(f'poseInterpolatorDriverName "{tpl}" {index};')
    return result

def poseInterpolatorDrivers(tpl):
    result = mel.eval(f'poseInterpolatorDrivers "{tpl}";')
    return result

def poseInterpolatorExport(filePath, tpls, shape):
    mel_array = melArray(tpls)
    result = mel.eval(f'poseInterpolatorExport "{filePath}" {mel_array} {shape};')
    return result

def poseInterpolatorExportAllNodes():
    result = mel.eval('poseInterpolatorExportAllNodes;')
    return result

def poseInterpolatorExportPoses(filePath, tpls, poses, shape):
    tpls_array = melArray(tpls)
    poses_array = melArray(poses)
    result = mel.eval(f'poseInterpolatorExportPoses "{filePath}" {tpls_array} {poses_array} {shape};')
    return result

def poseInterpolatorExportSelectedNodes():
    result = mel.eval('poseInterpolatorExportSelectedNodes;')
    return result

def poseInterpolatorExportSelectedPoses():
    result = mel.eval('poseInterpolatorExportSelectedPoses;')
    return result

def poseInterpolatorGoToPose(tpl, poseName):
    mel.eval(f'poseInterpolatorGoToPose "{tpl}" "{poseName}";')
    return

def poseInterpolatorImportNodes():
    result = mel.eval('poseInterpolatorImportNodes;')
    return result

def poseInterpolatorImportPoses(filePath, shape):
    result = mel.eval(f'poseInterpolatorImportPoses "{filePath}" {shape};')
    return result

def poseInterpolatorInitStrings():
    mel.eval('poseInterpolatorInitStrings;')
    return

def poseInterpolatorMirror(tpl, poses, searchFor, replaceWith, shape, symmetryAxis, storeSymmetryEdge):
    poses_array = melArray(poses)
    result = mel.eval(f'poseInterpolatorMirror "{tpl}" {poses_array} "{searchFor}" "{replaceWith}" {shape} {symmetryAxis} {storeSymmetryEdge};')
    return result

def poseInterpolatorNodeType():
    result = mel.eval('poseInterpolatorNodeType;')
    return result

def poseInterpolatorPoseDefaultName(tpl):
    result = mel.eval(f'poseInterpolatorPoseDefaultName "{tpl}";')
    return result

def poseInterpolatorPoseIndex(tpl, poseName):
    result = mel.eval(f'poseInterpolatorPoseIndex "{tpl}" "{poseName}";')
    return result

def poseInterpolatorPoseIndices(tpl):
    result = mel.eval(f'poseInterpolatorPoseIndices "{tpl}";')
    return result

def poseInterpolatorPoseName(tpl, index):
    result = mel.eval(f'poseInterpolatorPoseName "{tpl}" {index};')
    return result

def poseInterpolatorPoseNames(tpl):
    result = mel.eval(f'poseInterpolatorPoseNames "{tpl}";')
    return result

def poseInterpolatorRenamePose(tpl, poseOldName, poseNewName):
    mel.eval(f'poseInterpolatorRenamePose "{tpl}" "{poseOldName}" "{poseNewName}";')
    return

def poseInterpolatorSetPoseType(tpl, poseName, poseType):
    mel.eval(f'poseInterpolatorSetPoseType "{tpl}" "{poseName}" "{poseType}";')
    return

def poseInterpolatorSetup():
    mel.eval('poseInterpolatorSetup;')
    return

def poseInterpolatorShape(nodeName):
    result = mel.eval(f'poseInterpolatorShape "{nodeName}";')
    return result

def poseInterpolatorTransform(nodeName):
    result = mel.eval(f'poseInterpolatorTransform "{nodeName}";')
    return result

def poseInterpolatorUpdatePose(tpl, poseName):
    mel.eval(f'poseInterpolatorUpdatePose "{tpl}" "{poseName}";')
    return






