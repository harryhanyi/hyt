#include "miViewportPickerDrawOverride.h"
#include "miViewportPickerData.h"

#include <maya/MFloatPointArray.h>
#include <maya/MUintArray.h>
#include <maya/MFnCamera.h>
#include <maya/MGlobal.h>
#include <stdio.h>
#include <math.h>
#include <algorithm>

#define PI 3.14159265

LSViewportPickerDrawOverride::LSViewportPickerDrawOverride(const MObject& obj)
    : MPxDrawOverride(obj, NULL, true)
{
    MStatus status;
    MFnDependencyNode node(obj, &status);
    fLsViewportPicker = status ? dynamic_cast<LSViewportPicker*>(node.userNode()) : NULL;
}
LSViewportPickerDrawOverride::~LSViewportPickerDrawOverride() {}


bool LSViewportPickerDrawOverride::isBounded(const MDagPath& /*objPath*/,
    const MDagPath& /*cameraPath*/) const
{
    return true;
}



bool LSViewportPickerDrawOverride::disableInternalBoundingBoxDraw() const
{
    return false;
}

MHWRender::DrawAPI LSViewportPickerDrawOverride::supportedDrawAPIs() const
{
    // this plugin supports both GL and DX
    return MHWRender::kAllDevices;
}
MUserData* LSViewportPickerDrawOverride::prepareForDraw(
    const MDagPath& objPath,
    const MDagPath& cameraPath,
    const MHWRender::MFrameContext& frameContext,
    MUserData* oldData)
{
    LSViewportPickerData* data = dynamic_cast<LSViewportPickerData*>(oldData);
    if (!data) {
        data = new LSViewportPickerData();
    }

    MStatus status;
    MObject lsViewportPickerNode = objPath.node(&status);

    // Use camera target msg attribute 
    data->fEnabled = true;
    {
        MPlug plug(lsViewportPickerNode, LSViewportPicker::aCameraTarget);
        MString cameraTargetsStr = plug.asString();
        MStringArray splitResult;
        cameraTargetsStr.split(';', splitResult);
        unsigned numCameras = splitResult.length();
        if (numCameras) {
            data->fEnabled = false;
        }
        for (unsigned i = 0; i < numCameras; i++) {
            if (splitResult[i] == cameraPath.partialPathName()) {
                data->fEnabled = true;
            }
        }
        if (!data -> fEnabled) {
            return data;
        }
    }

    if (status) {
        // Hard code it here. Not sure yet how to calculate it correctly.
        MMatrix worldMatrix = objPath.inclusiveMatrix();
        MTransformationMatrix tm(worldMatrix);
        double scale[3];
        tm.getScale(scale, MSpace::kObject);
        data->fScaleFactor = abs(scale[0]) + abs(scale[0]) + abs(scale[0]) / 3;

        // retrieve uiType
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aUIType);
            data->fUIType = (LSViewportPicker::EuiType)plug.asInt();
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aRotate);
            data->rotation = plug.asFloat();
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aSelectability);
            data->fSelectability = (MUIDrawManager::Selectability)plug.asInt();
        }
        // common attributes
        // retrieve color
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aColor);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            nData.getData(data->fColor.r, data->fColor.g, data->fColor.b);
        }

        // retrieve high light color
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aHighColor);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            nData.getData(data->fHColor.r, data->fHColor.g, data->fHColor.b);
        }
        // retrieve transparency
        if (fLsViewportPicker != NULL) {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aAlpha);
            fLsViewportPicker->alpha = plug.asFloat();

            data->fColor.a = fLsViewportPicker->alpha;
            data->fHColor.a = fLsViewportPicker->alpha;
        }
        // retrieve line width
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aLineWidth);
            data->fLineWidth = plug.asFloat();
        }
        // retrieve line style
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aLineStyle);
            data->fLineStyle = (MUIDrawManager::LineStyle)plug.asShort();
        }
        // retrieve filled flag
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aIsFilled);
            data->fIsFilled = plug.asBool();
        }
        {

            MFnCamera camerafn(cameraPath);
            data->fUpVector = camerafn.upDirection(MSpace::kWorld);
            data->fFaceVector = camerafn.viewDirection(MSpace::kWorld);

            MPlug plug(lsViewportPickerNode, LSViewportPicker::aPosition);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            double x, y;
            nData.getData(x, y);

            MPoint near, far, near_offset, far_offset;

            frameContext.viewportToWorld(x, y, near, far);

            frameContext.viewportToWorld(x+1, y, near_offset, far_offset);
            double offset_dist = near_offset.distanceTo(near);

            if (camerafn.isOrtho()) {
                // For some reason the viewport to world for orthographic camera is returning
                // A point behind the camera near plane. I have to calculate it manually
                // ((near+td)-Q).faceVector = 0
                // t = ((Q-near)).n/(d.faceVector)

                MMatrix cameraWorldMatrix = objPath.inclusiveMatrix();
                MTransformationMatrix tMatrix(cameraWorldMatrix);
                MVector Q = tMatrix.getTranslation(MSpace::kWorld);
                MVector d = far - near;
                double x = d * data->fFaceVector;
                if (x != 0) {
                    double t = ((Q - near) * (data->fFaceVector)) / x;
                    near = near + t * d;
                    MPlug owidthPlug = camerafn.findPlug("orthographicWidth", false);
                    float owith = owidthPlug.asFloat();

                    data->fScaleFactor = data->fScaleFactor/ offset_dist;

                }

            }
            else {

                data->fScaleFactor = data->fScaleFactor /20 / offset_dist;
            }
            near = near + (far - near).normal();


            MMatrix inverseMatrix = objPath.inclusiveMatrixInverse();

            data->fPosition = near * inverseMatrix;

            data->fFaceVector = data->fFaceVector * inverseMatrix;
            data->fUpVector = data->fUpVector * inverseMatrix;
        }

        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aText);
            data->fText = plug.asString();
        }
        // retrieve text font size
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextFontSize);
            data->fTextFontSize = std::max(plug.asInt(), 0);
        }
        // retrieve font face index
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aFontFaceName);
            data->fFontFaceIndex = (unsigned int)plug.asInt();
        }
        // retrieve text alignment
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextAlignment);
            data->fTextAlignment = (MUIDrawManager::TextAlignment)plug.asShort();
        }

        // retrieve text incline
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::eTextIncline);
            data->fTextIncline = plug.asInt();
        }
        // retrieve text weight
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextWeight);
            data->fTextWeight = plug.asInt();
        }
        // retrieve text stretch
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextStretch);
            data->fTextStretch = plug.asInt();
        }
        // retrieve text line
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextLine);
            data->fTextLine = plug.asInt();
        }
        // retrieve text box size
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextBoxSize);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            nData.getData(data->fTextBoxWidth, data->fTextBoxHeight);
        }
        // retrieve text box color
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextBoxColor);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            nData.getData(data->fTextBoxColor.r, data->fTextBoxColor.g, data->fTextBoxColor.b);
        }
        // retrieve text box transparency
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aTextBoxTransparency);
            data->fTextBoxColor.a = plug.asFloat();
        }
    }
    switch (data->fUIType)
    {
    case LSViewportPicker::kCircle:
    {
        // retrieve radius{
        MPlug plug(lsViewportPickerNode, LSViewportPicker::aRadius);
        data->fRadius = plug.asDouble() / data->fScaleFactor;
    }
    break;
    case LSViewportPicker::kRect:
    {
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aWidth);
            data->fWidth = plug.asDouble() / data->fScaleFactor;
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aHeight);
            data->fHeight = plug.asDouble() / data->fScaleFactor;
        }
    }
    break;
    case LSViewportPicker::kImage: {
        if (!init_image_data) {
            fLsViewportPicker->UpdateAlphaImageCache(fLsViewportPicker);
            init_image_data = true;
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aContainerTextColor);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            nData.getData(data->fCTColor.r, data->fCTColor.g, data->fCTColor.b);
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aWidth);
            data->fWidth = plug.asDouble();
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aHeight);
            data->fHeight = plug.asDouble();
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aPosition);
            MObject o = plug.asMObject();
            MFnNumericData nData(o);
            double x, y;
            double xOffset = data->fWidth / 2;
            double yOffset = data->fHeight / 2;
            nData.getData(x, y);
            data->fQuadVertex[0] = MFloatPoint(x - xOffset, y - yOffset, 0.0);
            data->fQuadVertex[1] = MFloatPoint(x - xOffset, y + yOffset, 0.0);
            data->fQuadVertex[2] = MFloatPoint(x + xOffset, y + yOffset, 0.0);
            data->fQuadVertex[3] = MFloatPoint(x + xOffset, y - yOffset, 0.0);
        }
        if (fLsViewportPicker != NULL) {
            data->fTexture = fLsViewportPicker->fTexture;
        }
    }
    break;
    default: {
        int uiIdx = data->fUIType - 3;
        data->fWireFrameList.clear();
        data->fShadedList.clear();

        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aWidth);
            data->fWidth = plug.asDouble();
        }
        {
            MPlug plug(lsViewportPickerNode, LSViewportPicker::aHeight);
            data->fHeight = plug.asDouble();
        }
        MFnCamera camerafn(cameraPath);
        data->fUpVector = camerafn.upDirection(MSpace::kWorld);
        data->fFaceVector = camerafn.viewDirection(MSpace::kWorld);
        bool isOrtho = camerafn.isOrtho();

        MPlug plug(lsViewportPickerNode, LSViewportPicker::aPosition);
        MObject o = plug.asMObject();
        MFnNumericData nData(o);
        double x, y;
        nData.getData(x, y);

        MMatrix inverseMatrix = objPath.inclusiveMatrixInverse();
        MMatrix cameraWorldMatrix = objPath.inclusiveMatrix();
        MTransformationMatrix tMatrix(cameraWorldMatrix);
        MVector Q = tMatrix.getTranslation(MSpace::kWorld);

        data->tmpCache.clear();
        
        castViewportVtxToWorld(
            fLsViewportPicker->shapeList[uiIdx].wireFrameData,
            frameContext,
            x,
            y,
            data,
            isOrtho,
            Q,
            inverseMatrix,
            data->fWireFrameList);

        if (data->fIsFilled) {
            castViewportVtxToWorld(
                fLsViewportPicker->shapeList[uiIdx].shadedData,
                frameContext,
                x,
                y,
                data,
                isOrtho,
                Q,
                inverseMatrix,
                data->fShadedList);
            }
        }
    break;
    }
    return data;
}

void LSViewportPickerDrawOverride::castViewportVtxToWorld(
    PickerShape::DrawUnit& viewPortVtxList,
    const MHWRender::MFrameContext& frameContext,
    double& x,
    double& y,
    LSViewportPickerData* data,
    bool& isOrtho,
    MVector& camPos,
    MMatrix& camInvMatrix,
    PickerShape::DrawUnit& worldVtxList) 
{
    float cos_v = cos(data->rotation * PI/180.0);
    float sin_v = sin(data->rotation * PI/180.0);

    MPoint near, far, near_offset, far_offset;
    for (auto& pointArray : viewPortVtxList) {
        MPointArray pntArray;
        for (int i = 0; i < pointArray.length(); i++) {
            // Use a cache map to memoize duplicated points
            LSViewportPickerData::pair currentPoint;
            currentPoint = std::make_pair(pointArray[i].x, pointArray[i].y);
            std::map<LSViewportPickerData::pair, MPoint>::iterator ii = data->tmpCache.find(currentPoint);
            if (ii != data->tmpCache.end()) {
                MPoint pnt(ii->second);
                pntArray.append(pnt);
                continue;
            }
            int offset_x = pointArray[i].x * 0.5 * data->fWidth;
            int offset_y = pointArray[i].y * 0.5 * data->fHeight;

            int rotated_x = cos_v * offset_x - sin_v * offset_y;
            int rotated_y = sin_v * offset_x + cos_v * offset_y;

            int t_x = x + rotated_x;
            int t_y = y + rotated_y;
            
            frameContext.viewportToWorld(t_x, t_y, near, far);
            double offset_dist = near_offset.distanceTo(near);

            if (isOrtho) {
                // For some reason the viewport to world for orthographic camera is returning
                // A point behind the camera near plane. I have to calculate it manually
                // ((near+td)-Q).faceVector = 0
                // t = ((Q-near)).n/(d.faceVector)
                MVector d = far - near;
                double dist = d * data->fFaceVector;
                if (dist != 0) {
                    double t = ((camPos - near) * data->fFaceVector) / dist;
                    near = near + t * d;
                }

            }
            near = near + (far - near).normal();
            MPoint cast_point = near * camInvMatrix;
            pntArray.append(cast_point);
            data->tmpCache[currentPoint] = cast_point;
        }
        worldVtxList.push_back(pntArray);
    }
}

void LSViewportPickerDrawOverride::addUIDrawables(
    const MDagPath& objPath,
    MHWRender::MUIDrawManager& drawManager,
    const MHWRender::MFrameContext& frameContext,
    const MUserData* data)
{
    const LSViewportPickerData* thisdata = dynamic_cast<const LSViewportPickerData*>(data);
    if (!thisdata) {
        return;
    }
    MStatus status;

    MHWRender::DisplayStatus displayStatus = MHWRender::MGeometryUtilities::displayStatus(objPath, &status);
    CHECK_MSTATUS(status);


    if (!thisdata->fEnabled) {
        return;
    }

    switch (thisdata->fUIType)
    {
    case LSViewportPicker::kRect:
    {
        drawManager.beginDrawable(thisdata->fSelectability);

        drawManager.beginDrawInXray();

        drawManager.setLineWidth(thisdata->fLineWidth);
        drawManager.setLineStyle(thisdata->fLineStyle);
        if (displayStatus != MHWRender::DisplayStatus::kLead && displayStatus != MHWRender::kActive)
        {
            drawManager.setColor(thisdata->fColor);
        }
        else {
            drawManager.setColor(thisdata->fHColor);
        }

        drawManager.rect(thisdata->fPosition, thisdata->fUpVector, thisdata->fFaceVector,
            thisdata->fWidth, thisdata->fHeight, thisdata->fIsFilled);
        
        drawManager.endDrawInXray();
        drawManager.endDrawable();
    
    }
    break;
    case LSViewportPicker::kCircle:
    {
        drawManager.beginDrawable(thisdata->fSelectability);
        drawManager.setLineWidth(thisdata->fLineWidth);
        drawManager.setLineStyle(thisdata->fLineStyle);
        if (displayStatus != MHWRender::DisplayStatus::kLead && displayStatus != MHWRender::kActive)
        {
            drawManager.setColor(thisdata->fColor);
        }
        else {
            drawManager.setColor(thisdata->fHColor);
        }
        drawManager.beginDrawInXray();
        drawManager.circle(thisdata->fPosition, thisdata->fFaceVector, thisdata->fRadius,
            thisdata->fIsFilled);
        drawManager.endDrawInXray();
        drawManager.endDrawable();
    }
    break;
    case LSViewportPicker::kImage:
    {
        if (thisdata->fTexture == NULL) {
            break;
        }
        drawManager.beginDrawable(MUIDrawManager::Selectability::kNonSelectable);
        drawManager.setLineWidth(thisdata->fLineWidth);
        drawManager.setLineStyle(thisdata->fLineStyle);
   
        MUIDrawManager::Primitive mode =
            thisdata->fIsFilled ? MUIDrawManager::kTriStrip : MUIDrawManager::kClosedLine;
        // prepare index

        //drawManager.beginDrawInXray();
        MPointArray position;
        for (int i = 0; i < 4; ++i) {
            position.append(thisdata->fQuadVertex[i]);
        }
        drawManager.setTexture(thisdata->fTexture);
        drawManager.setTextureMask(MHWRender::MBlendState::kRGBAChannels);

        drawManager.mesh2d(mode, position, 
            NULL, thisdata->fIsFilled ? &thisdata->fMeshIndex : NULL,
            &thisdata->fUvCoordinates);
        drawManager.setTexture(NULL);

        drawManager.setColor(thisdata->fCTColor);
        MStringArray pathArray;

        // Draw name space indicator
        objPath.partialPathName().split(':', pathArray);
        MPoint pnt = thisdata->fQuadVertex[1] + MPoint(150, -80);
        if (pathArray.length() > 1) {
            drawManager.setFontSize(24);
            drawManager.text2d(pnt, pathArray[0]);
        }
        drawManager.endDrawable();
        
    }
    break;
    default: {
        
        drawManager.beginDrawable(thisdata->fSelectability);
        drawManager.setLineWidth(thisdata->fLineWidth);
        drawManager.setLineStyle(thisdata->fLineStyle);

        if (displayStatus != MHWRender::DisplayStatus::kLead && displayStatus != MHWRender::kActive)
        {
            drawManager.setColor(thisdata->fColor);
        }
        else {
            drawManager.setColor(thisdata->fHColor);
        }
        drawManager.setDepthPriority(1);
        drawManager.beginDrawInXray();

        for (auto& shape : thisdata->fWireFrameList) {
            drawManager.mesh(MUIDrawManager::kLines, shape);
        }
        if(thisdata->fIsFilled){
            for (auto& shape : thisdata->fShadedList) {
                drawManager.mesh(MUIDrawManager::kTriangles, shape);
            }
        }
        drawManager.endDrawInXray();
        drawManager.endDrawable();

    }
        break;
    }
}