#include "miViewportPickerData.h"


MStringArray LSViewportPickerData::fFontList;
LSViewportPickerData::LSViewportPickerData() : MUserData(false)
, fUIType(LSViewportPicker::kCircle)
, fColor(1.0f, 0.0f, 0.0f, 1.0f)
, fHColor(1.0f, 1.0f, 1.0f, 1.0f)
, fCTColor(1.0f, 1.0f, 1.0f, 1.0f)
, fLineWidth(2.0f)
, fLineStyle(MUIDrawManager::kSolid)
, fIsFilled(false)
, rotation(0.0f)
, fPosition(0.0f, 0.0, 0.001)
, fRadius(1.0)
, fWidth(1.0)
, fHeight(1.0)
, fScaleFactor(1.0)
, fFaceVector(0, 0, 1)
, fUpVector(0, 1, 0)
// text
, fText("")
, fTextFontSize(MUIDrawManager::kDefaultFontSize)
, fFontFaceIndex(0)
, fTextAlignment(MUIDrawManager::kLeft)
, fTextIncline(MUIDrawManager::kInclineNormal)
, fTextWeight(MUIDrawManager::kWeightBold)
, fTextStretch(MUIDrawManager::kStretchUnstretched)
, fTextLine(0)
, fTextBoxWidth(0)
, fTextBoxHeight(0)
, fTextBoxColor(0.0f, 1.0f, 1.0f, 1.0f)
{
    // quad
    fQuadVertex[0] = MFloatPoint(0.0, 0.0, 0.0);
    fQuadVertex[1] = MFloatPoint(1.0, 0.0, 0.0);
    fQuadVertex[2] = MFloatPoint(1.0, 1.0, 0.0);
    fQuadVertex[3] = MFloatPoint(0.0, 1.0, 0.0);

    fUvCoordinates.append(MPoint(0.0, 0.0, 0.0));
    fUvCoordinates.append(MPoint(0.0, 1.0, 0.0));
    fUvCoordinates.append(MPoint(1.0, 1.0, 0.0));
    fUvCoordinates.append(MPoint(1.0, 0.0, 0.0));

    fMeshIndex.append(0);
    fMeshIndex.append(1);
    fMeshIndex.append(3);
    fMeshIndex.append(2);
}