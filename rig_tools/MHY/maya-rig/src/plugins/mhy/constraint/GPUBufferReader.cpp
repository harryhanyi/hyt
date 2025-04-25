#include "GPUBufferReader.h"
#include <maya/MFnIntArrayData.h>
// the GPU override implementation of the offsetNode
//

MGPUDeformerRegistrationInfo *lsGPUBufferReader::getGPUDeformerInfo()
{
	static offsetNodeGPUDeformerInfo theOne;
	return &theOne;
}

lsGPUBufferReader::lsGPUBufferReader()
	: indicesNum(0), indexBufferSize(0), pointsBufferSize(0)
{
	// Remember the ctor must be fast.  No heavy work should be done here.
	// Maya may allocate one of these and then never use it.
}

lsGPUBufferReader::~lsGPUBufferReader()
{
	terminate();
}

/* static */
bool lsGPUBufferReader::validateNodeInGraph(MDataBlock &datablock, const MEvaluationNode &evaluationNode, const MPlug &plug, MStringArray *messages)
{
	// lsGPUBufferReader supports everything on the offset node except envelope
	// envelope is handled in validateNodeValues because we support some values
	// but not others.
	return true;
}

/* static */
bool lsGPUBufferReader::validateNodeValues(MDataBlock &datablock, const MEvaluationNode &evaluationNode, const MPlug &plug, MStringArray *messages)
{
	MObject node = plug.node();
	MFnDependencyNode fnNode(node);

	// Now that I know the envelope value is not changing, check to see if it is 1.0f
	MPlug envelopePlug(node, MPxDeformerNode::envelope);
	MDataHandle envData;
	envelopePlug.getValue(envData);
	if (envData.asFloat() != 1.0f)
	{
		MOpenCLInfo::appendMessage(messages, "Offset %s not supported by deformer evaluator because envelope is not exactly 1.0.", fnNode.name().asChar());
		return false;
	}

	return true;
}

cl_int lsGPUBufferReader::enqueueComputeData(
	MAutoCLEvent &syncEvent,
	const MGPUDeformerBuffer &inputPositions)
{
	cl_int err = CL_SUCCESS;
	MAutoCLEvent syncInputEvent = syncEvent;
	syncEvent = MAutoCLEvent();
	// Set all of our kernel parameters.  Input buffer and output buffer may be changing every frame
	// so always set them.
	unsigned int parameterId = 0;
	err = clSetKernelArg(fKernel.get(), parameterId++, sizeof(cl_mem), (void *)output_CLMemPtr.getReadOnlyRef());
	MOpenCLInfo::checkCLErrorStatus(err);
	err = clSetKernelArg(fKernel.get(), parameterId++, sizeof(cl_mem), (void *)inputPositions.buffer().getReadOnlyRef());
	MOpenCLInfo::checkCLErrorStatus(err);
	err = clSetKernelArg(fKernel.get(), parameterId++, sizeof(cl_mem), (void *)fCLParameterIndices.getReadOnlyRef());
	MOpenCLInfo::checkCLErrorStatus(err);
	err = clSetKernelArg(fKernel.get(), parameterId++, sizeof(cl_uint), (void *)&indicesNum);
	MOpenCLInfo::checkCLErrorStatus(err);

	// Figure out a good work group size for our kernel.
	size_t workGroupSize;
	size_t retSize;
	err = clGetKernelWorkGroupInfo(
		fKernel.get(),
		MOpenCLInfo::getOpenCLDeviceId(),
		CL_KERNEL_WORK_GROUP_SIZE,
		sizeof(size_t),
		&workGroupSize,
		&retSize);
	MOpenCLInfo::checkCLErrorStatus(err);

	size_t localWorkSize = 256;
	if (retSize > 0)
		localWorkSize = workGroupSize;
	size_t globalWorkSize = (localWorkSize - indicesNum % localWorkSize) + indicesNum; // global work size must be a multiple of localWorkSize

	// run the kernel
	MAutoCLEvent kernelFinishedEvent;
	// err = clEnqueueNDRangeKernel(
	// 	MOpenCLInfo::getMayaDefaultOpenCLCommandQueue(),
	// 	fKernel.get(),
	// 	1,
	// 	NULL,
	// 	&globalWorkSize,
	// 	&localWorkSize,
	// 	eventList.size(),
	// 	eventList.array(),
	// 	syncEvent.getReferenceForAssignment());

	// run the kernel
	err = clEnqueueNDRangeKernel(
		MOpenCLInfo::getMayaDefaultOpenCLCommandQueue(),
		fKernel.get(),
		1,
		NULL,
		&globalWorkSize,
		&localWorkSize,
		1,
		syncInputEvent.getReadOnlyRef(),
		syncEvent.getReferenceForAssignment());

	MOpenCLInfo::checkCLErrorStatus(err);
	return err;
}

cl_int lsGPUBufferReader::enqueueReadBuffer(const MObject &node,
											MAutoCLEvent &syncEvent,
											const MGPUDeformerBuffer &inputPositions)
{
	cl_int err = CL_SUCCESS;

	MAutoCLEvent syncoutputEvent = syncEvent;
	const size_t fullVertBufSize = indicesNum * sizeof(float) * 3;
	err = clEnqueueReadBuffer(
		MOpenCLInfo::getMayaDefaultOpenCLCommandQueue(),
		output_CLMemPtr.get(),
		CL_FALSE,		 //blocking_read
		0,				 //offset
		fullVertBufSize, //The size in bytes of data being read.
		positions.data(),
		1,
		syncoutputEvent.getReadOnlyRef(),
		syncEvent.getReferenceForAssignment());
	MOpenCLInfo::checkCLErrorStatus(err);
	clWaitForEvents(1, syncEvent.getReferenceForAssignment());
	updatePositions(node);
	return err;
}

LSBufferReaderNode *lsGPUBufferReader::getDeformerNode(const MObject &node)
{
	MStatus status;
	MFnDependencyNode dagFn(node, &status);
	CHECK_MSTATUS(status);
	MPxNode *pNode = dagFn.userNode(&status);
	CHECK_MSTATUS(status);
	return dynamic_cast<LSBufferReaderNode *>(pNode);
}

MStatus lsGPUBufferReader::updatePositions(const MObject &node)
{
	LSBufferReaderNode *pGPUReaderNode = getDeformerNode(node);
	if (pGPUReaderNode)
	{
		pGPUReaderNode->updateBuffer((float *)positions.data(), indicesNum * 3);
	}
	return MStatus::kSuccess;
}

MPxGPUDeformer::DeformerStatus lsGPUBufferReader::evaluate(
	MDataBlock &datablock,				   // data block for "this" node
	const MEvaluationNode &evaluationNode, // evaluation node representing "this" node
	const MPlug &plug,					   // the multi index we're working on.  There will be a separate instance created per multi index
	const MGPUDeformerData &inputData,	   // the input data provided by Maya or other upstream GPU Deformers
	MGPUDeformerData &outputData		   // the output data to be passed to the rendering system or other downstream GPU Deformers
)
{
	const MGPUDeformerBuffer inputPositions = inputData.getBuffer(MPxGPUDeformer::sPositionsName());
	if (!inputPositions.isValid())
		return MPxGPUDeformer::kDeformerFailure;
	outputData.setBuffer(inputPositions);
	MObject node = plug.node();
	extractParameters(datablock, evaluationNode, node);
	if (positions.empty())
	{
		return MPxGPUDeformer::kDeformerSuccess;
	}

	// Now that all the data we care about is on the GPU, setup and run the OpenCL Kernel
	if (!fKernel.get())
	{
		MString openCLKernelFile = LSBufferReaderNode::pluginPath + "/geometryFeedback.cl";
		MString openCLKernelName("geometryFeedback");
		fKernel = MOpenCLInfo::getOpenCLKernel(openCLKernelFile, openCLKernelName);
		if (!fKernel)
			return MPxGPUDeformer::kDeformerFailure;
	}

	MAutoCLEvent syncEvent = inputPositions.bufferReadyEvent();
	cl_int err = CL_SUCCESS;
	err = enqueueComputeData(syncEvent, inputPositions);
	if (err != CL_SUCCESS)
		return MPxGPUDeformer::kDeformerFailure;
	err = enqueueReadBuffer(node, syncEvent, inputPositions);
	if (err != CL_SUCCESS)
		return MPxGPUDeformer::kDeformerFailure;
	return MPxGPUDeformer::kDeformerSuccess;
}

void lsGPUBufferReader::terminate()
{
	MHWRender::MRenderer::theRenderer()->releaseGPUMemory(indexBufferSize);
	fCLParameterIndices.reset();
	MHWRender::MRenderer::theRenderer()->releaseGPUMemory(pointsBufferSize);
	output_CLMemPtr.reset();
	MOpenCLInfo::releaseOpenCLKernel(fKernel);
	fKernel.reset();
}

void lsGPUBufferReader::extractParameters(MDataBlock &datablock, const MEvaluationNode &evaluationNode, const MObject node)
{
	// if we've already got a weight array and it is not changing then don't bother copying it
	// to the GPU again

	// Note that right now hasAttributeBeenModified takes an attribute, so if any element in the multi is changing we think it is dirty...
	// To avoid false dirty issues here you'd need to only use one element of the MPxDeformerNode::input multi attribute for each
	// offset node.
	if (fCLParameterIndices.get() &&
		output_CLMemPtr.get() &&
		!MPxGPUDeformer::hasAttributeBeenModified(evaluationNode, LSBufferReaderNode::aParameters) &&
		!MPxGPUDeformer::hasAttributeBeenModified(evaluationNode, LSBufferReaderNode::aIndices))
	{
		return;
	}

	// Two possibilities: we could have a sparse array in indices[multiIndex] or there could be nothing in indices[multiIndex].
	// if nothing is there then all the weights at 1.0f.

	// Get a handle to the weight array we want.
	MStatus status;
	MDataHandle parameterStructure = datablock.inputValue(LSBufferReaderNode::aParameters, &status);
	if (!status)
		return;
	MDataHandle indicesHandle = datablock.inputValue(LSBufferReaderNode::aIndices);
	if (!status)
		return;

	MObject indicesDataObject = indicesHandle.data();
	if (indicesDataObject.isNull())
	{
		return;
	}
	MFnIntArrayData indices(indicesDataObject);
	indicesNum = indices.length();
	if ((!status) || indicesNum == 0)
		return;
	positions.resize(indicesNum * 3);
	// Maya might do some tricky stuff like not store the weight array at all for certain weight
	// values so we can't count on an array existing in the indices.  For the OpenCL Kernel
	// we want an array with one weight in it per vertex, we need to build it carefully here.

	if (!fCLParameterIndices.isNull() && indexBufferSize < indicesNum * sizeof(int))
	{
		MHWRender::MRenderer::theRenderer()->releaseGPUMemory(indexBufferSize);
		fCLParameterIndices.reset();
		indexBufferSize = 0;
	}
	if (!output_CLMemPtr.isNull() && pointsBufferSize < 3 * indicesNum * sizeof(int))
	{
		MHWRender::MRenderer::theRenderer()->releaseGPUMemory(pointsBufferSize);
		output_CLMemPtr.reset();
		pointsBufferSize = 0;
	}
	void *pTemp = (void *)(&indices.array()[0]);
	// Two possibilities, we could be updating an existing OpenCL buffer or allocating a new one.
	cl_int err = CL_SUCCESS;
	if (fCLParameterIndices.isNull())
	{
		indexBufferSize = indicesNum * sizeof(int);
		MHWRender::MRenderer::theRenderer()->holdGPUMemory(indexBufferSize);
		fCLParameterIndices.attach(clCreateBuffer(MOpenCLInfo::getOpenCLContext(), CL_MEM_COPY_HOST_PTR | CL_MEM_READ_ONLY, indexBufferSize, (void *)pTemp, &err));
		MOpenCLInfo::checkCLErrorStatus(err);
	}
	else
	{
		// I use a blocking write here, non-blocking could be faster...  need to manage the lifetime of temp, and have the kernel wait until the write finishes before running
		// I'm also assuming that the weight buffer is not growing.
		err = clEnqueueWriteBuffer(MOpenCLInfo::getMayaDefaultOpenCLCommandQueue(), fCLParameterIndices.get(), CL_TRUE, 0, indexBufferSize, (void *)pTemp, 0, NULL, NULL);
	}

	if (output_CLMemPtr.isNull())
	{
		pointsBufferSize = 3 * indicesNum * sizeof(int);
		MHWRender::MRenderer::theRenderer()->holdGPUMemory(pointsBufferSize);
		output_CLMemPtr.attach(clCreateBuffer(MOpenCLInfo::getOpenCLContext(), CL_MEM_WRITE_ONLY, pointsBufferSize, nullptr, &err));
		MOpenCLInfo::checkCLErrorStatus(err);
	}
}
