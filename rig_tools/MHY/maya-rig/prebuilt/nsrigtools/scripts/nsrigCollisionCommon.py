import maya.api.OpenMaya as om2


def getDependencyNode(name):
    selList = om2.MSelectionList()

    try:
        selList.add(name)
        return selList.getDependNode(0)
    except:
        return None


def getAttrWeights(
    node, attr, numWeights, parentAttr=None, parentAttrIndex=-1, defaultVal=1.0
):
    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)
    attrPlug = fnNode.findPlug(attr, False)

    if parentAttr and parentAttrIndex >= 0:
        parentAttrPlug = fnNode.findPlug(parentAttr, False)
        attrPlug.selectAncestorLogicalIndex(parentAttrIndex, parentAttrPlug.attribute())

    weights = [defaultVal] * numWeights
    existingIDs = attrPlug.getExistingArrayAttributeIndices()
    for i in existingIDs:
        if i >= numWeights:
            break
        weights[i] = attrPlug.elementByLogicalIndex(i).asFloat()

    return weights


def setAttrWeights(node, attr, weights, parentAttr=None, parentAttrIndex=-1):
    nodeObj = getDependencyNode(node)
    fnNode = om2.MFnDependencyNode(nodeObj)
    attrPlug = fnNode.findPlug(attr, False)

    if parentAttr and parentAttrIndex >= 0:
        parentAttrPlug = fnNode.findPlug(parentAttr, False)
        attrPlug.selectAncestorLogicalIndex(parentAttrIndex, parentAttrPlug.attribute())

    for i, w in enumerate(weights):
        try:
            attrPlug.elementByLogicalIndex(i).setFloat(w)
        except:
            pass
