import json

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

PLUGIN_NAME = 'nsrigWrap'
NODE_TYPE_NAME = 'nsrigWrap'

DEFAULT_SETTINGS = {
    'envelope': 1.0,
    'bindState': 0,
    'bindMode': 0,
    'bindSpace': 0,
    'wrapMode': 0,
    'bindDistance': -1.0,
    'bindOffset': 1.0,
    'setWorldPoints': False,
    'maxDrivers': 1,
    'falloff': 0.0,
    'falloffScale': 1.0,
}

WEIGHT_ATTRS = {
    'weightList': ['weights'],
    'userWeightList': ['bindOffsetWeights', 'falloffWeights', 'falloffScaleWeights'],
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


def geometryShapeAttrName(geom, worldSpace=False):
    geomShape = getShapePath(geom)

    name = ''
    geomType = geomShape.apiType()
    if geomType == om2.MFn.kMesh:
        name = 'worldMesh' if worldSpace else 'outMesh'
    elif geomType == om2.MFn.kNurbsSurface:
        name = 'worldSpace' if worldSpace else 'local'
    elif geomType == om2.MFn.kNurbsCurve:
        name = 'worldSpace' if worldSpace else 'local'
    elif geomType == om2.MFn.kLattice:
        name = 'worldLattice' if worldSpace else 'latticeOutput'
    else:
        raise TypeError('Unsupported geometry type.')

    return name


def duplicate(geom, subfix=''):
    shapePath = getShapePath(geom)
    fnDag = om2.MFnDagNode(shapePath)
    dupObj = fnDag.duplicate()
    dupGeom = om2.MFnDagNode(dupObj).partialPathName()
    dupGeom = cmds.rename(dupGeom, geom + subfix)
    dupGeomShape = cmds.listRelatives(dupGeom, s=1)[0]
    dupGeomShape = cmds.rename(dupGeomShape, dupGeom + 'Shape')

    return dupGeom, dupGeomShape


def create(
    geoms, bindGeoms=None, createBindGeoms=True, name='', worldSpace=False, **kwargs
):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not geoms:
        raise RuntimeError('%s: Please provide some geometries.' % NODE_TYPE_NAME)

    node = cmds.deformer(geoms, typ=NODE_TYPE_NAME, n=name, **kwargs)[0]

    if bindGeoms:  # Make provided bind geometry connected
        for i, geom in enumerate(bindGeoms):
            try:
                srcAttr = geometryShapeAttrName(geom, worldSpace)

                geomShape = cmds.listRelatives(geom, s=1)[0]
                cmds.connectAttr(
                    '%s.%s' % (geomShape, srcAttr), '%s.bindGeometry[%d]' % (node, i)
                )
            except:
                pass
    elif (
        createBindGeoms
    ):  # Make a duplication from current geometry to define bind geometry
        for i, geom in enumerate(geoms):
            try:
                srcAttr = geometryShapeAttrName(geom, worldSpace)

                bindGeom, bindGeomShape = duplicate(geom, 'Bind')

                cmds.connectAttr(
                    '%s.%s' % (bindGeomShape, srcAttr),
                    '%s.bindGeometry[%d]' % (node, i),
                )

                cmds.hide(bindGeom)
            except:
                pass

    return node


def createBySelection(name='', createBindGeoms=True, worldSpace=False, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select some geometries.' % NODE_TYPE_NAME)

    return create(sels, None, createBindGeoms, name, worldSpace, **kwargs)


def addDriver(node, mesh, bindMesh=None, createBindMesh=True, worldSpace=True):
    if isinstance(mesh, str):
        mesh = [mesh]

    ids = cmds.getAttr('%s.driver' % node, mi=1)
    nextId = 0 if not ids else ids[-1] + 1

    mtxAttr = 'worldMatrix' if worldSpace else 'matrix'
    for i, m in enumerate(mesh):
        cmds.connectAttr(
            '%s.outMesh' % m, '%s.driver[%d].driverGeometry' % (node, nextId + i)
        )

        cmds.connectAttr(
            '%s.%s' % (m, mtxAttr), '%s.driver[%d].driverMatrix' % (node, nextId + i)
        )

    meshAttr = 'worldMesh' if worldSpace else 'outMesh'
    if bindMesh:
        if isinstance(bindMesh, str):
            bindMesh = [bindMesh]

        for i, m in enumerate(bindMesh):
            cmds.connectAttr(
                '%s.%s' % (m, meshAttr),
                '%s.driver[%d].driverBindGeometry' % (node, nextId + i),
            )
    elif createBindMesh:
        for i, m in enumerate(mesh):
            bindMesh, bindMeshShape = duplicate(m, 'Bind')

            cmds.connectAttr(
                '%s.%s' % (bindMeshShape, meshAttr),
                '%s.driver[%d].driverBindGeometry' % (node, nextId + i),
            )

            cmds.hide(bindMesh)


def removeDriver(node, driverID):
    if isinstance(driverID, int):
        driverID = list(driverID)

    for id in driverID:
        cmds.removeMultiInstance('%s.driver[%d]' % (node, id), b=1)


def wrapToLastSelectedMesh(name='', createBindGeoms=True, worldSpace=True, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels or len(sels) < 2:
        raise RuntimeError(
            '%s: Please select at least one geometries, following up driver mesh.'
            % NODE_TYPE_NAME
        )

    node = create(sels[0:-1], None, createBindGeoms, name, worldSpace, **kwargs)
    addDriver(node, sels[-1], None, createBindGeoms, worldSpace)

    return node


def wrapFirstSelectedGeomToDrivers(
    name='', createBindGeoms=True, worldSpace=True, **kwargs
):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels or len(sels) < 2:
        raise RuntimeError(
            '%s: Please select one geometry, following up driver meshes.'
            % NODE_TYPE_NAME
        )

    node = create(sels[0], None, createBindGeoms, name, worldSpace, **kwargs)

    numDrivers = len(sels) - 1
    for i in range(numDrivers):
        addDriver(node, sels[i + 1], None, createBindGeoms, worldSpace)

    cmds.setAttr('%s.maxDrivers' % node, numDrivers)

    return node


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

    data = {}

    inGeoms = fnFilter.getInputGeometry()
    for i, geomObj in enumerate(inGeoms):
        if geomObj.isNull():
            continue

        geomIter = om2.MItGeometry(geomObj)
        numVerts = geomIter.count()

        data[i] = {}
        for pa, attrs in WEIGHT_ATTRS.items():
            if not pa in data[i]:
                data[i][pa] = {}

            for a in attrs:
                data[i][pa][a] = getAttrWeights(node, a, numVerts, pa, i)

    if outfile:
        with open(outfile, 'w') as outfile:
            json.dump(data, outfile, indent=2)

    return data


def importWeights(node, data=None, infile=None):
    if data:
        assert type(data) is dict, "'data' must be a dict."
        for i, currweights in data.items():
            for pa, attrweights in currweights.items():
                for a, weights in attrweights.items():
                    setAttrWeights(node, a, weights, pa, i)
        return

    if infile:
        f = open(infile)
        data = json.load(f)
        for i, currweights in data.items():
            for pa, attrweights in currweights.items():
                for a, weights in attrweights.items():
                    setAttrWeights(node, a, weights, pa, int(i))


def getWeightPlugs(node=None):
    if not node:
        return []

    ids = cmds.getAttr('%s.input' % node, mi=1)
    if not ids:
        return []

    plugs = []
    for rootattr, childattrs in WEIGHT_ATTRS.items():
        for attr in childattrs:
            for id in ids:
                attrname = '%s[%d].%s' % (rootattr, id, attr)
                plugs.append(attrname)

    return plugs
