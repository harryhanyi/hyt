import maya.cmds as cmds

list_nodes = [
    "GRP_earGUI",
    "GRP_noseGUI",
    "GRP_mouthStickyGUI",
    "GRP_tongueGUI",
    "GRP_chinGUI",
    "GRP_neckGUI",
    "GRP_switchesGUI",
    "GRP_faceTweakersGUI",
    "GRP_faceAndEyesAimFollowHeadGUI"
]

def simplify():
    # Get namespace of the referenced rig
    referenced_rigs = []
    all_nodes = cmds.ls()

    for node in all_nodes:
        # Check if the node is part of a reference
        if cmds.referenceQuery(node, isNodeReferenced=True):
            reference_file = cmds.referenceQuery(node, filename=True)
            namespace = cmds.referenceQuery(node, namespace=True)
            if (reference_file, namespace) not in referenced_rigs:
                referenced_rigs.append((reference_file, namespace))

    namespace = ''
    if len(referenced_rigs) > 0:
        namespace = referenced_rigs[0][1] + ':'

    # Set visibility
    for node in list_nodes:
        vis = cmds.getAttr(namespace+node+".visibility")
        cmds.setAttr(namespace+node+".visibility", 1-vis)
