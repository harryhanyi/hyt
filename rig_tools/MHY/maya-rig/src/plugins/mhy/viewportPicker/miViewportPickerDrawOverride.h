#include <maya/MPxDrawOverride.h>
#include <maya/MHWGeometryUtilities.h>
#include <maya/MPxLocatorNode.h>
#include <maya/MSelectInfo.h>

#include "miViewportPicker.h"
#include "miViewportPickerData.h"


#ifndef LSVIEWPORTPICKERDRAWOVERRIDE_H_
#define LSVIEWPORTPICKERDRAWOVERRIDE_H_

class LSViewportPickerDrawOverride : public MPxDrawOverride
{
public:
    static MPxDrawOverride* Creator(const MObject& obj)
    {
        return new LSViewportPickerDrawOverride(obj);
    }
    ~LSViewportPickerDrawOverride() override;
    MHWRender::DrawAPI supportedDrawAPIs() const override;
    MUserData* prepareForDraw(
        const MDagPath& objPath,
        const MDagPath& cameraPath,
        const MFrameContext& frameContext,
        MUserData* oldData) override;
    bool hasUIDrawables() const override { return true; }
    void addUIDrawables(
        const MDagPath& objPath,
        MHWRender::MUIDrawManager& drawManager,
        const MHWRender::MFrameContext& frameContext,
        const MUserData* data) override;

    bool disableInternalBoundingBoxDraw() const override;
    bool isBounded(
        const MDagPath& objPath,
        const MDagPath& cameraPath) const override;
private:
    LSViewportPicker* fLsViewportPicker;
    LSViewportPickerDrawOverride(const MObject& obj);
    void castViewportVtxToWorld(
        PickerShape::DrawUnit& viewPortVtxList,
        const MHWRender::MFrameContext& frameContext,
        double& x,
        double& y,
        LSViewportPickerData* data,
        bool& isOrtho,
        MVector& camPos,
        MMatrix& camInvMatrix,
        PickerShape::DrawUnit& worldVtxList);
    bool init_image_data = false;


};

#endif
