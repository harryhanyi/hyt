#include "miController.h"
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MColor.h>
#include <maya/MVector.h>
#include <maya/MFnDagNode.h>
#include <maya/MPxNode.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MDataBlock.h>
#include <maya/MArrayDataBuilder.h>
#include <maya/MEvaluationNode.h>
#include <maya/MViewport2Renderer.h>
#include <maya/MQuaternion.h>
#include <maya/MPlugArray.h>
#include <filesystem>
#include <fstream>
#include <json/json.h>

MTypeId LSController::sId(0x001357c0);
MObject LSController::aDrawIt;
MObject LSController::aFacePoseDriver;
MObject LSController::aFacePoseType;
MObject LSController::aFacePose;
MObject LSController::aFacePoseOverride;
MObject LSController::aFacePoseScale;
MObject LSController::aLocalRotate;
MObject LSController::aRebuild;
MObject LSController::aColor;
MObject LSController::aText;
MObject LSController::aTextPosition;
MObject LSController::aXrayMode;
MObject LSController::aShape;
MObject LSController::aMHYig;
MObject LSController::aControllerType;
MObject LSController::aBBoxMin;
MObject LSController::aBBoxMax;
MString LSController::drawDbClassification("drawdb/geometry/miController");
MString LSController::drawRegistrantId("miControllerPlugin");
LSControllerDrawData::Handle::List LSController::sHandleList;

void LSController::postConstructor()
{
	MStatus status;
	MFnDependencyNode node_fn(thisMObject());
	node_fn.setName("miControllerShape#");
}

LSController *LSController::getController(const MDagPath &dagPath)
{
	MStatus status;
	MObject controllerObj = dagPath.node(&status);
	MFnDagNode dagFn(dagPath);
	MPxNode *pNode = dagFn.userNode(&status);
	return dynamic_cast<LSController *>(pNode);
}
void LSController::updateShapeList()
{
	sHandleList.clear();

	sHandleList.push_back(LSControllerDrawData::Handle("circle"));
	sHandleList.push_back(LSControllerDrawData::Handle("cube"));
	sHandleList.push_back(LSControllerDrawData::Handle("square"));
	sHandleList.push_back(LSControllerDrawData::Handle("triangle"));
	sHandleList.push_back(LSControllerDrawData::Handle("hexagram"));
	sHandleList.push_back(LSControllerDrawData::Handle("donut"));
	sHandleList.push_back(LSControllerDrawData::Handle("sphere"));
	sHandleList.push_back(LSControllerDrawData::Handle("sphereCurve"));

	//scan custom shape json file in the handle folder.
	const char *resourcePathEnv = getenv("MHY_RESOURCE_PATH");
	if (resourcePathEnv != nullptr)
	{
		namespace fs = std::filesystem;
		const fs::path resourcePath{resourcePathEnv};
		const fs::path handlePath = resourcePath / fs::path("handles");
		if (fs::exists(handlePath))
		{
			for (const auto &entry : fs::directory_iterator(handlePath))
			{
				if (entry.is_regular_file())
				{
					fs::path entryPath = entry.path();
					if (entryPath.extension() == ".hdl")
					{
						const std::string filename = entryPath.string();
						std::ifstream jsonStream(filename);
						Json::Value shapeJson;
						jsonStream >> shapeJson;
						std::string version = shapeJson["version"].asString();
						std::string name = shapeJson["name"].asString();
						auto loader = LSControllerDrawData::getLoader(version);
						LSControllerDrawData::Handle handle(name.c_str());
						if (loader(&handle, shapeJson))
						{
							sHandleList.push_back(handle);

						}
					}
				}
			}
		}
	}
}
LSController::LSController()
{
}

LSController::~LSController()
{
}

// Called before this node is evaluated by Evaluation Manager
MStatus LSController::preEvaluation(
	const MDGContext &context,
	const MEvaluationNode &evaluationNode)
{
	if (context.isNormal())
	{
		MStatus status;
		if (controllerType == kPoseController)
		{
			if (evaluationNode.dirtyPlugExists(aFacePose, &status) && status)
			{
				MHWRender::MRenderer::setGeometryDrawDirty(thisMObject());
			}
		}
		else if (controllerType == kLocator)
		{
			if (evaluationNode.dirtyPlugExists(aRebuild, &status) && status)
			{
				MHWRender::MRenderer::setGeometryDrawDirty(thisMObject());
			}
		}
	}
	return MStatus::kSuccess;
}

MStatus LSController::computeOverride(const int index, MDataBlock &data)
{
	MStatus status;
	MArrayDataHandle outputArrayHandle = data.outputArrayValue(aFacePoseOverride);
	MArrayDataHandle inputArrayHandle = data.inputArrayValue(aFacePoseDriver);
	status = inputArrayHandle.jumpToElement(index);
	if (status)
	{
		MDataHandle currentInputHandle = inputArrayHandle.inputValue();
		float facePoseValue = currentInputHandle.asFloat();
		status = outputArrayHandle.jumpToElement(index);
		MDataHandle currentOutputHandle;
		if (status)
		{
			currentOutputHandle = outputArrayHandle.outputValue();
			float &outputValue = currentOutputHandle.asFloat();
			outputValue = facePoseValue;
		}
		else
		{
			MArrayDataBuilder builder = outputArrayHandle.builder();
			float &outputValue = builder.addElement(index).asFloat();
			outputValue = facePoseValue;
			outputArrayHandle.set(builder);
		}
	}
	return status;
}
MStatus LSController::computeFacePose(const int index, MDataBlock &data)
{
	MStatus status;
	if (index == -1)
	{
		return MS::kSuccess;
	}
	float scale = data.inputValue(aFacePoseScale).asFloat();
	MArrayDataHandle outputArrayHandle = data.outputArrayValue(aFacePose);
	status = outputArrayHandle.jumpToElement(index);
	if (!status)
	{
		MArrayDataBuilder builder = outputArrayHandle.builder();
		builder.addElement(index).asFloat();
		outputArrayHandle.set(builder);
		status = outputArrayHandle.jumpToElement(index);
	}
	MDataHandle currentOutputHandle = outputArrayHandle.outputValue();
	float &outputValue = currentOutputHandle.asFloat();
	MArrayDataHandle inputArrayHandle = data.inputArrayValue(aFacePoseDriver);
	status = inputArrayHandle.jumpToElement(index);
	if (status)
	{
		MDataHandle currentInputHandle = inputArrayHandle.inputValue();
		float facePoseValue = currentInputHandle.asFloat();
		outputValue = facePoseValue * scale;
	}
	return status;
}

MStatus LSController::compute(const MPlug &plug, MDataBlock &data)
{
	MStatus status;
	//controllerType = data.inputValue(aControllerType).asInt();
	if (plug == aRebuild)
	{
		MDataHandle inputHandle = data.inputValue(localScale);
		inputHandle = data.inputValue(aLocalRotate);
		inputHandle = data.inputValue(localPosition);
		inputHandle = data.inputValue(aShape);
		inputHandle = data.inputValue(aColor);
		inputHandle = data.inputValue(aText);
		inputHandle = data.inputValue(aTextPosition);
		inputHandle = data.inputValue(aXrayMode);
		inputHandle = data.inputValue(aControllerType);
		MDataHandle outputHandle = data.outputValue(aRebuild);
		outputHandle.set(true);
	}
	else if (plug == aFacePoseOverride)
	{
		int index = plug.logicalIndex();
		computeOverride(index, data);
	}
	else if (plug == aFacePose)
	{
		MPlugArray inputPlugArray;
		plug.connectedTo(inputPlugArray, true, false, &status);
		CHECK_MSTATUS(status);
		int index = plug.logicalIndex();
		MArrayDataHandle typeArrayHandle = data.inputArrayValue(aFacePoseType);
		bool isCorrectivePose = false;
		if (typeArrayHandle.jumpToElement(index))
		{
			if (typeArrayHandle.inputValue().asBool())
			{
				isCorrectivePose = true;
			}
		}
		if (!isCorrectivePose)
		{
			computeOverride(index, data);
		}
		computeFacePose(index, data);
	}
	data.setClean(plug);
	return MStatus::kSuccess;
}

bool LSController::isBounded() const
{
	return true;
}

MMatrix LSController::getMatrix() const
{
	MObject thisNode = thisMObject();
	MVector scale = getControllerScale();
	MPoint position = getControllerPosition();
	MVector rotate = getControllerRotate();
	MMatrix result = MMatrix::identity;
	result[0][0] = scale[0];
	result[1][1] = scale[1];
	result[2][2] = scale[2];
	MQuaternion rotateX, rotateY, rotateZ;
	rotateX.setToXAxis(rotate[0]);
	rotateY.setToYAxis(rotate[1]);
	rotateZ.setToZAxis(rotate[2]);
	result = (rotateZ * rotateY * rotateX).asMatrix() * result;
	result[0][3] = position[0];
	result[1][3] = position[1];
	result[2][3] = position[2];
	return result;
}

void *LSController::creator()
{
	return new LSController();
}

MStatus LSController::setDependentsDirty(
	const MPlug &plugBeingDirtied,
	MPlugArray &affectedPlugs)
{
	MString plugName = plugBeingDirtied.partialName(false, false, false, false, false, true); //useLongNames = false
	if (plugName.substring(0, 16) == "facePoseOverride[")
	{
		MStatus status;
		MObject thisNode = thisMObject();
		MPlug facePosePlug(thisNode, LSController::aFacePose);
		unsigned int index = plugBeingDirtied.logicalIndex();
		MPlug affectedPlug = facePosePlug.elementByLogicalIndex(index, &status);
		CHECK_MSTATUS(status);
		affectedPlugs.append(affectedPlug);
		recomputeOverrideAttribute = false;
	}
	if (plugName.substring(0, 14) == "facePoseDriver[")
	{
		MStatus status;
		MObject thisNode = thisMObject();
		MPlug facePoseDriverPlug(thisNode, LSController::aFacePoseOverride);
		unsigned int index = plugBeingDirtied.logicalIndex();
		MPlug affectedPlug = facePoseDriverPlug.elementByLogicalIndex(index, &status);
		CHECK_MSTATUS(status);
		affectedPlugs.append(affectedPlug);
		MPlug facePosePlug(thisNode, LSController::aFacePose);
		affectedPlug = facePosePlug.elementByLogicalIndex(index, &status);
		CHECK_MSTATUS(status);
		affectedPlugs.append(affectedPlug);
		recomputeOverrideAttribute = true;
	}
	return (MStatus::kSuccess);
}

MStatus LSController::initialize()
{
	LSController::updateShapeList();

	MStatus stat;
	MFnNumericAttribute numFn;

	aBBoxMin = numFn.create("bboxmin", "bmin", MFnNumericData::k3Float);
	numFn.setHidden(true);
	CHECK_MSTATUS(addAttribute(aBBoxMin));
	aBBoxMax = numFn.create("bboxmax", "bmax", MFnNumericData::k3Float);
	numFn.setHidden(true);
	CHECK_MSTATUS(addAttribute(aBBoxMax));

	aFacePoseScale = numFn.create("facePoseScale", "fps", MFnNumericData::kFloat);
	CHECK_MSTATUS(numFn.setDefault(1.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setArray(false));
	CHECK_MSTATUS(addAttribute(aFacePoseScale));

	aFacePose = numFn.create("facePose", "fp", MFnNumericData::kFloat);
	CHECK_MSTATUS(numFn.setDefault(0.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setArray(true));
	CHECK_MSTATUS(addAttribute(aFacePose));

	aFacePoseType = numFn.create("facePoseType", "fpt", MFnNumericData::kInt);
	CHECK_MSTATUS(numFn.setDefault(0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setArray(true));
	CHECK_MSTATUS(addAttribute(aFacePoseType));

	aFacePoseDriver = numFn.create("facePoseDriver", "fpd", MFnNumericData::kFloat);
	CHECK_MSTATUS(numFn.setDefault(0.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setArray(true));
	CHECK_MSTATUS(addAttribute(aFacePoseDriver));

	aFacePoseOverride = numFn.create("facePoseOverride", "fpo", MFnNumericData::kFloat);
	CHECK_MSTATUS(numFn.setDefault(0.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setArray(true));
	CHECK_MSTATUS(numFn.setUsesArrayDataBuilder(true));
	CHECK_MSTATUS(addAttribute(aFacePoseOverride));

	MObject localRotateX = numFn.create("localRotateX", "lrx", MFnNumericData::kDouble);
	MObject localRotateY = numFn.create("localRotateY", "lry", MFnNumericData::kDouble);
	MObject localRotateZ = numFn.create("localRotateZ", "lrz", MFnNumericData::kDouble);
	aLocalRotate = numFn.create("localRotate", "lr", localRotateX, localRotateY, localRotateZ, &stat);
	CHECK_MSTATUS(numFn.setDefault(0.0, 0.0, 0.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aLocalRotate));

	aRebuild = numFn.create("rebuild", "rb", MFnNumericData::kBoolean);
	CHECK_MSTATUS(numFn.setDefault(true));
	CHECK_MSTATUS(numFn.setStorable(false));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(numFn.setHidden(true));
	CHECK_MSTATUS(addAttribute(aRebuild));

	aColor = numFn.createColor("color", "clr");
	CHECK_MSTATUS(numFn.setDefault(1.0, 0.0, 0.0));
	CHECK_MSTATUS(numFn.setMin(0.0, 0.0, 0.0));
	CHECK_MSTATUS(numFn.setMax(1.0, 1.0, 1.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aColor));

	MObject textPositionX = numFn.create("textPositionX", "tpx", MFnNumericData::kDouble);
	MObject textPositionY = numFn.create("textPositionY", "tpy", MFnNumericData::kDouble);
	MObject textPositionZ = numFn.create("textPositionZ", "tpz", MFnNumericData::kDouble);
	aTextPosition = numFn.create("textPosition", "tp", textPositionX, textPositionY, textPositionZ, &stat);
	CHECK_MSTATUS(numFn.setDefault(0.0, 0.0, 0.0));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aTextPosition));

	MFnTypedAttribute typeFn;
	aText = typeFn.create("label", "l", MFnData::kString);
	CHECK_MSTATUS(typeFn.setChannelBox(true));
	CHECK_MSTATUS(typeFn.setStorable(true));
	CHECK_MSTATUS(typeFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aText));

	aMHYig = typeFn.create("lsRig", "mhy", MFnData::kString);
	CHECK_MSTATUS(typeFn.setChannelBox(true));
	CHECK_MSTATUS(typeFn.setStorable(true));
	CHECK_MSTATUS(typeFn.setWritable(true));
	CHECK_MSTATUS(typeFn.setHidden(true));
	CHECK_MSTATUS(addAttribute(aMHYig))

	MFnEnumAttribute enumFn;
	aShape = enumFn.create("shapeType", "st", 0, &stat);
	CHECK_MSTATUS(stat);
	int id = 0;
	for (auto handle : sHandleList)
	{
		stat = enumFn.addField(handle.name, id++);
		CHECK_MSTATUS(stat);
	}
	CHECK_MSTATUS(enumFn.setChannelBox(true));
	CHECK_MSTATUS(enumFn.setStorable(true));
	CHECK_MSTATUS(enumFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aShape));
	aControllerType = enumFn.create("controllerType", "ctt", 0, &stat);
	CHECK_MSTATUS(stat);
	stat = enumFn.addField("Locator", kLocator);
	CHECK_MSTATUS(stat);
	stat = enumFn.addField("PoseController", kPoseController);
	CHECK_MSTATUS(stat);
	stat = enumFn.addField("PoseDriver", kPoseDriver);
	CHECK_MSTATUS(stat);
	CHECK_MSTATUS(enumFn.setChannelBox(true));
	CHECK_MSTATUS(enumFn.setStorable(true));
	CHECK_MSTATUS(enumFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aControllerType));

	aXrayMode = numFn.create("xrayMode", "xr", MFnNumericData::kBoolean);
	CHECK_MSTATUS(numFn.setDefault(false));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aXrayMode));

	aDrawIt = numFn.create("drawIt", "di", MFnNumericData::kBoolean);
	CHECK_MSTATUS(numFn.setDefault(true));
	CHECK_MSTATUS(numFn.setChannelBox(true));
	CHECK_MSTATUS(numFn.setStorable(true));
	CHECK_MSTATUS(numFn.setWritable(true));
	CHECK_MSTATUS(addAttribute(aDrawIt));

	attributeAffects(localScale, aRebuild);
	attributeAffects(aLocalRotate, aRebuild);
	attributeAffects(localPosition, aRebuild);
	attributeAffects(aShape, aRebuild);
	attributeAffects(aColor, aRebuild);
	attributeAffects(aText, aRebuild);
	attributeAffects(aTextPosition, aRebuild);
	attributeAffects(aXrayMode, aRebuild);
	attributeAffects(aDrawIt, aRebuild);
	attributeAffects(aControllerType, aFacePose);
	attributeAffects(aFacePoseScale, aFacePoseDriver);
	attributeAffects(aFacePoseScale, aFacePoseOverride);
	MPxManipContainer::addToManipConnectTable(sId);
	return MStatus::kSuccess;
}

template <typename TupleType>
TupleType getFloatTupleAttribute(MPlug plug)
{
	MDataHandle dataHandle;
	if (plug.getValue(dataHandle))
	{
		const float3 &value = dataHandle.asFloat3();
		return TupleType(value);
	}
	return TupleType();
}

template <typename TupleType>
void setFloatTupleAttribute(MDataBlock &data, MObject attribute, const TupleType &value)
{
	MDataHandle dataHandle = data.outputValue(attribute);
	float3 &outputValue = dataHandle.asFloat3();
	outputValue[0] = value[0];
	outputValue[1] = value[1];
	outputValue[2] = value[2];
}

template <>
MPoint getFloatTupleAttribute(MPlug plug)
{
	MDataHandle dataHandle;
	if (plug.getValue(dataHandle))
	{
		const float3 &value = dataHandle.asFloat3();
		return MPoint(value[0], value[1], value[2], 1.0);
	}
	return MPoint(0.0, 0.0, 0.0, 1.0);
}

template <typename TupleType>
TupleType getDoubleTupleAttribute(MPlug plug)
{
	MDataHandle dataHandle;
	if (plug.getValue(dataHandle))
	{
		const double3 &value = dataHandle.asDouble3();
		return TupleType(value);
	}
	return TupleType();
}

template <>
MPoint getDoubleTupleAttribute(MPlug plug)
{
	MDataHandle dataHandle;
	if (plug.getValue(dataHandle))
	{
		const double3 &value = dataHandle.asDouble3();
		return MPoint(value[0], value[1], value[2], 1.0);
	}
	return MPoint(0.0, 0.0, 0.0, 1.0);
}
template <typename TupleType>
TupleType getFloatTupleAttribute(MObject controller, const MObject attributeObj)
{
	MPlug plug(controller, attributeObj);
	if (!plug.isNull())
	{
		return getFloatTupleAttribute<typename TupleType>(plug);
	}
	return TupleType();
}

template <typename TupleType>
TupleType getDoubleTupleAttribute(MObject controller, const MObject attributeObj)
{
	MPlug plug(controller, attributeObj);
	if (!plug.isNull())
	{
		return getDoubleTupleAttribute<typename TupleType>(plug);
	}
	return TupleType();
}
template <typename TupleType>
TupleType getTupleAttribute(const MDagPath &dagPath, const MObject attributeObj)
{
	MStatus status;
	MObject controller = dagPath.node(&status);
	if (status)
	{
		return getTupleAttribute<typename TupleType>(controller, attributeObj);
	}
	return TupleType();
}

template <typename TupleType>
TupleType getTupleAttribute(const MDagPath &dagPath, const MString &attrName)
{
	MStatus status;
	MObject controller = dagPath.node(&status);
	if (status)
	{
		MFnDependencyNode nodeFn(controller);
		MPlug plug = nodeFn.findPlug(attrName);
		if (!plug.isNull())
		{
			return getTupleAttribute<typename TupleType>(plug);
		}
	}
	return TupleType();
}

MString LSController::getStrAttr(MObject attribute) const
{
	MObject controller = thisMObject();
	MDataHandle dataHandle;
	MDataBlock data = getDataBlock();
	MDataHandle hText = data.inputValue(attribute);
	return hText.asString();
}

MString LSController::getMHYig() const
{
	return getStrAttr(aMHYig);
}

MString LSController::getLabel() const
{
	return getStrAttr(aText);
}

bool LSController::needRebuild() const
{
	MDataBlock data = getDataBlock();
	MDataHandle inDataHandle = data.inputValue(aRebuild);
	bool result = inDataHandle.asBool();
	MDataHandle outDataHandle = data.outputValue(aRebuild);
	outDataHandle.set(false);
	data.setClean(aRebuild);
	return result;
}

bool LSController::isXrayMode() const
{
	MDataBlock data = getDataBlock();
	MDataHandle inDataHandle = data.inputValue(aXrayMode);
	return inDataHandle.asBool();
}

bool LSController::isDrawableMode() const
{
	MDataBlock data = getDataBlock();
	MDataHandle inDataHandle = data.inputValue(aDrawIt);
	return inDataHandle.asBool();
}

MColor LSController::getColor() const
{
	return getFloatTupleAttribute<MColor>(thisMObject(), aColor);
}

MPoint LSController::getControllerPosition() const
{
	return getDoubleTupleAttribute<MPoint>(thisMObject(), localPosition);
}

MVector LSController::getControllerRotate() const
{
	double degreeToRadian = M_PI / 180.0;
	return degreeToRadian * getDoubleTupleAttribute<MVector>(thisMObject(), aLocalRotate);
}

MVector LSController::getControllerScale() const
{
	return getDoubleTupleAttribute<MVector>(thisMObject(), localScale);
}

MPoint LSController::getTextPosition() const
{
	return getDoubleTupleAttribute<MPoint>(thisMObject(), aTextPosition);
}

short LSController::getShapeTypeId() const
{
	short result = getAttr<short>(LSController::aShape);
	if (result >= LSController::sHandleList.size())
	{
		return 6; //sphere
	}
	return result;
}

MBoundingBox LSController::boundingBox() const
{
	MPoint minPoint = getFloatTupleAttribute<MPoint>(thisMObject(), aBBoxMin);
	MPoint maxPoint = getFloatTupleAttribute<MPoint>(thisMObject(), aBBoxMax);
	MBoundingBox bbox(minPoint, maxPoint);
	MPoint textPosition = getTextPosition();
	bbox.expand(textPosition);
	return bbox;
}

void LSController::updateBBox(const MBoundingBox &bbox)
{
	MDataBlock data = getDataBlock();
	setFloatTupleAttribute(data, aBBoxMin, bbox.min());
	setFloatTupleAttribute(data, aBBoxMax, bbox.max());
}


LSControllerInfoCmd::LSControllerInfoCmd(){};
LSControllerInfoCmd::~LSControllerInfoCmd(){};

void* LSControllerInfoCmd::creator()
{
	return new LSControllerInfoCmd();
}

MStatus LSControllerInfoCmd::doIt(const MArgList& args)
{
	MStatus status;
	MStringArray result;
	for (auto item : LSController::sHandleList) {
		result.append(item.name);
	}
	MPxCommand::setResult(result);
	return status;
}