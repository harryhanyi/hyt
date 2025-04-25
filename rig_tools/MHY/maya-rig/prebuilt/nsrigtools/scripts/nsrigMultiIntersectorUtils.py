import maya.cmds as cmds
import maya.api.OpenMaya as om

PLUGIN_NAME = 'nsrigCollisionTools'
NODE_TYPE_NAME = 'nsrigMultiIntersector'

DEFAULT_SETTINGS = {
    'intersectionTransparency': 0.0,
    'randomizeColors': False,
    'backfaceCulling': False,
    'maxIntersectionDepth': 0.5,
    'intersectionSteps': 5,
    'maxPosCollisionDepth': 0.5,
    'posCollisionSteps': 5,
    'maxNegCollisionDepth': 0.5,
    'negCollisionSteps': 5,
    'weightSmoothingIterations': 0,
}


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def addInputGeometry(node, mesh, worldSpace=True):
    if isinstance(mesh, str):
        mesh = list(mesh)

    ids = cmds.getAttr('%s.inputGeometry' % node, mi=1)
    nextId = 0 if not ids else ids[-1] + 1

    srcAttr = 'worldMesh' if worldSpace else 'outMesh'
    for m in mesh:
        cmds.connectAttr(
            '%s.%s' % (m, srcAttr), '%s.inputGeometry[%d]' % (node, nextId)
        )
        nextId += 1


def create(mesh, name='', worldSpace=True, **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except RuntimeError as e:
            raise (e)

    if not mesh:
        raise RuntimeError('%s: Please provide some meshes.' % NODE_TYPE_NAME)

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

    return create(sels, name, worldSpace, **kwargs)


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


def getIntersectedFaces(node, id):
    return cmds.getAttr('%s.outIntersectedFaces[%d]' % (node, id))


def getCollidedFaces(node, id):
    return cmds.getAttr('%s.outCollidedFaces[%d]' % (node, id))


def getIntersectionWeights(node, id):
    return cmds.getAttr(
        '%s.outIntersectionWeightList[%d].intersectionWeights' % (node, id)
    )[0]


def getPosCollisionWeights(node, id):
    return cmds.getAttr(
        '%s.outPosCollisionWeightList[%d].posCollisionWeights' % (node, id)
    )[0]


def getNegCollisionWeights(node, id):
    return cmds.getAttr(
        '%s.outNegCollisionWeightList[%d].negCollisionWeights' % (node, id)
    )[0]


def selectIntersectedFaces(node, id, mesh):
    faces = getIntersectedFaces(node, id)
    if not faces:
        return

    faceItems = []
    for f in faces:
        item = '%s.f[%d]' % (mesh, f)
        faceItems.append(item)

    cmds.select(faceItems, r=1)


def selectCollidedFaces(node, id, mesh):
    faces = getCollidedFaces(node, id)
    if not faces:
        return

    faceItems = []
    for f in faces:
        item = '%s.f[%d]' % (mesh, f)
        faceItems.append(item)

    cmds.select(faceItems, r=1)
