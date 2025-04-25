import maya.api.OpenMaya as om
import maya.cmds as cmds

PLUGIN_NAME = "nsrigWeightShader"
NODE_TYPE_NAME = "nsrigWeightShader"


def loadPlugin():
    cmds.loadPlugin(PLUGIN_NAME)


def unloadPlugin():
    cmds.unloadPlugin(PLUGIN_NAME)


def create(mesh, name="", **kwargs):
    if not cmds.pluginInfo(PLUGIN_NAME, q=1, l=1):
        try:
            loadPlugin()
        except Exception as e:
            raise (e)

    if not mesh:
        raise RuntimeError("%s: Please provide one mesh." % NODE_TYPE_NAME)

    if not kwargs:
        kwargs = {}

    if name:
        kwargs.update({"n": name})
    # create nsrigWeightShader and nsrigWeightShaderSG
    node = cmds.shadingNode(NODE_TYPE_NAME, asShader=True, **kwargs)
    nodeSG = cmds.sets(
        empty=True, renderable=True, noSurfaceShader=True, name="%sSG" % node
    )

    cmds.connectAttr("%s.outColor" % node, "%s.surfaceShader" % nodeSG)
    cmds.sets(mesh, e=True, forceElement=nodeSG)

    return node


def createBySelection(name="", **kwargs):
    sels = cmds.ls(sl=1, allPaths=1)
    if not sels:
        raise RuntimeError("%s: Please select some meshes." % NODE_TYPE_NAME)

    nodes = []
    for sel in sels:
        node = create(sel, name, **kwargs)
        nodes.append(node)
    return nodes
