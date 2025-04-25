#pragma once
#include "GeometryInfo.h"

#include <string.h>
#include <maya/MIOStream.h>
#include <maya/MStringArray.h>
#include <math.h>

#include <maya/MPxDeformerNode.h>
#include <maya/MItGeometry.h>
#include <maya/MPxLocatorNode.h>

#include <maya/MFnNumericAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnMatrixData.h>

#include <maya/MFnDependencyNode.h>

#include <maya/MTypeId.h>
#include <maya/MPlug.h>

#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MArrayDataHandle.h>

#include <maya/MPoint.h>
#include <maya/MVector.h>
#include <maya/MMatrix.h>

#include <maya/MDagModifier.h>

#include <maya/MPxGPUDeformer.h>
#include <maya/MGPUDeformerRegistry.h>
#include <maya/MOpenCLInfo.h>
#include <maya/MViewport2Renderer.h>
#include <maya/MFnMesh.h>
#include <maya/MPointArray.h>

#include <vector>

class LSBufferReaderNode : public MPxDeformerNode
{
public:
	enum coordType
	{
		vertex,
		uv
	};
	static const std::vector<std::string> coordTypeNames;
	LSBufferReaderNode();
	~LSBufferReaderNode() override;

	static void *creator();
	static MStatus initialize();
	MStatus deform(MDataBlock &block,
				   MItGeometry &iter,
				   const MMatrix &mat,
				   unsigned int multiIndex) override;
	LSGeometryInfo* getGeometryInfo();
	void updateBuffer(const float* buffer, const size_t size);
public:
	// local node attributes
	static MTypeId id;
    std::vector<float> positions;
	// path from where the plugin was loaded
	static MString pluginPath;
	static MObject aIndices;
	static MObject aParameters;
private:
};
