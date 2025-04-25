import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

PLUGIN_NAME = 'nsrigTransferTools'
NODE_TYPE_NAME = 'nsrigDeltaTransfer'


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


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


def duplicate(geom, subfix=''):
    shapePath = getShapePath(geom)
    fnDag = om2.MFnDagNode(shapePath)
    dupObj = fnDag.duplicate()
    dupGeom = om2.MFnDagNode(dupObj).partialPathName()
    dupGeom = cmds.rename(dupGeom, geom + subfix)
    dupGeomPaths = dupGeom.split('|')

    dupGeomShape = cmds.listRelatives(dupGeom, s=1, pa=1)[0]
    dupGeomShape = cmds.rename(dupGeomShape, dupGeomPaths[-1] + 'Shape')

    return dupGeom, dupGeomShape


def makeTransfer(
    srcMesh,
    tgtMesh,
    srcBS,
    tgtBS,
    srcShapeID,
    bindSpace,
    srcUVSet='map1',
    tgtUVSet='map1',
    bindDist=-1,
):
    loadPlugin()

    if isinstance(srcShapeID, int):
        if srcShapeID == -1:
            srcShapeID = cmds.getAttr('%s.weight' % srcBS, mi=1)
        else:
            srcShapeID = [srcShapeID]

    assert isinstance(srcShapeID, list) and len(srcShapeID) > 0, 'srcShapeID is empty.'

    node = cmds.createNode(NODE_TYPE_NAME)

    cmds.connectAttr('%s.outMesh' % srcMesh, '%s.sourceGeometry' % node)
    cmds.connectAttr('%s.outMesh' % tgtMesh, '%s.targetGeometry' % node)

    dataGrpID = 0
    for id in srcShapeID:
        shapeItemRootAttr = 'inputTarget[0].inputTargetGroup[%d].inputTargetItem' % id

        srcShapeItemRootAttr = '.'.join([srcBS, shapeItemRootAttr])
        srcItemIDs = cmds.getAttr(srcShapeItemRootAttr, mi=1)

        for itemID in srcItemIDs:
            shapeItemAttr = '%s[%d]' % (shapeItemRootAttr, itemID)
            srcDataGrpAttr = 'sourceDataGroup[%d]' % dataGrpID

            # make source blendShape connects to transfer node
            srcAttr = '.'.join([srcBS, shapeItemAttr, 'inputPointsTarget'])
            tgtAttr = '.'.join([node, srcDataGrpAttr, 'sourceDeltaPoints'])

            cmds.connectAttr(srcAttr, tgtAttr, f=1)

            srcAttr = '.'.join([srcBS, shapeItemAttr, 'inputComponentsTarget'])
            tgtAttr = '.'.join([node, srcDataGrpAttr, 'sourceDeltaComponents'])

            cmds.connectAttr(srcAttr, tgtAttr, f=1)

            # make transfer node connects to target blendShape
            outDataGrpAttr = 'outputDataGroup[%d]' % dataGrpID
            srcAttr = '.'.join([node, outDataGrpAttr, 'outputDeltaPoints'])
            tgtAttr = '.'.join([tgtBS, shapeItemAttr, 'inputPointsTarget'])

            cmds.connectAttr(srcAttr, tgtAttr, f=1)

            srcAttr = '.'.join([node, outDataGrpAttr, 'outputDeltaComponents'])
            tgtAttr = '.'.join([tgtBS, shapeItemAttr, 'inputComponentsTarget'])

            cmds.connectAttr(srcAttr, tgtAttr, f=1)

            dataGrpID += 1

        # make source blendShape connects to target blendShape
        srcAttr = '%s.weight[%d]' % (srcBS, id)
        tgtAttr = '%s.weight[%d]' % (tgtBS, id)

        cmds.connectAttr(srcAttr, tgtAttr, f=1)

    cmds.setAttr('%s.sourceUVSet' % node, srcUVSet, type='string')
    cmds.setAttr('%s.targetUVSet' % node, tgtUVSet, type='string')
    cmds.setAttr('%s.bindDistance' % node, bindDist)
    cmds.setAttr('%s.bindSpace' % node, bindSpace)

    return node


def extractShapes(node):
    retShapes = {}

    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)

    srcDataGrpPlug = fnNode.findPlug('sourceDataGroup', False)
    outDataGrpPlug = fnNode.findPlug('outputDataGroup', False)

    dataGrpIDs = srcDataGrpPlug.getExistingArrayAttributeIndices()

    for gi in dataGrpIDs:
        srcDataGrpElemPlug = srcDataGrpPlug.elementByLogicalIndex(gi)
        srcDeltaPointsPlug = srcDataGrpElemPlug.child(0)  # sourceDeltaPoints

        # find target shape name from source connections
        srcPlug = srcDeltaPointsPlug.source()  # source blendShape's inputPointsTarget
        if srcPlug.isNull:
            continue

        itemID = srcPlug.parent().logicalIndex()  # inputTargetItem index
        tgtGrpID = (
            srcPlug.parent().array().parent().logicalIndex()
        )  # inputTargetGroup index

        w = (itemID - 5000) / 1000.0

        srcBSNode = srcPlug.node()
        fnBSNode = om2.MFnDependencyNode(srcBSNode)

        srcWeightAlias = (
            fnBSNode.findPlug('weight', False)
            .elementByLogicalIndex(tgtGrpID)
            .partialName(useAlias=True)
        )

        newShapeName = srcWeightAlias
        if w != 1.0:
            subfix = str(round(w * 100))
            newShapeName = '_'.join([newShapeName, subfix])
        # print('  exacted shape name: %s' % newShapeName)

        # get output delta points and components plugs
        outDataGrpElemPlug = outDataGrpPlug.elementByLogicalIndex(gi)
        outDeltaPointsPlug = outDataGrpElemPlug.child(0)  # outputDeltaPoints
        outDeltaCompPlug = outDataGrpElemPlug.child(2)  # outputDeltaPoints

        if not outDeltaPointsPlug.isSource:
            continue

        dstPlugs = outDeltaPointsPlug.destinations()
        tgtBSNode = dstPlugs[0].node()

        # get original shape from destinate blendShape and make a clean duplication
        fnBSNode = oma2.MFnGeometryFilter(tgtBSNode)
        inShapeObj = fnBSNode.inputShapeAtIndex(0)
        inShapePath = om2.MFnDagNode(inShapeObj)

        dupGeom, dupGeomShape = duplicate(inShapePath.partialPathName())
        cmds.setAttr('%s.intermediateObject' % dupGeomShape, 0)
        dupGeom = cmds.rename(dupGeom, newShapeName)

        # get output delta points and components data
        fnPointArray = om2.MFnPointArrayData(outDeltaPointsPlug.asMObject())
        deltaPoints = fnPointArray.array()
        # print( deltaPoints)

        fnCompList = om2.MFnComponentListData(outDeltaCompPlug.asMObject())
        fnComp = om2.MFnSingleIndexedComponent(fnCompList.get(0))
        compIDs = fnComp.getElements()
        # print('target components:', compIDs)

        # apply output delta points to duplicated shape
        dupGeomShapePath = getShapePath(dupGeom)
        fnMesh = om2.MFnMesh(dupGeomShapePath)
        newPoints = fnMesh.getPoints()

        for id, dt in zip(compIDs, deltaPoints):
            newPoints[id] += dt

        fnMesh.setPoints(newPoints)

        retShapes[dupGeom] = {}
        retShapes[dupGeom]['index'] = tgtGrpID
        retShapes[dupGeom]['weight'] = w

    return retShapes


if __name__ == '__main__':
    srcMesh = 'pSphere1Ref'
    tgtMesh = 'highres_sphereRef'
    srcBsNode = 'blendShape1'
    tgtBsNode = 'blendShape2'
    tgtIds = cmds.getAttr('%s.weight' % srcBsNode, mi=1)
    shapeID = -1

    # dtxfNode = makeTransfer(srcMesh, tgtMesh, srcBsNode, tgtBsNode, shapeID, 0)
    # newShapes = extractShapes('nsrigDeltaTransfer1')
    # print(newShapes)
