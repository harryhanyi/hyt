#include "miController.h"
#include "miControllerDrawOverride.h"
#include "miControllerDrawData.h"
#include <maya/MFnDagNode.h>

LSControllerDrawOverride::LSControllerDrawOverride(const MObject& obj)
	: MHWRender::MPxDrawOverride(obj, NULL, false)
	, lsController(obj)
{
	fModelEditorChangedCbId = MEventMessage::addEventCallback(
		"modelEditorChanged", OnModelEditorChanged, this);
}

LSControllerDrawOverride::~LSControllerDrawOverride()
{
	if (fModelEditorChangedCbId != 0)
	{
		MMessage::removeCallback(fModelEditorChangedCbId);
		fModelEditorChangedCbId = 0;
	}
}

void LSControllerDrawOverride::OnModelEditorChanged(void *clientData)
{
	// Mark the node as being dirty so that it can update on display mode switch,
	// e.g. between wireframe and shaded.
	LSControllerDrawOverride *ovr = static_cast<LSControllerDrawOverride*>(clientData);
	if (ovr) MHWRender::MRenderer::setGeometryDrawDirty(ovr->lsController);
}

MHWRender::DrawAPI LSControllerDrawOverride::supportedDrawAPIs() const
{
	return MHWRender::kAllDevices;
}

bool LSControllerDrawOverride::isBounded(const MDagPath& /*objPath*/,
									  const MDagPath& /*cameraPath*/) const
{
	return true;
}

MBoundingBox LSControllerDrawOverride::boundingBox(
	const MDagPath& objPath,
	const MDagPath& cameraPath) const
{
	LSController* pController = LSController::getController(objPath);
	if (pController != nullptr) {
		MBoundingBox bbox = pController->boundingBox();
		MPoint zeroPoint(0.0, 0.0, 0.0);
		//prepareForDraw is called after boundingBox. So when bounding box is all zeroes.
		//need initialize boundingbox. 
		//TODO: This logic need revisit later.
		//1. Here actually initialized LSControllerDrawData twice.
		//   once in prepareForDraw, the other in boundingbox.
		if (bbox.min() == zeroPoint && bbox.max() == zeroPoint)
		{
			LSControllerDrawData constrollerdata;
			constrollerdata.update(objPath);
			bbox = pController->boundingBox();
		}
		LSControllerDrawOverride* nonConstThis = const_cast<LSControllerDrawOverride*>(this);
		nonConstThis->mCurrentBoundingBox = bbox;
	}
	return mCurrentBoundingBox;
}

bool LSControllerDrawOverride::disableInternalBoundingBoxDraw() const
{
	return false;
}

MUserData* LSControllerDrawOverride::prepareForDraw(
	const MDagPath& dagPath,
	const MDagPath& cameraPath,
	const MHWRender::MFrameContext& frameContext,
	MUserData* oldData)
{
	MStatus status;
	// Retrieve data cache (create if does not exist)
	LSControllerDrawData* data = dynamic_cast<LSControllerDrawData*>(oldData);
	if (!data)
	{
		data = new LSControllerDrawData();
	}
	data->update(dagPath);
	return data;
}
void LSControllerDrawOverride::_addUIDrawables(const MDagPath& dagPath,
	MHWRender::MUIDrawManager& drawManager,
	LSControllerDrawData* pControllerData)
{
	//draw lines.
	MStatus status;
	MHWRender::DisplayStatus displayStatus = MHWRender::MGeometryUtilities::displayStatus(dagPath, &status);
	CHECK_MSTATUS(status);
	drawManager.setColor(MHWRender::MGeometryUtilities::wireframeColor(dagPath));
	LSControllerDrawData::DrawData::List lineShapes = pControllerData->fLines;
	int linesShapeNum = int(lineShapes.size());
	for (int i = 0; i < linesShapeNum; ++i)
	{
		if (displayStatus != MHWRender::DisplayStatus::kLead && displayStatus != MHWRender::kActive)
		{
			drawManager.setColor(pControllerData->fColor);
		}
		drawManager.setDepthPriority(5);
		drawManager.mesh(MHWRender::MUIDrawManager::kLines, lineShapes[i].points);
	}
	LSControllerDrawData::DrawData::List triangleShapes = pControllerData->fTriangles;
	int triangleShapeNum = int(triangleShapes.size());
	for (int i = 0; i < triangleShapeNum; ++i)
	{
		if (displayStatus != MHWRender::DisplayStatus::kLead && displayStatus != MHWRender::kActive)
		{
			drawManager.setColor(pControllerData->fColor);
		}
		drawManager.setDepthPriority(5);
		drawManager.mesh(MHWRender::MUIDrawManager::kTriangles, triangleShapes[i].points);
	}
	//draw text.
	if (pControllerData->fText.length() != 0)
	{
		MPoint position(0.0, 0.0, 0.0); // Position of the text
		LSController* pController = LSController::getController(dagPath);
		if (pController != nullptr) {
			position = pController->getTextPosition();
		}
		MColor textColor(0.1f, 0.8f, 0.8f, 1.0f); // Text color
		drawManager.setColor(pControllerData->fColor);
		drawManager.setFontSize(MHWRender::MUIDrawManager::kSmallFontSize);
		drawManager.text(position, pControllerData->fText, MHWRender::MUIDrawManager::kCenter);
	}
}

void LSControllerDrawOverride::addUIDrawables(const MDagPath& dagPath,
	MHWRender::MUIDrawManager& drawManager,
	const MHWRender::MFrameContext& frameContext,
	const MUserData* data)
{
	LSController* pController = LSController::getController(dagPath);
	if (!pController->isDrawableMode()) {
		return;
	}
	LSControllerDrawData* pControllerData = (LSControllerDrawData*)data;
	drawManager.beginDrawable();
	_addUIDrawables(dagPath, drawManager, pControllerData);
	drawManager.endDrawable();
	if (pController->isXrayMode())
	{
		drawManager.beginDrawInXray();
		_addUIDrawables(dagPath, drawManager, pControllerData);
		drawManager.endDrawInXray();
	}
}

