import json

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

PLUGIN_NAME = 'nsrigSticky'
NODE_TYPE_NAME = 'nsrigSticky'

DEFAULT_SETTINGS = {
    'envelope': 1.0,
    'mode': 0,
    'attach': 0,
    'attachFalloff': 0.5,
    'attachThreshold': 0,
    'detachFalloff': 0.2,
    'smoothingIterations': 0,
    'resetFrame': 0,
    'detachFrames': 5,
}

WEIGHT_ATTRS = [
    'weights',
    'smoothingWeights',
    'attachThresholdWeights',
    'stickyRegionAWeights',
    'stickyRegionBWeights',
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


def create(geom, refGeom=None, createRefGeom=True, name='', **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not geom:
        raise RuntimeError('%s: Please provide one mesh.' % NODE_TYPE_NAME)

    node = cmds.deformer(geom, typ=NODE_TYPE_NAME, n=name, **kwargs)[0]

    srcAttr = 'outMesh'

    if refGeom:  # Make provided reference geometry connected
        try:
            refGeomShape = cmds.listRelatives(refGeom, s=1)[0]
            cmds.connectAttr(
                '%s.%s' % (refGeomShape, srcAttr), '%s.referenceGeometry' % node
            )
        except:
            pass
    elif (
        createRefGeom
    ):  # Make a duplication from current geometry to define bind geometry
        try:
            refGeom, refGeomShape = duplicate(geom, 'Ref')

            cmds.connectAttr(
                '%s.%s' % (refGeomShape, srcAttr),
                '%s.referenceGeometry' % node,
            )

            cmds.hide(refGeom)
        except:
            pass

    return node


def createBySelection(name='', createRefGeom=True, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select one mesh.' % NODE_TYPE_NAME)

    return create(sels[0], None, createRefGeom, name, **kwargs)


def getAttrWeights(node, attr, numWeights, parentAttr=None, parentAttrIndex=-1):
    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)
    attrPlug = fnNode.findPlug(attr, False)

    if parentAttr and parentAttrIndex >= 0:
        parentAttrPlug = fnNode.findPlug(parentAttr, False)
        attrPlug.selectAncestorLogicalIndex(parentAttrIndex, parentAttrPlug.attribute())

    fnAttr = om2.MFnNumericAttribute(attrPlug.attribute())
    weights = [fnAttr.default] * numWeights

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
