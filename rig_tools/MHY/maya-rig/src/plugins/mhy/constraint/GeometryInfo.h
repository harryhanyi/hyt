#pragma once
#include <string.h>
#include <maya/MIOStream.h>
#include <math.h>
#include <maya/MPxTransform.h>
#include <maya/MPxConstraint.h>
#include <maya/MPxConstraintCommand.h>
#include <maya/MArgDatabase.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MGlobal.h>
#include <maya/MString.h>
#include <maya/MTypeId.h>
#include <maya/MPlug.h>
#include <maya/MVector.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MArrayDataHandle.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnTransform.h>
#include <maya/MVector.h>
#include <maya/MTypes.h>
#include <maya/MFnNumericData.h>
#include <maya/MDGModifier.h>
#include <maya/MFloatPointArray.h>
#include <maya/MIntArray.h>
#include <maya/MFloatPointArray.h>
#include <maya/MMatrix.h>
#include <math.h>
#include <float.h>
#include <string>
#include <vector>
class LSGeometryInfo : public MPxNode
{
public:
	enum coordType
	{
		vertex,
		uv
	};
	static const std::vector<std::string> coordTypeNames;

	LSGeometryInfo();
	~LSGeometryInfo() override;
	bool updateBuffer(const float *positions, const size_t size);
	MStatus computeParameters(MArrayDataHandle &inputArrayHandle, MDataBlock &datablock);
	MStatus compute(const MPlug &plug, MDataBlock &data) override;
	MPxNode::SchedulingType schedulingType() const;
	MVector setValue(MObject attribute, const unsigned int index, const MVector &position);
	bool isGPUOverride();
	static void *creator();
	static MStatus initialize();
	static MObject aTargetGeometry;
	static MObject aDirtyDriver;
	static MObject aCoordinate;
	static MObject aTargetMatrix;
	static MObject aMatrix;
	// static MObject aCoordType;
	static MObject aIndex;
	static MObject aU;
	static MObject aV;
	static MObject aW;
	static MObject aUVCoord;

	static MObject aIndices;
	static MObject aParameters;
	static MObject aTranslateX;
	static MObject aTranslateY;
	static MObject aTranslateZ;
	static MObject aTranslate;
	static MObject aRotateX;
	static MObject aRotateY;
	static MObject aRotateZ;
	static MObject aRotate;
	static MObject aRotateOrder;
	static MTypeId sId;

private:
	void cleanDirtyDriver(const MPlug &plug, MDataBlock &datablock);
	bool updateFromMesh(MObject meshObj, const int elementBeginn, const int elementEndd, MDataBlock &datablock);
	bool updateFromNurbs(MObject meshObj, const int elementBeginn, const int elementEndd, MDataBlock &datablock);
	MFloatPointArray _vertices;
	MIntArray _vertexCount;
	MIntArray _vertexList;
};
