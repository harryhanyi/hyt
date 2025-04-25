#include "controller/miController.h"
#include "controller/miControllerDrawOverride.h"
#include "controller/miControllerManip.h"

#include "viewportPicker/miViewportPickerData.h"
#include "viewportPicker/miViewportPickerDrawOverride.h"
#include "viewportPicker/miViewportPickerManip.h"
#include "constraint/GeometryInfo.h"
#include "constraint/GeometryInfoCmd.h"
#include "constraint/GPUBufferReader.h"

#include <maya/MFnPlugin.h>
#include <maya/MGlobal.h>


#include "tensionNode/tensionNode.h"
#include "angleSliceSolver/angleSliceSolver.h"

MStatus initializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin(obj, "Mihoyo", "beta", "Any");
	status = plugin.registerNode( "angleSliceSolver", AngleSliceSolver::id, AngleSliceSolver::creator, AngleSliceSolver::initialize );
	if (!status)
	{
		status.perror("Failed to registerNode angleSliceSolver!");
		return status;
	}

	status = plugin.registerNode( "tensionNode", tensionNode::id, tensionNode::creator, tensionNode::initialize );
	if (!status)
	{
		status.perror("Failed to registerNode tensionNode!");
		return status;
	}

	status = plugin.registerNode("lsController",
								 LSController::sId,
								 &LSController::creator,
								 &LSController::initialize,
								 MPxNode::kLocatorNode,
								 &LSController::drawDbClassification);
	if (!status)
	{
		status.perror("Failed to registerNode");
		return status;
	}

	status = MHWRender::MDrawRegistry::registerDrawOverrideCreator(
		LSController::drawDbClassification,
		LSController::drawRegistrantId,
		LSControllerDrawOverride::Creator);
	if (!status)
	{
		status.perror("Failed to registerDrawOverrideCreator");
		return status;
	}

	status = plugin.registerNode(
		"lsViewportPicker",
		LSViewportPicker::id,
		&LSViewportPicker::creator,
		&LSViewportPicker::initialize,
		MPxNode::kLocatorNode,
		&LSViewportPicker::drawDbClassification);
	if (!status)
	{
		status.perror("Failed to registerNode");
		return status;
	}

	status = plugin.registerDisplayFilter("MHY_viewport_picker",
		"MHY Viewport Picker",
		LSViewportPicker::drawDbClassification);

	if (!status)
	{
		status.perror("Failed to register display filter for viewport picker");
		return status;
	}

	status = MHWRender::MDrawRegistry::registerDrawOverrideCreator(
		LSViewportPicker::drawDbClassification,
		LSViewportPicker::drawRegistrantId,
		LSViewportPickerDrawOverride::Creator);

	if (!status)
	{
		status.perror("Failed to registerDrawOverrideCreator");
		return status;
	}

#if MAYA_API_VERSION >= 20190000
	//https://around-the-corner.typepad.com/adn/2019/04/cached-playback-issues-and-their-workarounds.html
	const char *cacheEvaluatorRule = R"CACHE_EVAL_RULE(
from maya import cmds
cmds.cacheEvaluator(
    newFilter='nodeTypes',
    newFilterParam='types=+lsController',
    newAction='enableEvaluationCache'
)
)CACHE_EVAL_RULE";
	MGlobal::executePythonCommand(cacheEvaluatorRule);
#endif
	status = plugin.registerNode("lsGeometryInfo", LSGeometryInfo::sId, LSGeometryInfo::creator, LSGeometryInfo::initialize);
	if (!status)
	{
		status.perror("Failed to registerNode");
		return status;
	}
	status = plugin.registerNode("lsBufferReader", LSBufferReaderNode::id, LSBufferReaderNode::creator,
								 LSBufferReaderNode::initialize, MPxNode::kDeformerNode);
	if (!status)
	{
		status.perror("registerNode lsBufferReader");
		return status;
	}
	MString nodeClassName("lsBufferReader");
	MString registrantId("MHYAmerica");
	MGPUDeformerRegistry::registerGPUDeformerCreator(
		nodeClassName,
		registrantId,
		lsGPUBufferReader::getGPUDeformerInfo());

	MGPUDeformerRegistry::addConditionalAttribute(
		nodeClassName,
		registrantId,
		MPxDeformerNode::envelope);

	const char *resourcePathEnv = getenv("LSR_RESOURCE_PATH");
	if (resourcePathEnv != nullptr)
	{
		LSBufferReaderNode::pluginPath = resourcePathEnv;
		LSBufferReaderNode::pluginPath += "/OpenCL/";
	}
	else
	{
		LSBufferReaderNode::pluginPath = plugin.loadPath();
	}

	status = plugin.registerCommand("geometryInfoCmd", GeometryInfoCmd::creator, GeometryInfoCmd::cmdSyntax);
	if (!status)
	{
		status.perror("Failed to registerCommand GeometryInfoCmd!");
		return status;
	}

	status = plugin.registerCommand("lsControllerShapes", LSControllerInfoCmd::creator);
	if (!status)
	{
		status.perror("Failed to registerCommand lsControllerShapes!");
		return status;
	}
	return status;
}

MStatus uninitializePlugin(MObject obj)
{
	MStatus status;
	MFnPlugin plugin(obj);
    status = plugin.deregisterNode( AngleSliceSolver::id );
	if (!status)
	{
		status.perror("Failed to deregisterNode AngleSliceSolver!");
		return status;
	}
    status = plugin.deregisterNode( tensionNode::id );
	if (!status)
	{
		status.perror("Failed to deregisterNode tensionNode!");
		return status;
	}
	status = plugin.deregisterCommand("geometryInfoCmd");
	if (!status)
	{
		status.perror("Failed to deregisterCommand GeometryInfoCmd!");
		return status;
	}

	status = plugin.deregisterCommand("lsControllerShapes");
	if (!status)
	{
		status.perror("Failed to deregisterCommand lsControllerShapes!");
		return status;
	}

	status = plugin.deregisterNode(LSGeometryInfo::sId);
	if (!status)
	{
		status.perror("Failed to deregisterNode lsGeometryInfo");
		return status;
	}

	status = MHWRender::MDrawRegistry::deregisterDrawOverrideCreator(
		LSController::drawDbClassification,
		LSController::drawRegistrantId);
	if (!status)
	{
		status.perror("Failed to deregisterDrawOverrideCreator LSController");
		return status;
	}

	status = plugin.deregisterNode(LSBufferReaderNode::id);
	if (!status)
	{
		status.perror("Failed to deregisterNode LSBufferReaderNode");
		return status;
	}
	MString nodeClassName("lsBufferReader");
	MString registrantId("MHYAmerica");
	MGPUDeformerRegistry::deregisterGPUDeformerCreator(
		nodeClassName,
		registrantId);

	status = MDrawRegistry::deregisterGeometryOverrideCreator(
		LSViewportPicker::drawDbClassification,
		LSViewportPicker::drawRegistrantId);
	if (!status)
	{
		status.perror("Failed to deregisterNode GeometryOverrideCreator");
		return status;
	}
	status = plugin.deregisterNode(LSViewportPicker::id);
	if (!status)
	{
		status.perror("Failed to deregisterNode LSViewportPicker");
		return status;
	}

	status = plugin.deregisterDisplayFilter("LSR_viewport_picker");

	if (!status)
	{
		status.perror("Failed to deregister display filter for viewport picker");
		return status;
	}
	return status;
}
