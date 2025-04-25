#include <maya/MIOStream.h>
#include <maya/MPxNode.h>
#include <maya/MPxLocatorNode.h>
#include <maya/MString.h>
#include <maya/MVector.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MColor.h>
#include <maya/M3dView.h>
#include <maya/MDistance.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MFn.h>
#include <maya/MPxNode.h>
#include <maya/MPxManipContainer.h>
#include <maya/MFnDistanceManip.h>
#include <maya/MPxContext.h>
#include <maya/MPxSelectionContext.h>
#include <maya/MFnNumericData.h>
#include <maya/MManipData.h>
#include <maya/MEventMessage.h>


#ifndef LSVIEWPORTPICKERMANIP_H_
#define LSVIEWPORTPICKERMANIP_H_
class LSViewportPickerManip : public MPxManipContainer
{
public:
    LSViewportPickerManip();
    ~LSViewportPickerManip() override;

    static void * creator();
    static MStatus initialize();
    MStatus createChildren() override;
    MStatus connectToDependNode(const MObject & node) override;
    // Viewport 2.0 manipulator draw overrides
    void        preDrawUI( const M3dView &view ) override;
    void        drawUI( MHWRender::MUIDrawManager& drawManager,
                        const MHWRender::MFrameContext& frameContext) const override;
    MManipData startPointCallback(unsigned index) const;
    MVector nodeTranslation() const;
    MDagPath fDistanceManip;
    MDagPath fNodePath;
    // Value prepared for Viewport 2.0 draw
    MPoint fTextPosition;
    void updateManipLocations();

public:
    static MTypeId id;
};

#endif