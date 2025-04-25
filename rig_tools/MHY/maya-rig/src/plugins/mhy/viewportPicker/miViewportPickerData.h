#include <maya/MUserData.h>
#include <maya/MPxDrawOverride.h>
#include <maya/MPointArray.h>
#include <maya/MUintArray.h>
#include "miViewportPicker.h"

#ifndef LSVIEWPORTPICKERDATA_H_
#define LSVIEWPORTPICKERDATA_H_

class LSViewportPickerData : public MUserData
{
public:
    LSViewportPickerData();
    ~LSViewportPickerData() override {};
    bool fEnabled=false;
    LSViewportPicker::EuiType fUIType;
    MColor fColor;
    MColor fHColor;
    MColor fCTColor;

    LSViewportPicker::EuiType fLimitType;

    float fLineWidth;
    MUIDrawManager::LineStyle fLineStyle;
    bool fIsFilled;

    // Image arguments
    MHWRender::MTexture* fTexture = NULL;
    MUintArray fMeshIndex;
    MPointArray fUvCoordinates;

    MUIDrawManager::Selectability fSelectability;
    float fRadius;
    double fWidth;
    double fHeight;
    double fScaleFactor;
    MPoint fPosition;
    float rotation;
    MVector fFaceVector;
    MVector fUpVector;
    // quad
    MFloatPoint fQuadVertex[4];

    // text
    MString fText;
    unsigned int fTextFontSize;
    unsigned int fFontFaceIndex;
    static MStringArray fFontList;
    MUIDrawManager::TextAlignment fTextAlignment;
    int fTextIncline;
    int fTextWeight;
    int fTextStretch;
    int fTextLine;
    int fTextBoxWidth;
    int fTextBoxHeight;
    MColor fTextBoxColor;

    PickerShape::DrawUnit fWireFrameList;
    PickerShape::DrawUnit fShadedList;
    typedef std::pair<double, double> pair;
    std::map <pair, MPoint> tmpCache;
};

#endif
