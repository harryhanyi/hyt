#include "miController.h"
#include "miControllerManip.h"

MManipData LSControllerManip::startPointCallback(unsigned index) 
const
{
	MFnNumericData numData;
	MObject numDataObj = numData.create(MFnNumericData::k3Double);
	MVector vec = nodeTranslation();
	numData.setData(vec.x, vec.y, vec.z);
	return MManipData(numDataObj);
}

MVector LSControllerManip::nodeTranslation() const
{
	MFnDagNode dagFn(fNodePath);
	MDagPath path;
	dagFn.getPath(path);
	path.pop();  // pop from the shape to the transform
	MFnTransform transformFn(path);
	return transformFn.getTranslation(MSpace::kWorld);
}

MTypeId LSControllerManip::sId(0x001357c1);

LSControllerManip::LSControllerManip() 
{ 
    // Do not call createChildren from here 
}


LSControllerManip::~LSControllerManip() 
{
}


void* LSControllerManip::creator()
{
     return new LSControllerManip();
}


MStatus LSControllerManip::initialize()
{ 
    MStatus stat;
    stat = MPxManipContainer::initialize();
    return stat;
}


MStatus LSControllerManip::createChildren()
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


MStatus LSControllerManip::connectToDependNode(const MObject &node)
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

	MPlug sizePlug = nodeFn.findPlug("size",  true,  &stat);
    if (MStatus::kFailure != stat) {
	    distanceManipFn.connectToDistancePlug(sizePlug);
		unsigned startPointIndex = distanceManipFn.startPointIndex();
	    addPlugToManipConversionCallback(startPointIndex, 
										 (plugToManipConversionCallback) 
										 &LSControllerManip::startPointCallback);

		// also let the user tweak the size via the In-View Editor
		//
		addPlugToInViewEditor( sizePlug );

		finishAddingManips();
	    MPxManipContainer::connectToDependNode(node);
	}

    return stat;
}

// Viewport 2.0 manipulator draw overrides
void	LSControllerManip::preDrawUI( const M3dView &view )
{
	// Update text drawing position
	fTextPosition = nodeTranslation();
}

void	LSControllerManip::drawUI(
	MHWRender::MUIDrawManager& drawManager,
	const MHWRender::MFrameContext& frameContext ) const
{
	drawManager.beginDrawable();

	drawManager.setColor( MColor( 0.0f, 1.0f, 0.1f ) );
	//drawManager.text( fTextPosition, "Manipulate", MHWRender::MUIDrawManager::kLeft );

	drawManager.text2d( MPoint(100,100), "Manipulate", MHWRender::MUIDrawManager::kLeft );

	drawManager.endDrawable();
}
