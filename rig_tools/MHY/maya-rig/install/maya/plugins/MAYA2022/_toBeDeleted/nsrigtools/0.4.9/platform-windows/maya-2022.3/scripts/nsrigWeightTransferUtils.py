import maya.cmds as cmds
import maya.api.OpenMaya as om


import maya.cmds as cmds

def makeDeltaConnections( srcBS, transferNode, tgtBS, tgtIds ):
    for id in tgtIds:
        tgtItemAttr = 'inputTarget[0].inputTargetGroup[%d].inputTargetItem[6000]' % id
        srcDataGrpAttr = 'sourceDataGroup[%d]' % id

        # make source blendShape connects to transfer node
        srcAttr = '.'.join([srcBS, tgtItemAttr, 'inputPointsTarget'])
        tgtAttr = '.'.join([transferNode, srcDataGrpAttr, 'sourceDeltaPoints'])

        cmds.connectAttr( srcAttr, tgtAttr, f=1 )

        srcAttr = '.'.join([srcBS, tgtItemAttr, 'inputComponentsTarget'])
        tgtAttr = '.'.join([transferNode, srcDataGrpAttr, 'sourceDeltaComponents'])

        cmds.connectAttr( srcAttr, tgtAttr, f=1 )

        # make transfer node connects to target blendShape
        outDataGrpAttr = 'outputDataGroup[%d]' % id
        srcAttr = '.'.join([transferNode, outDataGrpAttr, 'outputDeltaPoints'])
        tgtAttr = '.'.join([tgtBS, tgtItemAttr, 'inputPointsTarget'])

        cmds.connectAttr( srcAttr, tgtAttr, f=1 )

        srcAttr = '.'.join([transferNode, outDataGrpAttr, 'outputDeltaComponents'])
        tgtAttr = '.'.join([tgtBS, tgtItemAttr, 'inputComponentsTarget'])

        cmds.connectAttr( srcAttr, tgtAttr, f=1 )


if __name__ == '__main__':
    srcBsNode = 'blendShape1'
    tgtBsNode = 'blendShape2'
    transferNode = 'nsrigDeltaTransfer1'
    tgtIds = [0, 1, 2, 3]

    makeDeltaConnections( srcBsNode, transferNode, tgtBsNode, tgtIds )