#include <maya/MPxLocatorNode.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnMessageAttribute.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnStringData.h>
#include <maya/MFnPointArrayData.h>
#include <maya/MPointArray.h>
#include <maya/MFloatPointArray.h>
#include <maya/MUintArray.h>
#include <maya/MFnDagNode.h>
#include <maya/MHWGeometryUtilities.h>
#include <maya/MTextureManager.h>
#include <maya/MPxManipContainer.h>


// Viewport 2.0 includes
#include <maya/MDrawRegistry.h>
#include <maya/MPxDrawOverride.h>
#include <maya/MUserData.h>
#include <algorithm>
#include <maya/MGlobal.h>

#include <filesystem>
#include <fstream>
#include <json/json.h>
#include <iostream>
#include <string>

#include "miViewportPicker.h"
#include "miViewportPickerData.h"


MObject LSViewportPicker::aUIType;
MObject LSViewportPicker::aSelectability;
MObject LSViewportPicker::aCameraTarget;

MObject LSViewportPicker::aColor;
MObject LSViewportPicker::aContainerTextColor;
MObject LSViewportPicker::aHighColor;
MObject LSViewportPicker::aAlpha;
MObject LSViewportPicker::aPosition;
MObject LSViewportPicker::aPickerLocalScale;

MObject LSViewportPicker::aLimitWidget;
MObject LSViewportPicker::aLimitInput;
MObject LSViewportPicker::aLimitRange;
MObject LSViewportPicker::aLimitWidgetSize;

MObject LSViewportPicker::aLineWidth;
MObject LSViewportPicker::aLineStyle;
MObject LSViewportPicker::aIsFilled;
MObject LSViewportPicker::aTexturePath;
MObject LSViewportPicker::aRadius;
MObject LSViewportPicker::aWidth;
MObject LSViewportPicker::aHeight;
MObject LSViewportPicker::aRotate;

MObject LSViewportPicker::aTextAlignment;
MObject LSViewportPicker::eTextIncline;
MObject LSViewportPicker::aTextWeight;
MObject LSViewportPicker::aTextStretch;
MObject LSViewportPicker::aTextLine;
MObject LSViewportPicker::aTextBoxSize;
MObject LSViewportPicker::aText;
MObject LSViewportPicker::aTextBoxColor;
MObject LSViewportPicker::aTextBoxTransparency;
MObject LSViewportPicker::aTextFontSize;
MObject LSViewportPicker::aFontFaceName;
MTypeId LSViewportPicker::id(0x001357c4);
LSViewportPicker::ShapeList LSViewportPicker::shapeList;


MString    LSViewportPicker::drawDbClassification("drawdb/geometry/miViewportPicker");
MString    LSViewportPicker::drawRegistrantId("lsViewportPickerPlugin");


PickerShape::PickerShape(const char* name) : name(name) {}

bool PickerShape::loadShape(const Json::Value& jsonValue)
{
    bool result = true;
    auto shapes = jsonValue["shapes"];
    if (shapes.isArray())
    {
        for (auto shape : shapes)
        {
            auto wireframe = shape["wireframe"];
            MPointArray wireVtx;
            if (!wireframe.isNull())
            {

                if (!loadVertices(wireVtx, wireframe))
                {
                    return false;
                }
                if (wireVtx.length() != 0)
                {
                    wireFrameData.push_back(wireVtx);
                }
            }

            auto shaded = shape["shaded"];
            MPointArray shadedVtx;
            if (!shaded.isNull())
            {

                if (!loadVertices(shadedVtx, shaded))
                {
                    return false;
                }
                if (shadedVtx.length() != 0)
                {
                    shadedData.push_back(shadedVtx);
                }
            }
        }
    }
    return result;
}

bool PickerShape::loadFloat3(MPoint& value, const Json::Value& jsonValue)
{
    if (!jsonValue.isArray())
    {
        return false;
    }
    if (jsonValue[0].isNumeric() && jsonValue[1].isNumeric())
    {
        value = MPoint(jsonValue[0].asFloat(), jsonValue[1].asFloat(), jsonValue[2].asFloat());
    }
    else
    {
        return false;
    }
    return true;
}
bool PickerShape::loadVertices(MPointArray& points, const Json::Value& jsonPointArray)
{
    if (!jsonPointArray.isArray())
    {
        return false;
    }
    bool result = true;
    Json::ArrayIndex pointNum = jsonPointArray.size();
    points.setLength(pointNum);
    for (Json::ArrayIndex i = 0; i < pointNum; ++i)
    {
        const Json::Value& jsonPoint = jsonPointArray[i];
        result = result && loadFloat3(points[i], jsonPoint);
    }
    return result;
}


LSViewportPicker::LSViewportPicker(){}
LSViewportPicker::~LSViewportPicker() {
    if (fAttrChangedCbId != 0)
    {
        MMessage::removeCallback(fAttrChangedCbId);
        fAttrChangedCbId = 0;
    }
}

void LSViewportPicker::updateShapeList()
{

    shapeList.clear();
    //scan custom shape json file in the handle folder.
    const char* resourcePathEnv = getenv("MHY_RESOURCE_PATH");
    if (resourcePathEnv != nullptr)
    {
        std::string env_str(resourcePathEnv);
        std::vector<std::string> result;
        const char delimiter = ';';
        size_t previous = 0;
        size_t index = env_str.find(delimiter);
        while (index != std::string::npos)
        {
            result.push_back(env_str.substr(previous, index - previous));
            previous = index + 1;
            index = env_str.find(delimiter, previous);
        }
        result.push_back(env_str.substr(previous));
        namespace fs = std::filesystem;

        MString msgBuffer;
        for (auto path : result) {
            const fs::path resourcePath{ path };
            const fs::path handlePath = resourcePath / fs::path("picker_shapes");
            if (fs::exists(handlePath))
            {
                msgBuffer.format(MString("Loading MHY picker shapes from `^1s`"), handlePath.c_str());
                MGlobal::displayInfo(msgBuffer);
                for (const auto& entry : fs::directory_iterator(handlePath))
                {
                    if (entry.is_regular_file())
                    {
                        fs::path entryPath = entry.path();
                        if (entryPath.extension() == ".picker")
                        {
                            const std::string filename = entryPath.string();
                            std::ifstream jsonStream(filename);
                            Json::Value shapeJson;
                            jsonStream >> shapeJson;
                            std::string name = shapeJson["name"].asString();
                            PickerShape shape(name.c_str());
                            shape.loadShape(shapeJson);
                            shapeList.push_back(shape);

                        }
                    }
                }
            }
        }
    }
}

void* LSViewportPicker::creator()
{
    return new LSViewportPicker();
}

void LSViewportPicker::postConstructor() {
    char buf[1024];

    fAttrChangedCbId = MNodeMessage::addAttributeChangedCallback(thisMObject(), OnAttrChanged, this);
    MFnDependencyNode node(thisMObject());
    UpdateAlphaImageCache(this);
}

void LSViewportPicker::OnAttrChanged(MNodeMessage::AttributeMessage msg, MPlug& plug,
    MPlug& otherPlug, void* clientData)
{
    if((plug.partialName(false, false, false, true, true, true) == "alpha")
        || (plug.partialName(false, false, false, true, true, true) == "imagePath")){
        LSViewportPicker* node = static_cast<LSViewportPicker*>(clientData);
        UpdateAlphaImageCache(node);
    }
 }

void LSViewportPicker::UpdateAlphaImageCache(LSViewportPicker* node)
{
    MFnDependencyNode dpNode(node->thisMObject());
    MPlug alphaPlug = dpNode.findPlug("alpha", false);
    node->alpha = alphaPlug.asFloat();

    MString textureFileName;
    MPlug texturePlug = dpNode.findPlug("imagePath", false);
    texturePlug.getValue(textureFileName);
    if (textureFileName.length() == 0) {
        return;
    }
    MHWRender::MRenderer* theRenderer = MHWRender::MRenderer::theRenderer();
    if (theRenderer == NULL) {
        return;
    }
    MHWRender::MTextureManager* txtManager = theRenderer->getTextureManager();
    if (txtManager == NULL) {
        return;
    }

    int mipmapLevels = 1;
    node->fTexture = txtManager->acquireTexture(textureFileName, mipmapLevels);
    if (node->fTexture == NULL)
    {
        return;
    }

    int rowPitch = 0;
    size_t slicePitch = 0;
    unsigned char* pixelData = (unsigned char*)node->fTexture->rawData(rowPitch, slicePitch);
    unsigned char* val = NULL;
    bool generateMipMaps = true;
    MHWRender::MTextureDescription desc;
    node->fTexture->textureDescription(desc);

    if (pixelData && rowPitch > 0 && slicePitch > 0)
    {
        for (unsigned int i = 0; i < desc.fHeight; i++)
        {
            val = pixelData + (i * rowPitch) + 3;

            for (unsigned int j = 0; j < desc.fWidth; j++)
            {
                if (*val > 0) {
                    *val = std::max(255 * node->alpha, 0.01f);
                }
                val += 4;
            }
        }
        node->fTexture->update(pixelData, generateMipMaps, rowPitch);
    }


    delete[] pixelData;

    MHWRender::MRenderer::setGeometryDrawDirty(node->thisMObject());
}

LSViewportPicker* LSViewportPicker::getController(const MDagPath& dagPath)
{
    MStatus status;
    MObject controllerObj = dagPath.node(&status);
    MFnDagNode dagFn(dagPath);
    MPxNode* pNode = dagFn.userNode(&status);
    return dynamic_cast<LSViewportPicker*>(pNode);
}

MStatus LSViewportPicker::initialize()
{   updateShapeList();
    MStatus status;
    MFnCompoundAttribute cmpAttr;
    MFnNumericAttribute nAttr;
    MFnEnumAttribute eAttr;
    MFnTypedAttribute typedAttr;
    MFnMessageAttribute msgAttr;

    // Add ui type attribute
    aUIType = eAttr.create("uiType", "ut", LSViewportPicker::kCircle);
    eAttr.addField("circle", LSViewportPicker::kCircle);
    eAttr.addField("rect", LSViewportPicker::kRect);
    eAttr.addField("image", LSViewportPicker::kImage);
    int id = 3;
    for (auto pickShape : shapeList)
    {
        status = eAttr.addField(pickShape.name, id++);
    }
    MPxNode::addAttribute(aUIType);

    // Add selectability attribute
    aSelectability = eAttr.create("selectability", "st", MUIDrawManager::kAutomatic);
    eAttr.addField("NonSelectable", MUIDrawManager::kNonSelectable);
    eAttr.addField("Selectable", MUIDrawManager::kSelectable);
    eAttr.addField("Automatic", MUIDrawManager::kAutomatic);
    MPxNode::addAttribute(aSelectability);

    MFnStringData cameraFnStringData;
    MObject cameraDefaultObject = cameraFnStringData.create("");
    aCameraTarget = typedAttr.create("cameraTargets", "camt", MFnData::kString, cameraDefaultObject);
    typedAttr.setStorable(true);
    MPxNode::addAttribute(aCameraTarget);

    // Add color attribute
    aColor= nAttr.create("color", "col", MFnNumericData::k3Float);
    nAttr.setDefault(1.0f, 0.0f, 0.0f);
    nAttr.setUsedAsColor(true);
    MPxNode::addAttribute(aColor);

    // Add color attribute
    aHighColor = nAttr.create("highLightColor", "hcol", MFnNumericData::k3Float);
    nAttr.setDefault(1.0f, 1.0f, 1.0f);
    nAttr.setUsedAsColor(true);
    MPxNode::addAttribute(aHighColor);

    // Add color attribute
    aContainerTextColor = nAttr.create("containerTextColor", "ctcol", MFnNumericData::k3Float);
    nAttr.setDefault(1.0f, 1.0f, 1.0f);
    nAttr.setUsedAsColor(true);
    MPxNode::addAttribute(aContainerTextColor);

    // Add transparency attribute
    aAlpha= nAttr.create("alpha", "al", MFnNumericData::kFloat, 1.0);
    nAttr.setMin(0.01);
    nAttr.setMax(1.0);
    MPxNode::addAttribute(aAlpha);

    // Add color attribute
    aPosition = nAttr.create("pickerPosition", "pp", MFnNumericData::k2Double);
    nAttr.setDefault(0.0, 0.0);
    MPxNode::addAttribute(aPosition);

    // Add color attribute
    aPickerLocalScale = nAttr.create("pickerLocalScale", "pls", MFnNumericData::kFloat);
    nAttr.setDefault(1.0f);
    MPxNode::addAttribute(aPickerLocalScale);

    // add line width and line style attributes
    aLineWidth = nAttr.create("lineWidth", "lw", MFnNumericData::kFloat, 2.0);
    nAttr.setMin(0.0);

    MPxNode::addAttribute(aLineWidth);
    aLineStyle = eAttr.create("lineStyle", "ls", MUIDrawManager::kSolid);
    eAttr.addField("solid", MUIDrawManager::kSolid);
    eAttr.addField("shortdotted", MUIDrawManager::kShortDotted);
    eAttr.addField("shortdashed", MUIDrawManager::kShortDashed);
    eAttr.addField("dashed", MUIDrawManager::kDashed);
    eAttr.addField("dotted", MUIDrawManager::kDotted);
    MPxNode::addAttribute(aLineStyle);
    // Add filled attribute

    aIsFilled = nAttr.create("isFilled", "if", MFnNumericData::kBoolean, 1);
    MPxNode::addAttribute(aIsFilled);
    // Add texture path attribute
    MFnStringData fileFnStringData;
    MObject fileNameDefaultObject = fileFnStringData.create("");
    aTexturePath = typedAttr.create("imagePath", "imp", MFnData::kString, fileNameDefaultObject);
    typedAttr.setStorable(true);
    typedAttr.setUsedAsFilename(true);
    MPxNode::addAttribute(aTexturePath);
    
    // Add radius attribute
    aRadius = nAttr.create("radius", "ra", MFnNumericData::kDouble, 30.0);
    MPxNode::addAttribute(aRadius);
    nAttr.setMin(0.0);

    // Add width attribute
    aWidth = nAttr.create("width", "wd", MFnNumericData::kDouble, 30.0);
    nAttr.setMin(0.0);
    MPxNode::addAttribute(aWidth);

    // Add height attribute
    aHeight= nAttr.create("height", "ht", MFnNumericData::kDouble, 30.0);
    nAttr.setMin(0.0);
    MPxNode::addAttribute(aHeight);

    // Add rotate attribute
    aRotate= nAttr.create("rotate", "r", MFnNumericData::kFloat, 0.0);
    MPxNode::addAttribute(aRotate);
   
    // Add text attributes.
    MFnStringData stringFn;
    MObject defaultText = stringFn.create("lsViewportPicker-Text");
    aText = typedAttr.create("text", "t", MFnData::kString, defaultText);
    MPxNode::addAttribute(aText);
    aTextFontSize = nAttr.create("textFontSize", "tfs", MFnNumericData::kInt, MUIDrawManager::kDefaultFontSize);
    nAttr.setMin(-1);
    nAttr.setMax(99);
    MPxNode::addAttribute(aTextFontSize);
    unsigned int nFont = MUIDrawManager::getFontList(LSViewportPickerData::fFontList);
    if (nFont == 0)
    {
        perror("No font available!");
    }
    aFontFaceName = eAttr.create("fontFaceName", "ffn", 0);
    for (unsigned int i = 0; i < nFont; i++)
    {
        MString str = LSViewportPickerData::fFontList[i];
        eAttr.addField(str, (short)i);
    }
    MPxNode::addAttribute(aFontFaceName);
    aTextAlignment = eAttr.create("textAlignment", "ta", MUIDrawManager::kLeft);
    eAttr.addField("left", MUIDrawManager::kLeft);
    eAttr.addField("center", MUIDrawManager::kCenter);
    eAttr.addField("right", MUIDrawManager::kRight);
    MPxNode::addAttribute(aTextAlignment);
    eTextIncline = eAttr.create("textIncline", "tic", MUIDrawManager::kInclineNormal);
    eAttr.addField("normal", MUIDrawManager::kInclineNormal);
    eAttr.addField("italic", MUIDrawManager::kInclineItalic);
    MPxNode::addAttribute(eTextIncline);
    aTextWeight = eAttr.create("textWeight", "tw", MUIDrawManager::kWeightBold);
    eAttr.addField("light", MUIDrawManager::kWeightLight);
    eAttr.addField("normal", MUIDrawManager::kWeightNormal);
    eAttr.addField("demiBold", MUIDrawManager::kWeightDemiBold);
    eAttr.addField("bold", MUIDrawManager::kWeightBold);
    eAttr.addField("black", MUIDrawManager::kWeightBlack);
    MPxNode::addAttribute(aTextWeight);
    aTextStretch = nAttr.create("textStretch", "ts", MFnNumericData::kInt, MUIDrawManager::kStretchUnstretched);
    nAttr.setMin(50);
    nAttr.setMax(200);
    MPxNode::addAttribute(aTextStretch);
    aTextLine = eAttr.create("textLine", "tl", 0);
    eAttr.addField("none", 0);
    eAttr.addField("overline", MUIDrawManager::kLineOverline);
    eAttr.addField("underline", MUIDrawManager::kLineUnderline);
    eAttr.addField("strikeout", MUIDrawManager::kLineStrikeoutLine);
    MPxNode::addAttribute(aTextLine);
    aTextBoxSize = nAttr.create("textBoxSize", "tbs", MFnNumericData::k2Int);
    nAttr.setDefault(0, 0);
    MPxNode::addAttribute(aTextBoxSize);
    aTextBoxColor = nAttr.create("textBoxColor", "tbc", MFnNumericData::k3Float);
    nAttr.setDefault(0.0f, 1.0f, 1.0f);
    nAttr.setUsedAsColor(true);
    MPxNode::addAttribute(aTextBoxColor);
    aTextBoxTransparency = nAttr.create("textBoxTransparency", "tbt", MFnNumericData::kFloat, 0.0);
    nAttr.setSoftMin(0.0);
    nAttr.setSoftMax(1.0);
    MPxNode::addAttribute(aTextBoxTransparency);

    return MS::kSuccess;
}
