#pragma once
#include "BufferReaderNode.h"

class lsGPUBufferReader : public MPxGPUDeformer
{
public:
	// Virtual methods from MPxGPUDeformer
	lsGPUBufferReader();
	~lsGPUBufferReader() override;

	MPxGPUDeformer::DeformerStatus evaluate(MDataBlock& datablock, const MEvaluationNode& evaluationNode, const MPlug& outputPlug, const MGPUDeformerData& inputData, MGPUDeformerData& outputData) override;
	void terminate() override;

	static MGPUDeformerRegistrationInfo* getGPUDeformerInfo();
	static bool validateNodeInGraph(MDataBlock& datablock, const MEvaluationNode&, const MPlug& plug, MStringArray* messages);
	static bool validateNodeValues(MDataBlock& datablock, const MEvaluationNode&, const MPlug& plug, MStringArray* messages);

private:
	// helper methods
	void extractParameters(MDataBlock& datablock, const MEvaluationNode& evaluationNode, const MObject node);
	MStatus updatePositions(const MObject &node);
	unsigned int affectCount() const;
	unsigned int fullCount() const;
	LSBufferReaderNode* getDeformerNode(const MObject &node);
	cl_int enqueueComputeData(MAutoCLEvent& syncEvent, const MGPUDeformerBuffer& inputPositions);
	cl_int enqueueReadBuffer(const MObject &node, MAutoCLEvent& syncEvent, const MGPUDeformerBuffer& inputPositions);
	// holds the data for which verts are affected
	MPointArray points;

	// Storage for data on the GPU
	MAutoCLMem fCLParameterIndices;
    MAutoCLMem output_CLMemPtr;
	size_t indexBufferSize;
	size_t pointsBufferSize;
	size_t indicesNum;
	// Kernel
	MAutoCLKernel fKernel;
    std::vector<float> positions;
    cl_mem output_CLMem=0;
};

class offsetNodeGPUDeformerInfo : public MGPUDeformerRegistrationInfo
{
public:
	offsetNodeGPUDeformerInfo() {}
	~offsetNodeGPUDeformerInfo() override{}

	MPxGPUDeformer* createGPUDeformer() override
	{
		return new lsGPUBufferReader();
	}

	bool validateNodeInGraph(MDataBlock& block, const MEvaluationNode& evaluationNode, const MPlug& plug, MStringArray* messages) override
	{
		return lsGPUBufferReader::validateNodeInGraph(block, evaluationNode, plug, messages);
	}

	bool validateNodeValues(MDataBlock& block, const MEvaluationNode& evaluationNode, const MPlug& plug, MStringArray* messages) override
	{
		return lsGPUBufferReader::validateNodeValues(block, evaluationNode, plug, messages);
	}
};
