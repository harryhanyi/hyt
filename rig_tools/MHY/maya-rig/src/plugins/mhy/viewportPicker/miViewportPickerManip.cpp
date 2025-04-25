#include "miViewportPickerManip.h"
#include <maya/MGlobal.h>

MManipData LSViewportPickerManip::startPointCallback(unsigned index)
const
{
    MFnNumericData numData;
    MObject numDataObj = numData.create(MFnNumericData::k3Double);
    MVector vec = nodeTranslation();
    numData.setData(vec.x, vec.y, vec.z);
    return MManipData(numDataObj);
}
MVector LSViewportPickerManip::nodeTranslation() const
{
    MFnDagNode dagFn(fNodePath);
    MDagPath path;
    dagFn.getPath(path);
    path.pop();  // pop from the shape to the transform
    MFnTransform transformFn(path);
    return transformFn.getTranslation(MSpace::kWorld);
}
MTypeId LSViewportPickerManip::id(0x001357c5);
LSViewportPickerManip::LSViewportPickerManip()
{
    // Do not call createChildren from here
}
LSViewportPickerManip::~LSViewportPickerManip()
{
}
void* LSViewportPickerManip::creator()
{
     return new LSViewportPickerManip();
}
MStatus LSViewportPickerManip::initialize()
{
    MStatus stat;
    stat = MPxManipContainer::initialize();
    return stat;
}
MStatus LSViewportPickerManip::createChildren()
{
    MStatus stat = MStatus::kSuccess;
    MString manipName("distanceManip");
    MString distanceName("distance");
    MPoint startPoint(0.0, 0.0, 0.0);
    MVector direction(0.0, 1.0, 0.0);
    fDistanceManip = addDistanceManip(manipName,
                                      distanceName);
    MFnDistanceManip distanceManipFn(fDistanceManip);
    distanceManipFn.setStartPoint(startPoint);
    distanceManipFn.setDirection(direction);

    return stat;
}
MStatus LSViewportPickerManip::connectToDependNode(const MObject &node)
{
    MStatus stat;
    // Get the DAG path
    //
    MFnDagNode dagNodeFn(node);
    dagNodeFn.getPath(fNodePath);
    // Connect the plugs
    //
    MFnDistanceManip distanceManipFn(fDistanceManip);
    MFnDependencyNode nodeFn(node);
    MPlug sizePlug = nodeFn.findPlug("aPickerLocalScale",  true,  &stat);

    if (MStatus::kFailure != stat) {
        distanceManipFn.connectToDistancePlug(sizePlug);
        unsigned startPointIndex = distanceManipFn.startPointIndex();
        addPlugToManipConversionCallback(startPointIndex,
            (plugToManipConversionCallback)
            &LSViewportPickerManip::startPointCallback);
        addPlugToInViewEditor(sizePlug);
        finishAddingManips();
        MPxManipContainer::connectToDependNode(node);
    }
    return stat;
}
// Viewport 2.0 manipulator draw overrides
void    LSViewportPickerManip::preDrawUI( const M3dView &view )
{
    // Update text drawing position
    MStatus stat;

    fTextPosition = nodeTranslation();
    MObject node = fNodePath.node();
    MFnDependencyNode dpNode(node);
    MPlug positionPlug = dpNode.findPlug("pickerPosition", true, &stat);
    if (MStatus::kFailure != stat) {
        MObject o = positionPlug.asMObject();
        MFnNumericData nData(o);
        double x, y;
        nData.getData(x, y);
        MPoint nearClipPt, farClipPt;
        view.viewToWorld(x, y, nearClipPt, farClipPt);
        MFnDistanceManip distManip(fDistanceManip);
        nearClipPt = nearClipPt + (farClipPt - nearClipPt).normal()*10;

        MMatrix worldMatrix = fNodePath.inclusiveMatrix();
        MTransformationMatrix tm(worldMatrix);
        double scale[3];
        tm.getScale(scale, MSpace::kObject);
        distManip.setManipScale(1.0 / (abs(scale[0]) + abs(scale[0]) + abs(scale[0]) / 3));

        distManip.setTranslation(nearClipPt, MSpace::kWorld);
    }

}
void    LSViewportPickerManip::drawUI(
    MHWRender::MUIDrawManager& drawManager,
    const MHWRender::MFrameContext& frameContext ) const
{
    drawManager.beginDrawable();
    drawManager.setColor( MColor( 0.0f, 1.0f, 0.1f ) );
    drawManager.text2d( MPoint(100,100), "Scale Pickers", MHWRender::MUIDrawManager::kLeft );
    drawManager.endDrawable();
}
