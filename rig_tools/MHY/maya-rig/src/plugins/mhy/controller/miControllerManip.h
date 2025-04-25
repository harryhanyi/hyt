#pragma once

#include <maya/MObject.h>
#include <maya/MDagPath.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MFnTransform.h>
#include <maya/MFnDistanceManip.h>
#include <maya/MFnDependencyNode.h>
// Viewport 2.0MFnDagNode
#include <maya/MDrawRegistry.h>

class LSControllerManip : public MPxManipContainer
{
public:
    LSControllerManip();
    ~LSControllerManip() override;
    
    static void * creator();
    static MStatus initialize();
    MStatus createChildren() override;
    MStatus connectToDependNode(const MObject & node) override;

	// Viewport 2.0 manipulator draw overrides
	void		preDrawUI( const M3dView &view ) override;
	void		drawUI( MHWRender::MUIDrawManager& drawManager,
						const MHWRender::MFrameContext& frameContext) const override;

	MManipData startPointCallback(unsigned index) const;
	MVector nodeTranslation() const;
    MDagPath fDistanceManip;
	MDagPath fNodePath;

	// Value prepared for Viewport 2.0 draw
	MPoint fTextPosition;
public:
    static MTypeId sId;
};
