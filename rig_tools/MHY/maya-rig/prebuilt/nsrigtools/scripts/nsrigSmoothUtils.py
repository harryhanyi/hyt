import json

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

PLUGIN_NAME = 'nsrigSmooth'
NODE_TYPE_NAME = 'nsrigSmooth'

DEFAULT_SETTINGS = {
    'envelope': 1.0,
    'uvSet': 'map1',
    'weightingScheme': 0,
    'smoothingDirection': 0,
    'smoothingIterations': 10,
    'smoothing': 1.0,
    'uSmoothing': 0.0,
    'vSmoothing': 1.0,
    'surfaceSmoothing': 0.0,
    'surfaceConstraint': 0.0,
    'displacement': 1.0,
    'normalOffset': 0.0,
    'pinBorderVertices': 1.0,
    'targetProjection': 0.0,
    'targetSubdivLevel': 0,
}

WEIGHT_ATTRS = [
    'weights',
    'smoothingWeights',
    'uSmoothingWeights',
    'vSmoothingWeights',
    'surfaceSmoothingWeights',
    'surfaceConstraintWeights',
    'displacementWeights',
    'normalOffsetWeights',
    'targetProjectionWeights',
    'targetTangentFittingWeights',
    'targetBlendingWeights',
]


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


def create(mesh, refMesh=None, createRefMesh=True, name='', worldSpace=False, **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not mesh:
        raise RuntimeError('%s: Please provide one mesh.' % NODE_TYPE_NAME)

    node = cmds.deformer(mesh, typ=NODE_TYPE_NAME, n=name, **kwargs)[0]

    srcAttr = 'worldMesh' if worldSpace else 'outMesh'
    if refMesh:  # Make provided reference mesh connected
        cmds.connectAttr('%s.%s' % (refMesh, srcAttr), '%s.referenceGeometry' % node)
    else:
        if (
            createRefMesh
        ):  # Make a duplication from current mesh to define reference geometry
            meshShapePath = getShapePath(mesh)
            fnDag = om2.MFnDagNode(meshShapePath)
            dupObj = fnDag.duplicate()
            refMesh = om2.MFnDagNode(dupObj).partialPathName()
            refMesh = cmds.rename(refMesh, mesh + 'Ref')
            refMeshShape = cmds.listRelatives(refMesh, s=1)[0]
            cmds.rename(refMeshShape, refMesh + 'Shape')
            cmds.hide(refMesh)
            cmds.connectAttr(
                '%s.%s' % (refMesh, srcAttr), '%s.referenceGeometry' % node
            )

    return node


def createBySelection(createRefMesh=True, name='', worldSpace=False, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select some meshes.' % NODE_TYPE_NAME)

    nodes = []
    for sel in sels:
        n = create(sel, None, createRefMesh, name, worldSpace, **kwargs)
        nodes.append(n)

    return nodes


def applySettings(node, settings):
    assert type(settings) is dict, "'settings' should be an instance of dict."

    for attr, val in settings.items():
        nodeAttr = '%s.%s' % (node, attr)
        if type(val) == str:
            cmds.setAttr(nodeAttr, val, type='string')
        else:
            cmds.setAttr(nodeAttr, val)


def reset(node):
    applySettings(node, DEFAULT_SETTINGS)


def getAttrWeights(
    node, attr, numWeights, parentAttr=None, parentAttrIndex=-1, defaultVal=1.0
):
    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)
    attrPlug = fnNode.findPlug(attr, False)

    if parentAttr and parentAttrIndex >= 0:
        parentAttrPlug = fnNode.findPlug(parentAttr, False)
        attrPlug.selectAncestorLogicalIndex(parentAttrIndex, parentAttrPlug.attribute())

    weights = [defaultVal] * numWeights
    existingIDs = attrPlug.getExistingArrayAttributeIndices()
    for i in existingIDs:
        if i >= numWeights:
            break
        weights[i] = attrPlug.elementByLogicalIndex(i).asFloat()

    return weights


def setAttrWeights(node, attr, weights, parentAttr=None, parentAttrIndex=-1):
    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)
    attrPlug = fnNode.findPlug(attr, False)

    if parentAttr and parentAttrIndex >= 0:
        parentAttrPlug = fnNode.findPlug(parentAttr, False)
        attrPlug.selectAncestorLogicalIndex(parentAttrIndex, parentAttrPlug.attribute())

    for i, w in enumerate(weights):
        try:
            attrPlug.elementByLogicalIndex(i).setFloat(w)
        except:
            pass


def exportWeights(node, outfile=None):
    nodeObj = getDependencyNode(node)
    fnFilter = oma2.MFnGeometryFilter(nodeObj)

    meshObj = fnFilter.inputShapeAtIndex(0)
    fnMesh = om2.MFnMesh(meshObj)
    numVerts = fnMesh.numVertices

    data = {}
    for attr in WEIGHT_ATTRS:
        data[attr] = getAttrWeights(node, attr, numVerts)

    if outfile:
        with open(outfile, 'w') as outfile:
            json.dump(data, outfile, indent=2)

    return data


def importWeights(node, data=None, infile=None):
    if data:
        assert type(data) is dict, "'data' must be a dict."
        for attr, weights in data.items():
            setAttrWeights(node, attr, weights)
        return

    if infile:
        f = open(infile)
        data = json.load(f)
        for attr, weights in data.items():
            setAttrWeights(node, attr, weights)
