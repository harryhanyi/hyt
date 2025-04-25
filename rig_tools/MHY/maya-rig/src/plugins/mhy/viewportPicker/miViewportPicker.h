#include <maya/MPxLocatorNode.h>
#include <maya/MNodeMessage.h>
#include <functional>
#include <map>
#include <json/json.h>

#ifndef LSVIEWPORTPICKER_H_
#define LSVIEWPORTPICKER_H_

using namespace MHWRender;

class PickerShape
{
public:
    typedef std::vector<MPointArray> DrawUnit;
    PickerShape(const char* name);
    MString name;
    DrawUnit wireFrameData;
    DrawUnit shadedData;

    bool loadShape(const Json::Value& jsonValue);
private:
    static bool loadVertices(MPointArray& points, const Json::Value& jsonPointArray);
    static bool loadFloat3(MPoint& value, const Json::Value& jsonValue);
};

class LSViewportPicker : public MPxLocatorNode
{
public:
    enum EuiType {
        kRect,
        kCircle,
        kImage,
    };
    enum ELimitType {
        kSlider,
        kSquare,
    };

public:
    LSViewportPicker();
    ~LSViewportPicker() override;
    static void* creator();
    static LSViewportPicker* getController(const MDagPath& dagPath);
    static MStatus            initialize();
    void postConstructor() override;
    bool excludeAsLocator() const { return false; };
    // general attribute
    static MObject aUIType;
    static MObject aSelectability;
    static MObject aCameraTarget;

    // color
    static MObject aColor;
    static MObject aHighColor;
    static MObject aContainerTextColor;
    static MObject aAlpha;
    static MObject aPosition;
    static MObject aPickerLocalScale;
    

    // limitat widget
    static MObject aLimitWidget;
    static MObject aLimitRange;
    static MObject aLimitInput;
    static MObject aLimitWidgetSize;
    
    // line width and line style attributes
    static MObject aLineWidth;
    static MObject aLineStyle;
    // fill attribute
    static MObject aIsFilled;
    static MObject aTexturePath;
    
    // radius attribute
    static MObject aRadius;
    static MObject aWidth;
    static MObject aHeight;
    static MObject aRotate;

    // Text attributes
    static MObject aTextAlignment;
    static MObject eTextIncline;
    static MObject aTextWeight;
    static MObject aTextStretch;
    static MObject aTextLine;
    static MObject aTextBoxSize;
    static MObject aText;
    static MObject aTextBoxColor;
    static MObject aTextBoxTransparency;
    static MObject aTextFontSize;
    static MObject aFontFaceName;
    // line attributes

public:
    static MTypeId id;
    static MString drawDbClassification;
    static MString drawRegistrantId;
    mutable MBoundingBox fBBox;
    MHWRender::MTexture* fTexture = NULL;
    float alpha = 1.0f;
    static void UpdateAlphaImageCache(LSViewportPicker* node);
    static void updateShapeList();

    typedef std::vector<PickerShape> ShapeList;

    static ShapeList shapeList;
    
private:
    MCallbackId fAttrChangedCbId = 0;
    static void OnAttrChanged(MNodeMessage::AttributeMessage msg, MPlug& plug,
        MPlug& otherPlug, void*);


};

#endif