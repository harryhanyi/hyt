import sys
import random

import maya.cmds as cmds
import maya.api.OpenMaya as om

def connectDriverPosition(node, ctrl):
    cmds.connectAttr('%s.tx' % ctrl, '%s.driverPosition[0]' % node, f=1)
    cmds.connectAttr('%s.ty' % ctrl, '%s.driverPosition[1]' % node, f=1)
    cmds.connectAttr('%s.tz' % ctrl, '%s.driverPosition[2]' % node, f=1)

def connectDriverMatrix(node, ctrl, worldMatrix=False):
    if worldMatrix:
        cmds.connectAttr('%s.worldMatrix' % ctrl, '%s.driverMatrix' % node, f=1)
    else:
        cmds.connectAttr('%s.matrix' % ctrl, '%s.driverMatrix' % node, f=1)

def disconnectDriverMatrix(node):
    tgtAttr = '%s.driverMatrix' % node
    hist = cmds.listConnections(tgtAttr, s=1, d=0, p=1)
    if hist:
        srcAttr = hist[0]
        cmds.disconnectAttr(srcAttr, tgtAttr)

def connectPosePosition(node, poseId, ctrl):
    cmds.connectAttr('%s.tx' % ctrl, '%s.pose[%d].posePosition[0]' % (node, poseId), f=1)
    cmds.connectAttr('%s.ty' % ctrl, '%s.pose[%d].posePosition[1]' % (node, poseId), f=1)
    cmds.connectAttr('%s.tz' % ctrl, '%s.pose[%d].posePosition[2]' % (node, poseId), f=1)

def connectPoseMatrix(node, poseId, ctrl, worldMatrix=False):
    if worldMatrix:
        cmds.connectAttr('%s.worldMatrix' % ctrl, '%s.pose[%d].poseMatrix' % (node, poseId), f=1)
    else:
        cmds.connectAttr('%s.matrix' % ctrl, '%s.pose[%d].poseMatrix' % (node, poseId), f=1)

def disconnectPoseMatrix(node, poseId):
    tgtAttr = '%s.pose[%d].poseMatrix' % (node, poseId)
    hist = cmds.listConnections(tgtAttr, s=1, d=0, p=1)
    if hist:
        srcAttr = hist[0]
        cmds.disconnectAttr(srcAttr, tgtAttr)

def connectPoseTranslateValues(node, poseId, xfm):
    poseValAttr = '%s.pose[%d].poseValues' % (node, poseId)
    poseValIds = cmds.getAttr(poseValAttr, mi=1)

    if not poseValIds:
        nextId = 0
    else:
        nextId = poseValIds[-1] + 1
    
    cmds.connectAttr( '%s.tx' % xfm, '%s[%d]' % (poseValAttr, nextId) )
    cmds.connectAttr( '%s.ty' % xfm, '%s[%d]' % (poseValAttr, nextId+1) )
    cmds.connectAttr( '%s.tz' % xfm, '%s[%d]' % (poseValAttr, nextId+2) )

def connectPoseRotateValues(node, poseId, xfm):
    poseValAttr = '%s.pose[%d].poseValues' % (node, poseId)
    poseValIds = cmds.getAttr(poseValAttr, mi=1)

    if not poseValIds:
        nextId = 0
    else:
        nextId = poseValIds[-1] + 1
    
    cmds.connectAttr( '%s.rx' % xfm, '%s[%d]' % (poseValAttr, nextId) )
    cmds.connectAttr( '%s.ry' % xfm, '%s[%d]' % (poseValAttr, nextId+1) )
    cmds.connectAttr( '%s.rz' % xfm, '%s[%d]' % (poseValAttr, nextId+2) )

def connectPoseScaleValues(node, poseId, xfm):
    poseValAttr = '%s.pose[%d].poseValues' % (node, poseId)
    poseValIds = cmds.getAttr(poseValAttr, mi=1)

    if not poseValIds:
        nextId = 0
    else:
        nextId = poseValIds[-1] + 1
    
    cmds.connectAttr( '%s.sx' % xfm, '%s[%d]' % (poseValAttr, nextId) )
    cmds.connectAttr( '%s.sy' % xfm, '%s[%d]' % (poseValAttr, nextId+1) )
    cmds.connectAttr( '%s.sz' % xfm, '%s[%d]' % (poseValAttr, nextId+2) )

def connectPoseTransformValues(node, poseId, xfm, translate=True, rotate=True, scale=True):
    if translate:
        connectPoseTranslateValues(node, poseId, xfm)
    
    if rotate:
        connectPoseRotateValues(node, poseId, xfm)
    
    if scale:
        connectPoseScaleValues(node, poseId, xfm)

def setPoseName(node, poseId, name):
    cmds.setAttr( '%s.pose[%d].poseName' % (node, poseId), name, type="string" )

def setPoseIsolated(node, poseId, isolated):
    cmds.setAttr( '%s.pose[%d].poseIsolated' % (node, poseId), isolated )

def setAllPoseIsolated(node, isolated):
    poseIds = cmds.getAttr('%s.pose' % node, mi=1)
    for id in poseIds:
        cmds.setAttr( '%s.pose[%d].poseIsolated' % (node, id), isolated )
    
    # Enforce evaluation
    cmds.getAttr('%s.dummy' % node)

def connectPoseMatrices(node, ctrls, setName=True, worldMatrix=False):
    existingIds = cmds.getAttr('%s.pose' % node, mi=1)
    if existingIds:
        nextId = existingIds[-1] + 1
    else:
        nextId = 0

    for i, ctrl in enumerate(ctrls):
        poseId = nextId + i
        connectPoseMatrix(node, poseId, ctrl, worldMatrix)
        if setName:
            setPoseName(node, poseId, ctrl)

def deletePose(node, poseId):
    if poseId == 0:
        om.MGlobal.displayError('Deleting the neutral pose is forbidden.')
        return

    ids = cmds.getAttr('%s.pose' % node, mi=1)
    if not poseId in ids:
        om.MGlobal.displayError('pose[%d] is not existed.' % poseId)
        return

    cmds.setAttr('%s.pose[%d].poseDelete' % (node, poseId), True)
    cmds.removeMultiInstance('%s.pose[%d]' % (node, poseId), b=1)
    cmds.removeMultiInstance('%s.outputWeights[%d]' % (node, poseId), b=1)

def setPoseColor(node, poseId, color):
    cmds.setAttr('%s.pose[%d].poseColor' % (node, poseId), color[0], color[1], color[2], type="double3")

def randomColor():
    color = [0.0] * 3
    color[0] = random.uniform(0.0, 1.0)
    color[1] = random.uniform(0.0, 1.0)
    color[2] = random.uniform(0.0, 1.0)

    random.shuffle(color)
    return color

def setRandomPoseColor(node, poseId):
    color = randomColor()
    setPoseColor(node, poseId, color)

def randomizeAllPoseColors(node):
    poseIds = cmds.getAttr('%s.pose' % node, mi=1)
    numPoses = len(poseIds)
    colors = [om.MVector.kOneVector] * (poseIds[-1] + 1)
    # colors = [om.MVector.kZeroVector ] * (poseIds[-1] + 1)
    
    maxRetry = numPoses * 10

    for id in poseIds:
        minDiff = sys.float_info.max
        bestColor = om.MVector.kZeroVector
        currTry = 0
        while True:
            c = randomColor()
            newColor = om.MVector(c[0], c[1], c[2])
            retry = False

            for oldColor in colors:
                diff = newColor.normal() * oldColor.normal()

                if diff >= 0.9:
                    retry = True
                    break
            
                if diff < minDiff:
                    bestColor = newColor
                    minDiff = diff
            
            if not retry or currTry >= maxRetry:
                break

            currTry += 1
        
        colors[id] = bestColor

        setPoseColor(node, id, bestColor)
    
    # Enforce evaluation
    cmds.getAttr('%s.dummy' % node)