#include "angleSliceSolver.h"
#include <maya/MFnMesh.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MArrayDataBuilder.h>

MTypeId AngleSliceSolver::id(0x001357c7);

MObject AngleSliceSolver::aClamp;
MObject AngleSliceSolver::aLocation;
MObject AngleSliceSolver::aLocationX;
MObject AngleSliceSolver::aLocationY;
MObject AngleSliceSolver::aInputName;
MObject AngleSliceSolver::aInputLocationX;
MObject AngleSliceSolver::aInputLocationY;
MObject AngleSliceSolver::aInputValue;
MObject AngleSliceSolver::aInputList;
MObject AngleSliceSolver::aOutputValue;
MStatus AngleSliceSolver::initialize()
{
    MStatus status;
    MFnNumericAttribute numAttrFn;
    aClamp = numAttrFn.create("clamp", "clp", MFnNumericData::kBoolean, true);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);
    addAttribute(aClamp);

    aLocationX = numAttrFn.create("locationX", "lx", MFnNumericData::kDouble, 0.0);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);
    addAttribute(aLocationX);

    aLocationY = numAttrFn.create("locationY", "ly", MFnNumericData::kDouble, 0.0);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);
    addAttribute(aLocationY);

    aLocation = numAttrFn.create("location", "lct", aLocationX, aLocationY);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);
    addAttribute(aLocation);

    MFnTypedAttribute typeFn;
    aInputName = typeFn.create("inputName", "in", MFnData::kString);
    CHECK_MSTATUS(typeFn.setChannelBox(true));
    CHECK_MSTATUS(typeFn.setStorable(true));
    CHECK_MSTATUS(typeFn.setWritable(true));

    aInputLocationX = numAttrFn.create("inputLocationX", "ilx", MFnNumericData::kDouble, 0.0);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);

    aInputLocationY = numAttrFn.create("inputLocationY", "ily", MFnNumericData::kDouble, 0.0);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);

    aInputValue = numAttrFn.create("inputValue", "iv", MFnNumericData::kDouble, 0.0);
    numAttrFn.setStorable(true);
    numAttrFn.setKeyable(true);
    numAttrFn.setReadable(true);
    numAttrFn.setWritable(true);

    MFnCompoundAttribute compoundAttrFn;
    aInputList = compoundAttrFn.create("inputList", "il", &status);
    compoundAttrFn.setArray(true);
    status = compoundAttrFn.addChild(aInputName);
    status = compoundAttrFn.addChild(aInputLocationX);
    status = compoundAttrFn.addChild(aInputLocationY);
    status = compoundAttrFn.addChild(aInputValue);
    addAttribute(aInputList);

    aOutputValue = numAttrFn.create("outputValue", "ov", MFnNumericData::kDouble, 0.0);
    numAttrFn.setReadable(true);
    numAttrFn.setArray(true);
    numAttrFn.setKeyable(false);
    numAttrFn.setUsesArrayDataBuilder(true);
    addAttribute(aOutputValue);

    attributeAffects(aClamp, aOutputValue);
    attributeAffects(aLocationX, aOutputValue);
    attributeAffects(aLocationY, aOutputValue);
    attributeAffects(aLocation, aOutputValue);
    attributeAffects(aInputLocationX, aOutputValue);
    attributeAffects(aInputLocationY, aOutputValue);
    attributeAffects(aInputValue, aOutputValue);
    attributeAffects(aInputList, aOutputValue);
    return MStatus::kSuccess;
}

double AngleSliceSolver::computeRadians(const MVector &dir)
{
    double radians = atan2(dir.y, dir.x) - atan2(startDir.y, startDir.x);
    if (radians < 0.0)
    {
        radians += M_PI * 2.0;
    }
    return radians;
}

MStatus AngleSliceSolver::updateAttributes(MDataBlock &data)
{
    MStatus status;
    values.clear();
    splitAngles.clear();
    splitMagnitudes.clear();
    MArrayDataHandle inputListHandle = data.inputArrayValue(aInputList, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    elementNum = inputListHandle.elementCount(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MDataHandle handle = inputListHandle.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MDataHandle xHandle = handle.child(aInputLocationX);
    MDataHandle yHandle = handle.child(aInputLocationY);
    MDataHandle vHandle = handle.child(aInputValue);
    splitAngles.append(0.0);
    values.append(vHandle.asDouble());
    startDir.x = xHandle.asDouble();
    startDir.y = yHandle.asDouble();
    splitMagnitudes.append(startDir.length());
    while (inputListHandle.next())
    {
        handle = inputListHandle.inputValue(&status);
        xHandle = handle.child(aInputLocationX);
        yHandle = handle.child(aInputLocationY);
        vHandle = handle.child(aInputValue);
        values.append(vHandle.asDouble());
        MVector dir(xHandle.asDouble(), yHandle.asDouble(), 0.0);
        splitMagnitudes.append(dir.length());
        splitAngles.append(computeRadians(dir));
    }
    splitAngles.append(2.0 * M_PI);
    values.append(values[0]);
    splitMagnitudes.append(startDir.length());

    //compute current angle and direction.
    MDataHandle locationHandle = data.inputValue(aLocation, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    xHandle = locationHandle.child(aLocationX);
    yHandle = locationHandle.child(aLocationY);
    MVector currentDir;
    currentDir.x = xHandle.asDouble();
    currentDir.y = yHandle.asDouble();
    currentAngle = computeRadians(currentDir);
    currentMagnitude = currentDir.length();

    updateBlendIndices();
    return MStatus::kSuccess;
}

void AngleSliceSolver::updateBlendIndices()
{
    double floorAngle = -M_PI;
    double ceilAngle = 3 * M_PI;
    floorIndex = -1;
    ceilIndex = -1;
    unsigned int num = splitAngles.length();
    for (unsigned int index = 0; index < num; ++index)
    {
        double splitAngle = splitAngles[index];
        if (splitAngle == currentAngle)
        {
            floorIndex = index;
            ceilIndex = index;
            return;
        }
        else if (splitAngle > currentAngle && splitAngle < ceilAngle)
        {
            ceilIndex = index;
            ceilAngle = splitAngle;
        }
        else if (splitAngle < currentAngle && splitAngle > floorAngle)
        {
            floorIndex = index;
            floorAngle = splitAngle;
        }
    }
}

void AngleSliceSolver::computeOutputValues(MArrayDataHandle &outArrayHandle, const bool clamp)
{
    MDataHandle outputHandle;
    if (floorIndex == ceilIndex)
    {
        outArrayHandle.jumpToElement(floorIndex);
        double value = currentMagnitude / splitMagnitudes[floorIndex];
        outputHandle = outArrayHandle.outputValue();
        outputHandle.setDouble(value);
        return;
    }
    double floorValue = currentMagnitude / splitMagnitudes[floorIndex];
    double ceilValue = currentMagnitude / splitMagnitudes[ceilIndex];
    double floorAngle = splitAngles[floorIndex];
    double ceilAngle = splitAngles[ceilIndex];
    double ratio = (currentAngle - floorAngle) / (ceilAngle - floorAngle);
    ceilValue *= ratio;
    floorValue *= (1.0 - ratio);
    double magnitude = ceilValue + floorValue;
    ceilValue = ceilValue * currentMagnitude / magnitude;
    floorValue = floorValue * currentMagnitude / magnitude;
    if (clamp)
    {
        double scale = 1.0 / (ceilValue + floorValue);
        if (scale < 1.0)
        {
            ceilValue *= scale;
            floorValue *= scale;
        }
    }

    outArrayHandle.jumpToElement(floorIndex);
    outputHandle = outArrayHandle.outputValue();
    outputHandle.setDouble(floorValue);
    if (ceilIndex == elementNum)
    {
        outArrayHandle.jumpToElement(0);
    }
    else
    {
        outArrayHandle.jumpToElement(ceilIndex);
    }
    outputHandle = outArrayHandle.outputValue();
    outputHandle.setDouble(ceilValue);
}

MStatus AngleSliceSolver::compute(const MPlug &plug, MDataBlock &data)
{
    MStatus status;
    auto name = plug.name();
    std::cerr << name;
    if (plug == aOutputValue)
    {
        CHECK_MSTATUS_AND_RETURN_IT(updateAttributes(data));
        MArrayDataHandle outArrayHandle = data.outputArrayValue(aOutputValue, &status);
        CHECK_MSTATUS_AND_RETURN_IT(status);
        MArrayDataBuilder outbuilder = outArrayHandle.builder(&status);
        CHECK_MSTATUS_AND_RETURN_IT(status);
        unsigned int index = 0;
        MDataHandle outHandle;
        while (index < elementNum)
        {
            status = outArrayHandle.jumpToElement(index);
            if (status != MStatus::kSuccess)
            {
                outHandle = outbuilder.addElement(index, &status);
                CHECK_MSTATUS_AND_RETURN_IT(status);
            }
            else
            {
                outHandle = outArrayHandle.outputValue();
            }
            outHandle.setDouble(0.0);
            ++index;
        }
        outArrayHandle.set(outbuilder);
        MDataHandle clampHandle = data.inputValue(aClamp, &status);
        bool clamp = clampHandle.asBool();
        CHECK_MSTATUS_AND_RETURN_IT(status);
        computeOutputValues(outArrayHandle, clamp);
        data.setClean(aOutputValue);
    }
    data.setClean(plug);
    return MStatus::kSuccess;
}
