#pragma once

#include <maya/MEventMessage.h>
// Viewport 2.0
#include <maya/MPxDrawOverride.h>
#include <maya/MHWGeometryUtilities.h>

class LSControllerDrawOverride : public MHWRender::MPxDrawOverride
{
public:
	static MHWRender::MPxDrawOverride* Creator(const MObject& obj)
	{
		return new LSControllerDrawOverride(obj);
	}

	~LSControllerDrawOverride() override;

	MHWRender::DrawAPI supportedDrawAPIs() const override;

	bool isBounded(
		const MDagPath& objPath,
		const MDagPath& cameraPath) const override;

	MBoundingBox boundingBox(
		const MDagPath& objPath,
		const MDagPath& cameraPath) const override;

	bool disableInternalBoundingBoxDraw() const override;

	MUserData* prepareForDraw(
		const MDagPath& objPath,
		const MDagPath& cameraPath,
		const MHWRender::MFrameContext& frameContext,
		MUserData* oldData) override;

	bool hasUIDrawables() const override { return true; }

	void addUIDrawables(
		const MDagPath& objPath,
		MHWRender::MUIDrawManager& drawManager,
		const MHWRender::MFrameContext& frameContext,
		const MUserData* data) override;
protected:
	MBoundingBox mCurrentBoundingBox;
	MCallbackId fModelEditorChangedCbId;
	MObject lsController;
private:
	LSControllerDrawOverride(const MObject& obj);
	static void OnModelEditorChanged(void *clientData);
	void _addUIDrawables(const MDagPath& dagPath,
		MHWRender::MUIDrawManager& drawManager,
		LSControllerDrawData* pControllerData);
};
