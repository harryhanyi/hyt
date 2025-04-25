import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender

kPluginNodeTypeName = "limbNode"
limbShapeNodeId = OpenMaya.MTypeId(0x87079)
glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


class limbShapeNode(OpenMayaMPx.MPxSurfaceShape):
    def __init__(self):
        OpenMayaMPx.MPxSurfaceShape.__init__(self)

    # override
    def postConstructor(self):
        self.setRenderable(False)
        
    # override
    def isBounded(self):
        return False

        
# creator
def nodeCreator():
    return OpenMayaMPx.asMPxPtr( limbShapeNode() )


# initializer
def nodeInitializer():
    print('Initializing...')
    
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kPluginNodeTypeName,
                             limbShapeNodeId,
                             nodeCreator,
                             nodeInitializer,
                             OpenMayaMPx.MPxNode.kSurfaceShape)
    except:
        sys.stderr.write("Failed to register command: {}\n".format(kPluginNodeTypeName))
        raise


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(limbShapeNodeId)
    except:
        sys.stderr.write( "Failed to unregister node: {}\n".format(kPluginNodeTypeName))
