import json

import maya.cmds as cmds
import maya.api.OpenMayaAnim as oma2

from nsrigCollisionCommon import *


PLUGIN_NAME = 'nsrigCollisionTools'
NODE_TYPE_NAME = 'nsrigMultiCollide'

DEFAULT_SETTINGS = {
    'envelope': 1.0,
    'iterations': 10,
    'smoothing': 0.5,
    'surfaceSmoothing': 0.0,
    'bendingResistance': 0.0,
    'volumePreservation': 0.0,
    'bulge': 0.0,
    'bulgeDistance': 1.0,
    'separationDistance': 0.0,
    'maxPenetrationDepth': 1.0,
}

WEIGHT_ATTRS = {
    'weightList': ['weights'],
    'userWeightList': [
        'smoothingWeights',
        'volumePreservationWeights',
        'separationWeights',
    ],
}


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def create(meshes, name='', **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not meshes:
        raise RuntimeError('%s: Please provide some meshes.' % NODE_TYPE_NAME)

    node = cmds.deformer(meshes, typ=NODE_TYPE_NAME, n=name, **kwargs)[0]

    return node


def createBySelection(name='', **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select some meshes.' % NODE_TYPE_NAME)

    return create(sels, name, **kwargs)


def addCollider(node, mesh, worldSpace=True):
    if isinstance(mesh, str):
        mesh = list(mesh)

    ids = cmds.getAttr('%s.collider' % node, mi=1)
    nextId = 0 if not ids else ids[-1] + 1

    srcAttr = 'worldMesh' if worldSpace else 'outMesh'
    for m in mesh:
        cmds.connectAttr(
            '%s.%s' % (m, srcAttr), '%s.collider[%d].colliderGeometry' % (node, nextId)
        )
        nextId += 1


def removeCollider(node, collideID):
    if isinstance(collideID, int):
        collideID = list(collideID)

    for id in collideID:
        cmds.removeMultiInstance('%s.collider[%d]' % (node, id), b=1)


def exportWeights(node, outfile=None):
    nodeObj = getDependencyNode(node)
    fnFilter = oma2.MFnGeometryFilter(nodeObj)

    data = {}

    inGeoms = fnFilter.getInputGeometry()
    for i, meshObj in enumerate(inGeoms):
        if meshObj.isNull():
            continue

        fnMesh = om2.MFnMesh(meshObj)
        numVerts = fnMesh.numVertices

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
                    setAttrWeights(node, a, weights, pa, int(i))
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
