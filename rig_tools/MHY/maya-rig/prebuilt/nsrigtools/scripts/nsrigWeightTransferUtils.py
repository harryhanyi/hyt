import maya.cmds as cmds

PLUGIN_NAME = 'nsrigTransferTools'
NODE_TYPE_NAME = 'nsrigWeightTransfer'


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def makeTransfer(
    srcMesh,
    tgtMesh,
    srcNode,
    tgtNode,
    srcWeightAttr,
    tgtWeightAttr,
    bindSpace,
    srcUVSet='map1',
    tgtUVSet='map1',
    bindDist=-1,
):
    loadPlugin()

    if isinstance(srcWeightAttr, str):
        srcWeightAttr = [srcWeightAttr]

    if isinstance(tgtWeightAttr, str):
        tgtWeightAttr = [tgtWeightAttr]

    assert len(srcWeightAttr) == len(
        tgtWeightAttr
    ), "Length of srcWeightAttr isn't match the length of tgtWeightAttr."

    node = cmds.createNode(NODE_TYPE_NAME)

    cmds.connectAttr('%s.outMesh' % srcMesh, '%s.sourceGeometry' % node)
    cmds.connectAttr('%s.outMesh' % tgtMesh, '%s.targetGeometry' % node)

    for i, attrPair in enumerate(zip(srcWeightAttr, tgtWeightAttr)):
        srcAttr = attrPair[0]
        tgtAttr = attrPair[1]
        cmds.connectAttr(
            '%s.%s' % (srcNode, srcAttr),
            '%s.sourceDataGroup[%d].sourceWeights' % (node, i),
        )
        cmds.connectAttr(
            '%s.outputDataGroup[%d].outputWeights' % (node, i),
            '%s.%s' % (tgtNode, tgtAttr),
        )

    cmds.setAttr('%s.sourceUVSet' % node, srcUVSet, type='string')
    cmds.setAttr('%s.targetUVSet' % node, tgtUVSet, type='string')
    cmds.setAttr('%s.bindDistance' % node, bindDist)
    cmds.setAttr('%s.bindSpace' % node, bindSpace)

    return node


def makeSkinClusterTransfer(
    srcMesh,
    srcSkinnedMesh,
    tgtMesh,
    srcNode,
    tgtNode,
    bindSpace,
    srcUVSet='map1',
    tgtUVSet='map1',
    bindDist=-1,
):
    loadPlugin()

    node = cmds.createNode(NODE_TYPE_NAME)

    cmds.connectAttr('%s.outMesh' % srcMesh, '%s.sourceGeometry' % node)
    cmds.connectAttr('%s.outMesh' % srcSkinnedMesh, '%s.sourceSkinnedGeometry' % node)
    cmds.connectAttr('%s.outMesh' % tgtMesh, '%s.targetGeometry' % node)

    cmds.connectAttr('%s.weightList' % srcNode, '%s.sourceWeightList' % node)
    cmds.connectAttr('%s.outputWeightList' % node, '%s.weightList' % tgtNode)

    cmds.setAttr('%s.sourceUVSet' % node, srcUVSet, type='string')
    cmds.setAttr('%s.targetUVSet' % node, tgtUVSet, type='string')
    cmds.setAttr('%s.bindDistance' % node, bindDist)
    cmds.setAttr('%s.bindSpace' % node, bindSpace)

    return node
