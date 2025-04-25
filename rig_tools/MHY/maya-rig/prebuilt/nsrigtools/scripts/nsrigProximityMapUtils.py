import re

import maya.api.OpenMaya as om
import maya.cmds as cmds

TENSION_TYPES = ("tension", "compression", "stretch", "shear")
PLUGIN_NAME = "nsrigProximityMap"
NODE_TYPE_NAME = "nsrigProximityMap"
DEFAULT_SETTINGS = {
    "radius": 1,
    "maxBlendedWeight": 1,
    "blendOperator": 0,
    "smoothingIterations": 0,
}


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def create(srcMesh, tgtMeshes, name="", worldSpace=True, **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if type(tgtMeshes) == str:
        tgtMeshes = list(tgtMeshes)

    if name:
        pxyNode = cmds.createNode("nsrigProximityMap", n=name, **kwargs)
    else:
        pxyNode = cmds.createNode("nsrigProximityMap", **kwargs)

    srcAttr = "worldMesh" if worldSpace else "outMesh"
    cmds.connectAttr("%s.%s" % (srcMesh, srcAttr), "%s.sourceGeometry" % pxyNode, f=1)
    for tgt in tgtMeshes:
        addTarget(pxyNode, tgt, worldSpace)

    return pxyNode


def createBySelection(name="", worldSpace=True, createWeightShader=False, **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError(
            "%s: Please select target meshes then source mesh." % NODE_TYPE_NAME
        )

    node = create(sels[-1], sels[:-1], name, worldSpace, **kwargs)

    # create weight shader
    if createWeightShader:
        import nsrigWeightShaderUtils

        shader = nsrigWeightShaderUtils.create(sels[-1], "", skipSelect=True)
        cmds.connectAttr(
            "%s.outputWeights" % node, "%s.inputWeights" % shader, f=1
        )

    return node


def addTarget(pxyNode, geo, worldSpace=True):
    targetIds = cmds.getAttr("%s.target" % pxyNode, mi=1)
    nextId = 0 if not targetIds else targetIds[-1] + 1

    outMeshAttr = "worldMesh" if worldSpace else "outMesh"
    srcAttr = "%s.%s" % (geo, outMeshAttr)
    tgtAttr = "%s.target[%d].targetGeometry" % (pxyNode, nextId)

    cmds.connectAttr(srcAttr, tgtAttr, f=1)


def removeTarget(pxyNode, id):
    attr = "%s.target[%d]" % (pxyNode, id)
    cmds.removeMultiInstance(attr, b=1)


def makeTensionConnections(pxyNode, tensionName, prefix=""):
    assert tensionName in TENSION_TYPES

    try:
        cmds.loadPlugin("nsrigGeometryInfo", qt=1)
    except RuntimeError as err:
        raise RuntimeError(err)

    infoNodes = []
    targetIds = cmds.getAttr("%s.target" % pxyNode, mi=1)
    for i in targetIds:
        hist = cmds.listConnections(
            "%s.target[%d].targetGeometry" % (pxyNode, i), d=0, s=1
        )
        if not hist:
            continue

        tgtMesh = hist[0]
        infoNode = cmds.createNode("nsrigGeometryInfo")
        infoNodeXfm = cmds.listRelatives(infoNode, p=1)[0]
        infoNodeName = "%s_geoInfo" % tgtMesh
        if prefix:
            infoNodeName = "%s_%s" % (prefix, infoNodeName)
        infoNodeXfm = cmds.rename(infoNodeXfm, infoNodeName)
        infoNode = cmds.listRelatives(infoNodeXfm, s=1)[0]

        infoNodes.append(infoNode)

        cmds.connectAttr("%s.outMesh" % tgtMesh, "%s.inputGeometry" % infoNode, f=1)
        cmds.connectAttr(
            "%s.%s" % (infoNode, tensionName),
            "%s.target[%d].targetEnvelope" % (pxyNode, i),
            f=1,
        )

    return infoNodes


def getTargetId(pxyNode, tgtMesh):
    if cmds.nodeType(tgtMesh) == "transform":
        try:
            tgtMesh = cmds.listRelatives(tgtMesh, s=1)[0]
        except:
            return -1

    hist = cmds.listConnections(tgtMesh, d=1, s=0, et=1, t="nsrigProximityMap")

    if not hist or pxyNode not in hist:
        return -1

    hist_plugs = cmds.listConnections(
        tgtMesh, d=1, s=0, et=1, t="nsrigProximityMap", p=1
    )

    pxyTgtPlug = hist_plugs[hist.index(pxyNode)]

    try:
        id = re.findall(r"target\[(\d+)\]", pxyTgtPlug)[0]
    except:
        return -1

    return int(id)
