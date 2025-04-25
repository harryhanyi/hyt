#pragma once
#include <maya/MPxLocatorNode.h>
#include <maya/MDistance.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MPxManipContainer.h>
#include <maya/MColor.h>
#include <maya/MStringArray.h>
#include <maya/MMatrix.h>
#include <memory>

#include <maya/MPxCommand.h>
#include <maya/MArgList.h>
#include <maya/MString.h>
#include <maya/MVector.h>
#include <maya/MSyntax.h>

#include "miControllerDrawData.h"

using namespace std;

class LSController : public MPxLocatorNode
{
public:
	enum ControllerType
	{
		kLocator = 0,
		kPoseController = 1,
		kPoseDriver = 2
	};
	LSController();
	~LSController() override;
	void LSController::postConstructor() override;
	MStatus computeOverride(const int index, MDataBlock& data);
	MStatus computeFacePose(const int index, MDataBlock& data);
	MStatus compute(const MPlug &plug, MDataBlock &data) override;
	bool isBounded() const override;
	MBoundingBox boundingBox() const override;
	void updateBBox(const MBoundingBox& bbox);
	MMatrix getMatrix() const;
	MPoint getTextPosition() const;
	MColor getColor() const;
	short getShapeTypeId() const;
	MString getLabel() const;
	MString getMHYig() const;
	MString getStrAttr(MObject attribute) const;
	bool needRebuild() const;
	bool isXrayMode() const;
	bool isDrawableMode() const;
	static void *creator();
	static MStatus initialize();
	static LSController *getController(const MDagPath &dagPath);
	static void updateShapeList();
	MStatus preEvaluation(const MDGContext &context, const MEvaluationNode &evaluationNode) override;

private:
	int controllerType = 0;
	bool recomputeOverrideAttribute = true;
	static MObject aDrawIt;
	static MObject aFacePoseDriver;
	static MObject aFacePoseOverride;
	static MObject aFacePoseType;
	static MObject aFacePose;
	static MObject aRebuild;
	static MObject aColor;
	static MObject aLocalRotate;
	static MObject aTextPosition;
	static MObject aText;
	static MObject aShape;
	static MObject aControllerType;
	static MObject aXrayMode;
	static MObject aMHYig;
	static MObject aFacePoseScale;
	static MObject aBBoxMin;
	static MObject aBBoxMax;

public:
	static MTypeId sId;
	static MString drawDbClassification;
	static MString drawRegistrantId;
	static LSControllerDrawData::Handle::List sHandleList;

private:
	MStatus setDependentsDirty( const MPlug& plug, MPlugArray& plugArray) override;
	MVector getControllerScale() const;
	MVector getControllerRotate() const;
	MPoint getControllerPosition() const;
	inline MDataBlock getDataBlock()
	{
		return forceCache();
	}
	virtual MDataBlock getDataBlock() const
	{
		LSController *thisNode = const_cast<LSController *>(this);
		return thisNode->forceCache();
	}
	template <typename ValueType>
	ValueType getAttr(const MObject &oAttribute) const;
};

template <>
inline float LSController::getAttr(const MObject &attributeObj) const
{
	MDataBlock dataBlock = getDataBlock();
	MStatus status;
	MDataHandle inHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	dataBlock.setClean(attributeObj);
	return inHandle.asFloat();
}

template <>
inline double LSController::getAttr(const MObject &attributeObj) const
{
	MDataBlock dataBlock = getDataBlock();
	MStatus status;
	MDataHandle inHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	dataBlock.setClean(attributeObj);
	return inHandle.asDouble();
}

template <>
inline int LSController::getAttr(const MObject &attributeObj) const
{
	MDataBlock dataBlock = getDataBlock();
	MStatus status;
	MDataHandle inHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	dataBlock.setClean(attributeObj);
	return inHandle.asInt();
}

template <>
inline short LSController::getAttr(const MObject &attributeObj) const
{
	MDataBlock dataBlock = getDataBlock();
	MStatus status;
	MDataHandle inHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	dataBlock.setClean(attributeObj);
	return inHandle.asShort();
}

template <>
inline bool LSController::getAttr(const MObject &attributeObj) const
{
	MDataBlock dataBlock = getDataBlock();
	MStatus status;
	MDataHandle inHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	dataBlock.setClean(attributeObj);
	return inHandle.asBool();
}

template <>
inline MString LSController::getAttr(const MObject &attributeObj) const
{
	MString result;
	MStatus status = MStatus::kSuccess;
	MDataBlock dataBlock = getDataBlock();
	MDataHandle inputHandle = dataBlock.inputValue(attributeObj, &status);
	CHECK_MSTATUS(status);
	result = inputHandle.asString();
	return result;
}

class LSControllerInfoCmd : public MPxCommand
{
public:
	LSControllerInfoCmd();
	virtual ~LSControllerInfoCmd();
	static void* creator();
	MStatus doIt(const MArgList& args) override;
	bool isUndoable() const override
	{
		return false;
	}
};