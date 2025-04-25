import json

import maya.cmds as cmds
import maya.api.OpenMayaAnim as oma2

from nsrigCollisionCommon import *

PLUGIN_NAME = 'nsrigCollisionTools'
NODE_TYPE_NAME = 'nsrigSelfCollide'

DEFAULT_SETTINGS = {
    'envelope': 1.0,
    'forwardIterations': 20,
    'reverseSteps': 30,
    'postIterations': 0,
    'smoothing': 0.2,
    'surfaceSmoothing': 1.0,
    'bendingResistance': 0.0,
    'bulge': 0.0,
    'bulgeDistance': 1.0,
    'separationDistance': 0.0,
}

WEIGHT_ATTRS = ['weights', 'smoothingWeights', 'bulgeWeights']


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def create(mesh, name='', **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not mesh:
        raise RuntimeError('%s: Please provide a mesh.' % NODE_TYPE_NAME)

    node = cmds.deformer(mesh, typ=NODE_TYPE_NAME, n=name, **kwargs)[0]

    return node


def createBySelection(name='', **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select a mesh.' % NODE_TYPE_NAME)

    return create(sels[0], name, **kwargs)


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


def getWeightPlugs(node=None):
    return WEIGHT_ATTRS
