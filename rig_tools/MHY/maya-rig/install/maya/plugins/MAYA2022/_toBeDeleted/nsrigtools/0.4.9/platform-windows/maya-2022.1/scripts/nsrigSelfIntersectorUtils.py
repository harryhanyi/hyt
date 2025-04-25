import maya.cmds as cmds
import maya.api.OpenMaya as om

def getOutputWeights(node):
    return cmds.getAttr('%s.outputWeights' % node)[0]

def getIntersectedFaces(node):
    return cmds.getAttr('%s.intersectedFaces' % node)

def getPartitionFaces(node, id):
    return cmds.getAttr('%s.partition[%d].partitionFaces' % (node, id) )

def getPartitionWeights(node, id):
    return cmds.getAttr('%s.partition[%d].partitionWeights' % (node, id) )[0]

def selectIntersectedFaces(mesh, node):
    faces = getIntersectedFaces(node)
    if not faces: return

    faceItems = []
    for f in faces:
        item = '%s.f[%d]' % (mesh, f)
        faceItems.append( item )
    
    cmds.select(faceItems, r=1)

def selectPartitionFaces(mesh, node, id):
    faces = getPartitionFaces(node, id)
    if not faces: return

    faceItems = []
    for f in faces:
        item = '%s.f[%d]' % (mesh, f)
        faceItems.append( item )
    
    cmds.select(faceItems, r=1)

def getNumPartitions(node):
    return cmds.getAttr('%s.numPartitions' % node)