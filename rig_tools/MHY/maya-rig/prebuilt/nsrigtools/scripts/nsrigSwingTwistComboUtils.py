import maya.cmds as cmds
import maya.api.OpenMaya as om2


PLUGIN_NAME = 'nsrigPsdNodes'
NODE_TYPE_NAME = 'nsrigSwingTwistCombo'

DEFAULT_SETTINGS = {
    'globalTwist': 0.0,
    'globalTwistPos': 0.0,
    'globalTwistNeg': 0.0,
}


def getDependencyNode(name):
    selList = om2.MSelectionList()

    try:
        selList.add(name)
        return selList.getDependNode(0)
    except:
        return None


def getDagPath(name):
    selList = om2.MSelectionList()

    try:
        selList.add(name)
        return selList.getDagPath(0)
    except:
        return None


def getShapePath(name):
    path = getDagPath(name)

    if path.apiType() == om2.MFn.kTransform:
        path.extendToShape()
    return path


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def deletePose(node, poseId):
    ids = cmds.getAttr('%s.pose' % node, mi=1)

    nodeAttrName = '%s.pose[%d]' % (node, poseId)
    if not poseId in ids:
        om2.MGlobal.displayError('%s is not existed.' % nodeAttrName)
        return

    cmds.setAttr('%s.poseDelete' % nodeAttrName, True)
    cmds.removeMultiInstance(nodeAttrName, b=1)
    cmds.removeMultiInstance('%s.outputPoseSwingWeights[%d]' % (node, poseId), b=1)
    cmds.removeMultiInstance('%s.outputPoseTwistPosWeights[%d]' % (node, poseId), b=1)
    cmds.removeMultiInstance('%s.outputPoseTwistNegWeights[%d]' % (node, poseId), b=1)
