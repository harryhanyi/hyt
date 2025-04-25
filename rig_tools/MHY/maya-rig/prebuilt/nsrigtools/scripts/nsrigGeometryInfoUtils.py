import random
import sys

import maya.api.OpenMaya as om
import maya.cmds as cmds

PLUGIN_NAME = "nsrigGeometryInfo"
NODE_TYPE_NAME = "nsrigGeometryInfo"
DEFAULT_SETTINGS = {
    "measure": 0,
    "deltaComponent": 0,
    "displayMetricInfo": False,
    "displayDeltaFlow": False,
}

WEIGHT_ATTRS = [
    "deltaWeights",
    "curvature",
    "posCurvature",
    "negCurvature",
    "curvatureWeights",
    "posCurvatureWeights",
    "negCurvatureWeights",
    "tensionWeights",
    "compressionWeights",
    "stretchWeights",
    "shearWeights",
    "fluxes",
    "inFluxes",
    "outFluxes",
    "fluxWeights",
    "inFluxWeights",
    "outFluxWeights",
]


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def getDagPath(name):
    selList = om.MSelectionList()

    try:
        selList.add(name)
        return selList.getDagPath(0)
    except:
        return None


def getShapePath(name):
    path = getDagPath(name)

    if path.apiType() == om.MFn.kTransform:
        path.extendToShape()
    return path


def create(
    mesh,
    refMesh=None,
    name="",
    worldSpace=False,
    createRefMesh=True,
    createWeightShader=False,
    weightAttr=None,
    **kwargs,
):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not mesh:
        raise RuntimeError("%s: Please provide one mesh." % NODE_TYPE_NAME)

    node = cmds.createNode(NODE_TYPE_NAME, **kwargs)
    if name:
        parent = cmds.listRelatives(node, p=1, pa=1)[0]
        parent = cmds.rename(parent, name)
        node = cmds.listRelatives(parent, c=1, pa=1)[0]

    meshAttr = "worldSpace" if worldSpace else "outMesh"
    cmds.connectAttr("%s.%s" % (mesh, meshAttr), "%s.inputGeometry" % node, f=1)

    if not refMesh and createRefMesh:
        # create reference mesh
        meshShapePath = getDagPath(mesh)
        fnDag = om.MFnDagNode(meshShapePath)
        dupObj = fnDag.duplicate()
        refMesh = om.MFnDagNode(dupObj).partialPathName()
        refMesh = cmds.rename(refMesh, mesh + "Ref")
        refMeshShape = cmds.listRelatives(refMesh, s=1)[0]
        cmds.rename(refMeshShape, refMesh + "Shape")
        cmds.hide(refMesh)

    if refMesh:
        cmds.connectAttr("%s.%s" % (refMesh, meshAttr), "%s.referenceGeometry" % node)

    if createWeightShader:
        if weightAttr not in WEIGHT_ATTRS:
            raise RuntimeError("%s: Invalid weight attribute '%s'." % weightAttr)

        import nsrigWeightShaderUtils

        shadingNode = nsrigWeightShaderUtils.create(mesh, "", skipSelect=True)
        cmds.connectAttr(
            "%s.%s" % (node, weightAttr),
            "%s.inputWeights" % shadingNode,
            f=1,
        )

    return node


def createBySelection(
    name="",
    worldSpace=False,
    createRefMesh=True,
    createWeightShader=False,
    weightAttr=None,
    **kwargs,
):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError("%s: Please select some meshes." % NODE_TYPE_NAME)

    animMesh = sels[0]
    refMesh = sels[1] if len(sels) > 1 else None
    return create(
        animMesh,
        refMesh,
        name,
        worldSpace,
        createRefMesh,
        createWeightShader,
        weightAttr,
        **kwargs,
    )
