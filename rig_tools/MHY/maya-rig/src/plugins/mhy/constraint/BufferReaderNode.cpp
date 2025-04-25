#include "BufferReaderNode.h"
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnMessageAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnIntArrayData.h>
#include <maya/MPlugArray.h>
#include <clew/clew_cl.h>
MTypeId LSBufferReaderNode::id( 0x001357c3 );
MString LSBufferReaderNode::pluginPath;
MObject LSBufferReaderNode::aIndices;
MObject LSBufferReaderNode::aParameters;
const std::vector<std::string> LSBufferReaderNode::coordTypeNames = {"vertex", "uv"};

LSBufferReaderNode::LSBufferReaderNode() {}
LSBufferReaderNode::~LSBufferReaderNode() {}

void* LSBufferReaderNode::creator()
{
	return new LSBufferReaderNode();
}

MStatus LSBufferReaderNode::initialize()
{
	// local attribute initialization
	MFnMatrixAttribute  mAttr;
	MStatus status;
    MFnCompoundAttribute compoundAttrFn;
    MFnTypedAttribute typeAttrFn;
	aIndices = typeAttrFn.create("indexList", "il", MFnData::kIntArray, &status);
    CHECK_MSTATUS(typeAttrFn.setStorable(true));
    CHECK_MSTATUS(typeAttrFn.setArray(false));
    aParameters = compoundAttrFn.create("kernelParameters", "kp", &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(compoundAttrFn.setStorable(true));
    CHECK_MSTATUS(compoundAttrFn.setArray(false));
    CHECK_MSTATUS(compoundAttrFn.addChild(aIndices));
    CHECK_MSTATUS(addAttribute(aParameters));
	return MStatus::kSuccess;
}


MStatus LSBufferReaderNode::deform( MDataBlock& datablock,
				MItGeometry& iter,
				const MMatrix& matrix,
				unsigned int multiIndex)
{
	MStatus status;
	MDataHandle indicesHandle = datablock.inputValue(LSBufferReaderNode::aIndices);
	if (!status)
		return status;
	MObject indicesDataObject = indicesHandle.data();
	if (indicesDataObject.isNull())
	{
		return MS::kFailure;
	}
	MFnIntArrayData indices(indicesDataObject);
	const unsigned int indicesNum = indices.length(&status);
	CHECK_MSTATUS(status);
	if (!status)
		return status;
	if((!status) || indicesNum==0)
		return MS::kFailure;
	unsigned int id = 0;
	positions.clear();
	MPointArray points;
	status = iter.allPositions(points);
	CHECK_MSTATUS(status);
	if (!status)
		return status;
	for (auto id = 0; id < indicesNum; ++id) {
		const unsigned int positionId = indices[id];
		const MPoint& point = points[positionId];
		positions.push_back(float(point[0]));
		positions.push_back(float(point[1]));
		positions.push_back(float(point[2]));
	}
	updateBuffer((const float*)positions.data(), positions.size());
	return status;
}

LSGeometryInfo* LSBufferReaderNode::getGeometryInfo()
{
	MStatus status;
	MObject node = thisMObject();
	MPlug geometryIOPlug(node, aParameters);
	if(geometryIOPlug.isConnected(&status))
	{
		MPlugArray geometryInfoPlugArray;
		geometryIOPlug.connectedTo(geometryInfoPlugArray, true, false, &status);
    	CHECK_MSTATUS(status);
		const unsigned int plugNum = geometryInfoPlugArray.length();
		if(plugNum>0)
		{
			MObject geometryInfoNode= geometryInfoPlugArray[0].node(&status);
			CHECK_MSTATUS(status);
			if(!geometryInfoNode.isNull())
			{
				MFnDependencyNode dagFn(geometryInfoNode, &status);
				CHECK_MSTATUS(status);
				MPxNode *pNode = dagFn.userNode(&status);
				CHECK_MSTATUS(status);
				LSGeometryInfo* pGPUReaderNode = dynamic_cast<LSGeometryInfo*>(pNode);
				return pGPUReaderNode;
			}
		}
	}
	return nullptr;
}
void LSBufferReaderNode::updateBuffer(const float* buffer, const size_t size)
{
	LSGeometryInfo* pGPUReaderNode = getGeometryInfo();
	if(pGPUReaderNode)
	{
		pGPUReaderNode->updateBuffer(buffer, size);
	}
}
