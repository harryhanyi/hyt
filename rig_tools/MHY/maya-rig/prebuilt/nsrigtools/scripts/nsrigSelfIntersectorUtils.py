import maya.cmds as cmds
import maya.api.OpenMaya as om

PLUGIN_NAME = 'nsrigCollisionTools'
NODE_TYPE_NAME = 'nsrigSelfIntersector'

DEFAULT_SETTINGS = {
    'intersectionTransparency': 0.0,
    'fontSize': 16,
    'backfaceCulling': False,
    'intersectionPartitioning': False,
    'partitioningThreshold': 0.5,
    'maxIntersectionDepth': 0.5,
    'intersectionSteps': 5,
    'weightSmoothingIterations': 0,
}


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def _selectMeshFaces(mesh, faces):
    visitedFaces = [False] * cmds.polyEvaluate(mesh, f=1)
    faceItems = []
    for f in faces:
        if visitedFaces[f]:
            continue

        item = '%s.f[%d]' % (mesh, f)
        faceItems.append(item)

        visitedFaces[f] = True

    cmds.select(faceItems, r=1)


def _getIntersectedPrimInfo(prims, auxPrims, auxPrimOffsets):
    res = {}
    for i, f in enumerate(prims):
        offset = auxPrimOffsets[i * 2]
        if offset < 0:
            res[f] = tuple()
            continue

        count = auxPrimOffsets[i * 2 + 1]
        currAuxPrims = [0] * count
        for j in range(count):
            currAuxPrims[j] = auxPrims[offset + j]

        res[f] = tuple(currAuxPrims)

    return res


def addInputGeometry(node, mesh, worldSpace=True):
    srcAttr = 'worldMesh' if worldSpace else 'outMesh'
    cmds.connectAttr('%s.%s' % (mesh, srcAttr), '%s.inputGeometry' % node)


def create(mesh, name='', worldSpace=True, **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except RuntimeError as e:
            raise (e)

    if not mesh:
        raise RuntimeError('%s: Please provide one mesh.' % NODE_TYPE_NAME)

    node = cmds.createNode(NODE_TYPE_NAME, **kwargs)
    if name:
        parent = cmds.listRelatives(node, p=1, pa=1)[0]
        parent = cmds.rename(parent, name)
        node = cmds.listRelatives(parent, c=1, pa=1)[0]

    addInputGeometry(node, mesh, worldSpace)
    return node


def createBySelection(name='', worldSpace=True, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError('%s: Please select some meshes.' % NODE_TYPE_NAME)

    nodes = []
    for sel in sels:
        n = create(sel, name, worldSpace, **kwargs)
        nodes.append(n)

    return nodes


def getNumPartitions(node):
    return cmds.getAttr('%s.numPartitions' % node)


def getIntersectionWeights(node):
    return cmds.getAttr('%s.outIntersectionWeights' % node)[0]


def getIntersectedFaces(node):
    return cmds.getAttr('%s.outIntersectedFaces' % node)


def getAuxIntersectedFaces(node):
    faces = cmds.getAttr('%s.outIntersectedFaces' % node)
    auxFaces = cmds.getAttr('%s.outAuxIntersectedFaces' % node)
    auxFaceOffsets = cmds.getAttr('%s.outAuxIntersectedFaceOffsets' % node)

    return _getIntersectedPrimInfo(faces, auxFaces, auxFaceOffsets)


def getIntersectedPartitions(node):
    numPart = getNumPartitions(node)
    parts = list(range(numPart))
    itsParts = cmds.getAttr('%s.outIntersectedPartitions' % node)
    itsPartOffsets = cmds.getAttr('%s.outIntersectedPartitionOffsets' % node)

    return _getIntersectedPrimInfo(parts, itsParts, itsPartOffsets)


def getPartitionFaces(node, id):
    return cmds.getAttr('%s.outPartitionFaces[%d]' % (node, id))


def getAuxPartitionFaces(node, id):
    faces = cmds.getAttr('%s.outPartitionFaces[%d]' % (node, id))
    auxFaces = cmds.getAttr('%s.outAuxPartitionFaces[%d]' % (node, id))
    auxFaceOffsets = cmds.getAttr('%s.outAuxPartitionFaceOffsets[%d]' % (node, id))

    return _getIntersectedPrimInfo(faces, auxFaces, auxFaceOffsets)


def getPartitionArea(node, id):
    return cmds.getAttr('%s.outPartitionArea[%d]' % (node, id))


def getPartitionAreas(node):
    numParts = getNumPartitions(node)
    areas = [0] * numParts
    for i in range(numParts):
        areas[i] = cmds.getAttr('%s.outPartitionArea[%d]' % (node, i))

    return areas


def getPartitionVolume(node, id):
    return cmds.getAttr('%s.outPartitionVolume[%d]' % (node, id))


def getPartitionVolumes(node):
    numParts = getNumPartitions(node)
    volumes = [0] * numParts
    for i in range(numParts):
        volumes[i] = cmds.getAttr('%s.outPartitionVolume[%d]' % (node, i))

    return volumes


def getPartitionWeights(node, id):
    return cmds.getAttr('%s.outPartitionWeightList[%d].partitionWeights' % (node, id))[
        0
    ]


def selectIntersectedFaces(node, mesh):
    faces = getIntersectedFaces(node)
    if not faces:
        return

    _selectMeshFaces(mesh, faces)


def selectAuxIntersectedFaces(node, mesh):
    faces = cmds.getAttr('%s.outAuxIntersectedFaces' % node)
    if not faces:
        return

    _selectMeshFaces(mesh, faces)


def selectPartitionFaces(node, id, mesh):
    faces = getPartitionFaces(node, id)
    if not faces:
        return

    _selectMeshFaces(mesh, faces)


def selectAuxPartitionFaces(node, id, mesh):
    faces = cmds.getAttr('%s.outAuxPartitionFaces[%d]' % (node, id))
    if not faces:
        return

    _selectMeshFaces(mesh, faces)
