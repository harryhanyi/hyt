#include "GeometryInfo.h"
#include <cmath>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MGlobal.h>
#include <maya/MEulerRotation.h>
#include <maya/MArrayDataHandle.h>
#include <maya/MArrayDataBuilder.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnGenericAttribute.h>
#include <maya/MFnIntArrayData.h>
#include <maya/MFnMeshData.h>
#include <maya/MFnMesh.h>
#include <maya/MFnNurbsSurface.h>
#include <maya/MTransformationMatrix.h>
#include <maya/MItMeshVertex.h>
#include <maya/MItMeshEdge.h>
#include <maya/MPlugArray.h>
#include <maya/MEvaluationNode.h>
#include <maya/MViewport2Renderer.h>

const std::vector<std::string> LSGeometryInfo::coordTypeNames = {"vertex", "uv"};
MTypeId LSGeometryInfo::sId(0x001357c2);
MObject LSGeometryInfo::aTargetGeometry;
MObject LSGeometryInfo::aTranslateX;
MObject LSGeometryInfo::aTranslateY;
MObject LSGeometryInfo::aTranslateZ;
MObject LSGeometryInfo::aTranslate;
MObject LSGeometryInfo::aRotateX;
MObject LSGeometryInfo::aRotateY;
MObject LSGeometryInfo::aRotateZ;
MObject LSGeometryInfo::aRotate;
MObject LSGeometryInfo::aCoordinate;
MObject LSGeometryInfo::aIndex;
MObject LSGeometryInfo::aMatrix;
MObject LSGeometryInfo::aTargetMatrix;
MObject LSGeometryInfo::aRotateOrder;
// MObject LSGeometryInfo::aCoordType;
MObject LSGeometryInfo::aUVCoord;
MObject LSGeometryInfo::aU;
MObject LSGeometryInfo::aV;
MObject LSGeometryInfo::aW;
MObject LSGeometryInfo::aDirtyDriver;
MObject LSGeometryInfo::aIndices;
MObject LSGeometryInfo::aParameters;
LSGeometryInfo::LSGeometryInfo()
{
}

LSGeometryInfo::~LSGeometryInfo()
{
}
bool LSGeometryInfo::isGPUOverride()
{
    MStatus status;
    MPlug meshPlug(thisMObject(), aTargetGeometry);
    MPlugArray plugArray;
    meshPlug.connectedTo(plugArray, true, false, &status);
    CHECK_MSTATUS(status);
    const unsigned int plugNum = plugArray.length();
    return plugNum == 0;
}
bool LSGeometryInfo::updateBuffer(const float *positions, const size_t size)
{
    MStatus status;
    if (!isGPUOverride()) //use traditional CPU to update buffer.
    {
        return true;
    }
    MDataBlock datablock = forceCache();
    datablock.inputArrayValue(aIndices);
    MArrayDataHandle inputArrayHandle = datablock.inputArrayValue(aCoordinate);
    MArrayDataHandle outTranslateArrayHandle = datablock.outputArrayValue(aTranslate);
    MArrayDataHandle outRotateArrayHandle = datablock.outputArrayValue(aRotate);
    unsigned int elementCount = inputArrayHandle.elementCount();
    inputArrayHandle.jumpToArrayElement(0);
    size_t offset = 0;
    for (unsigned int i = 0; i < elementCount; ++i)
    {
        if (offset + 3 > size)
            return false;
        unsigned int index = inputArrayHandle.elementIndex();
        status = outTranslateArrayHandle.jumpToElement(index);
        MDataHandle outTranslateHandle = outTranslateArrayHandle.outputValue();
        if (!status)
        {
            MArrayDataBuilder builder = outTranslateArrayHandle.builder();
            outTranslateHandle = builder.addElement(index);
            outTranslateArrayHandle.set(builder);
        }
        double3 &outTranslateValue = outTranslateHandle.asDouble3();
        if (outTranslateValue)
        {
            outTranslateValue[0] = positions[offset];
            outTranslateValue[1] = positions[offset + 1];
            outTranslateValue[2] = positions[offset + 2];
        }
        MDataHandle outRotateHandle = outRotateArrayHandle.outputValue();
        if (!status)
        {
            MArrayDataBuilder builder = outRotateArrayHandle.builder();
            outRotateHandle = builder.addElement(index);
            outRotateArrayHandle.set(builder);
        }
        double3 &outRotateValue = outRotateHandle.asDouble3();
        if (outRotateValue)
        {
            outRotateValue[0] = positions[offset];
            outRotateValue[1] = positions[offset + 1];
            outRotateValue[2] = positions[offset + 2];
        }

        offset += 3;
        inputArrayHandle.next();
    }
    return true;
}

MPxNode::SchedulingType LSGeometryInfo::schedulingType() const
{
    return MPxNode::SchedulingType::kParallel;
}

void LSGeometryInfo::cleanDirtyDriver(const MPlug &plug, MDataBlock &datablock)
{
    if (isGPUOverride())
    {
        MArrayDataHandle inputArrayHandle = datablock.inputArrayValue(aDirtyDriver);
        unsigned int elementCount = inputArrayHandle.elementCount();
        for (unsigned int i = 0; i < elementCount; ++i)
        {
            inputArrayHandle.inputValue();
        }
    }
}

MStatus LSGeometryInfo::computeParameters(MArrayDataHandle &inputArrayHandle, MDataBlock &datablock)
{
    MStatus status;
    MDataHandle outputHandle = datablock.outputValue(aIndices);
    unsigned int elementCount = inputArrayHandle.elementCount(&status);
    CHECK_MSTATUS(status);
    MIntArray indices(elementCount);
    for (unsigned int i = 0; i < elementCount; ++i, inputArrayHandle.next())
    {
        MDataHandle coordHandle = inputArrayHandle.inputValue();
        MDataHandle indexHandle = coordHandle.child(aIndex);
        indices[i] = indexHandle.asInt();
    }
    MFnIntArrayData indicesDataFn;
    MObject indicesData = indicesDataFn.create(indices);
    status = outputHandle.set(indicesData);
    CHECK_MSTATUS(status);
    return status;
}
void updateElement(const int index, const MMatrix &matrix,
                   MArrayDataHandle &outTranslateArrayHandle,
                   MArrayDataHandle &outRotateArrayHandle,
                   MArrayDataHandle &outMatrixArrayHandle,
                   MTransformationMatrix::RotationOrder rotateOrder)

{
    MStatus status = outMatrixArrayHandle.jumpToElement(index);
    MDataHandle outMatrixHandle;
    if (!status)
    {
        MArrayDataBuilder builder = outMatrixArrayHandle.builder();
        outMatrixHandle = builder.addElement(index);
        outMatrixArrayHandle.set(builder);
    }
    else
    {
        outMatrixHandle = outMatrixArrayHandle.outputValue(&status);
        CHECK_MSTATUS(status);
    }
    MMatrix &outMatrix = outMatrixHandle.asMatrix();
    outMatrix = matrix;
    status = outTranslateArrayHandle.jumpToElement(index);
    if (!status)
    {
        MArrayDataBuilder builder = outTranslateArrayHandle.builder();
        builder.addElement(index);
        outTranslateArrayHandle.set(builder);
    }
    MDataHandle outTranslateHandle = outTranslateArrayHandle.outputValue(&status);
    CHECK_MSTATUS(status);
    double3 &outTranslateValue = outTranslateHandle.asDouble3();
    if (outTranslateValue)
    {
        outTranslateValue[0] = matrix[3][0];
        outTranslateValue[1] = matrix[3][1];
        outTranslateValue[2] = matrix[3][2];
    }

    status = outRotateArrayHandle.jumpToElement(index);
    if (!status)
    {
        MArrayDataBuilder builder = outRotateArrayHandle.builder();
        builder.addElement(index);
        outRotateArrayHandle.set(builder);
    }
    MDataHandle outRotateHandle = outRotateArrayHandle.outputValue(&status);
    CHECK_MSTATUS(status);
    double3 &outRotateValue = outRotateHandle.asDouble3();
    if (outRotateValue)
    {
        MTransformationMatrix transformMatrix(outMatrix);
        transformMatrix.reorderRotation(rotateOrder);
        MEulerRotation eulers = transformMatrix.eulerRotation();
        outRotateValue[0] = eulers.x;
        outRotateValue[1] = eulers.y;
        outRotateValue[2] = eulers.z;
    }
}
bool LSGeometryInfo::updateFromNurbs(MObject nurbsObj, const int elemlnmtBegin, const int elemlnmtEnd, MDataBlock &datablock)
{
    MStatus status;
    MArrayDataHandle coordArrayHandle = datablock.inputArrayValue(aCoordinate);
    MArrayDataHandle outTranslateArrayHandle = datablock.outputArrayValue(aTranslate);
    MArrayDataHandle outRotateArrayHandle = datablock.outputArrayValue(aRotate);
    MArrayDataHandle outMatrixArrayHandle = datablock.outputArrayValue(aMatrix);
    MPoint position;
    if (!nurbsObj.isNull())
    {
        MMatrix &targetMatrix = datablock.inputValue(aTargetMatrix).asMatrix();
        MFnNurbsSurface nurbsFn(nurbsObj, &status);
        CHECK_MSTATUS(status);
        double startU, endU, startV, endV;
        nurbsFn.getKnotDomain(startU, endU, startV, endV);
        for (unsigned int index = elemlnmtBegin; index < elemlnmtEnd; ++index)
        {
            status = coordArrayHandle.jumpToElement(index);
            if (!status)
            {
                std::cerr << "Constraint to a vertex:" << index << " without information.";
                continue;
            }
            MDataHandle coordHandle = coordArrayHandle.inputValue();
            MDataHandle uvHandle = coordHandle.child(aUVCoord);
            double3 &uv = uvHandle.asDouble3();
            double u = startU + uv[0] * (endU - startU);
            double v = startV + uv[1] * (endV - startV);
            short order = coordHandle.child(aRotateOrder).asShort() + 1;
            MTransformationMatrix::RotationOrder rotateOrder = static_cast<MTransformationMatrix::RotationOrder>(order);
            MPoint point;
            CHECK_MSTATUS(nurbsFn.getPointAtParam(u, v, point));
            MVector uDir, vDir;
            nurbsFn.getTangents(u, v, uDir, vDir);
            MVector normal = vDir ^ uDir;
            vDir = normal ^ uDir;
            double matrixValue[4][4] = {{uDir[0], uDir[1], uDir[2], 0.0},
                                        {normal[0], normal[1], normal[2], 0.0},
                                        {vDir[0], vDir[1], vDir[2], 0.0},
                                        {point[0], point[1], point[2], 1.0}};
            MMatrix matrix = MMatrix(matrixValue) * targetMatrix;
            updateElement(index, matrix,
                          outTranslateArrayHandle,
                          outRotateArrayHandle,
                          outMatrixArrayHandle,
                          rotateOrder);
        }
        return true;
    }
    return false;
}

bool LSGeometryInfo::updateFromMesh(MObject meshObj, const int elemlnmtBegin, const int elemlnmtEnd, MDataBlock &datablock)
{
    MStatus status;
    MArrayDataHandle coordArrayHandle = datablock.inputArrayValue(aCoordinate);
    MArrayDataHandle outTranslateArrayHandle = datablock.outputArrayValue(aTranslate);
    MArrayDataHandle outRotateArrayHandle = datablock.outputArrayValue(aRotate);
    MArrayDataHandle outMatrixArrayHandle = datablock.outputArrayValue(aMatrix);
    MPoint position;
    if (!meshObj.isNull())
    {
        MFnMesh meshFn(meshObj, &status);
        CHECK_MSTATUS(status);
        MMatrix &targetMatrix = datablock.inputValue(aTargetMatrix).asMatrix();
        MItMeshVertex vertexIt(meshObj, &status);
        CHECK_MSTATUS(status);
        MItMeshEdge edgeIt(meshObj, &status);
        // MItMeshPolygon faceIt(meshObj, &status);
        CHECK_MSTATUS(status);
        for (unsigned int index = elemlnmtBegin; index < elemlnmtEnd; ++index)
        {
            status = coordArrayHandle.jumpToElement(index);
            if (!status)
            {
                std::cerr << "Constraint to a vertex:" << index << " without information.";
                continue;
            }
            MDataHandle coordHandle = coordArrayHandle.inputValue();
            MDataHandle indexHandle = coordHandle.child(aIndex);
            short order = coordHandle.child(aRotateOrder).asShort() + 1;
            MTransformationMatrix::RotationOrder rotateOrder = static_cast<MTransformationMatrix::RotationOrder>(order);
            int vertexIndex = indexHandle.asInt();
            if (vertexIndex >= 0) // do vertex constraint
            {
                int dummyPreIndex = 0;
                vertexIt.setIndex(vertexIndex, dummyPreIndex);
                position = vertexIt.position(MSpace::kObject, &status);
                MIntArray edgeList;
                vertexIt.getConnectedEdges(edgeList);
                edgeIt.setIndex(edgeList[0], dummyPreIndex);
                MVector uDir = edgeIt.point(1) - edgeIt.point(0);
                CHECK_MSTATUS(uDir.normalize());
                MVector normal;
                vertexIt.getNormal(normal);
                CHECK_MSTATUS(normal.normalize());
                MVector vDir = normal ^ uDir;
                double matrixValue[4][4] = {{uDir[0], uDir[1], uDir[2], 0.0},
                                            {normal[0], normal[1], normal[2], 0.0},
                                            {vDir[0], vDir[1], vDir[2], 0.0},
                                            {position[0], position[1], position[2], 1.0}};
                MMatrix matrix = MMatrix(matrixValue) * targetMatrix;
                updateElement(index, matrix,
                              outTranslateArrayHandle,
                              outRotateArrayHandle,
                              outMatrixArrayHandle,
                              rotateOrder);
            }
            else //do uv constraint
            {
                // MDataHandle uvHandle = coordHandle.child(aIndex);
                // float2 &uv = uvHandle.asFloat2();

                // meshFn.getPointAtUV() int dummyPreIndex = 0;
                // vertexIt.setIndex(vertexIndex, dummyPreIndex);
                // position = vertexIt.position(MSpace::kObject, &status);
                // MIntArray edgeList;
                // vertexIt.getConnectedEdges(edgeList);
                // edgeIt.setIndex(edgeList[0], dummyPreIndex);
                // MVector uDir = edgeIt.point(1) - edgeIt.point(0);
                // CHECK_MSTATUS(uDir.normalize());
                // MVector normal;
                // vertexIt.getNormal(normal);
                // CHECK_MSTATUS(normal.normalize());
                // MVector vDir = normal ^ uDir;
                // double matrixValue[4][4] = {{uDir[0], uDir[1], uDir[2], 0.0},
                //                             {normal[0], normal[1], normal[2], 0.0},
                //                             {vDir[0], vDir[1], vDir[2], 0.0},
                //                             {position[0], position[1], position[2], 1.0}};
                // MMatrix matrix = MMatrix(matrixValue) * targetMatrix;
                // updateElement(index, matrix,
                //               outTranslateArrayHandle,
                //               outRotateArrayHandle,
                //               outMatrixArrayHandle,
                //               rotateOrder);
            }
        }
        return true;
    }
    return false;
}

MStatus LSGeometryInfo::compute(const MPlug &plug, MDataBlock &datablock)
{
    MStatus status;
    if (plug == aIndices)
    {
        MArrayDataHandle inputArrayHandle = datablock.inputArrayValue(aCoordinate);
        computeParameters(inputArrayHandle, datablock);
    }
    if (plug == aTranslate || plug == aRotate || plug == aMatrix)
    {
        datablock.inputArrayValue(aIndices);
        datablock.inputArrayValue(aCoordinate);
        cleanDirtyDriver(plug, datablock);
        MDataHandle meshHandle = datablock.inputValue(aTargetGeometry);
        if (meshHandle.type() == MFnData::kMesh)
        {
            MObject meshObj = meshHandle.asMesh();
            int elemlnmtBegin = plug.logicalIndex();
            MArrayDataHandle coordArrayHandle = datablock.inputArrayValue(aCoordinate);
            int elementCount = coordArrayHandle.elementCount(&status);
            if (!status)
            {
                return status;
            }
            int elemlnmtEnd = elemlnmtBegin + 1;
            if (elemlnmtBegin < 0)
            {
                elemlnmtBegin = 0;
                elemlnmtEnd = elementCount;
            }
            updateFromMesh(meshObj, elemlnmtBegin, elemlnmtEnd, datablock);
        }
        if (meshHandle.type() == MFnData::kNurbsSurface)
        {
            MObject meshObj = meshHandle.asNurbsSurface();
            int elemlnmtBegin = plug.logicalIndex();
            MArrayDataHandle coordArrayHandle = datablock.inputArrayValue(aCoordinate);
            int elementCount = coordArrayHandle.elementCount(&status);
            if (!status)
            {
                return status;
            }
            int elemlnmtEnd = elemlnmtBegin + 1;
            if (elemlnmtBegin < 0)
            {
                elemlnmtBegin = 0;
                elemlnmtEnd = elementCount;
            }
            updateFromNurbs(meshObj, elemlnmtBegin, elemlnmtEnd, datablock);
        }
        datablock.setClean(plug);
    }
    else
    {
        return MStatus::kUnknownParameter;
    }
    return MStatus::kSuccess;
}

void *LSGeometryInfo::creator()
{
    return new LSGeometryInfo();
}

MVector LSGeometryInfo::setValue(MObject attribute, const unsigned int index, const MVector &position)
{
    MVector result;
    MStatus status;
    MDataBlock datablock = forceCache();
    MArrayDataHandle inputArrayHandle = datablock.inputArrayValue(attribute);
    MArrayDataHandle outputArrayHandle = datablock.outputArrayValue(attribute);
    unsigned int elementCount = inputArrayHandle.elementCount();
    unsigned int offset = index * 3;
    status = inputArrayHandle.jumpToElement(index);
    CHECK_MSTATUS(status);
    MDataHandle inputHandle = inputArrayHandle.inputValue();
    const float3 &inputValue = inputHandle.asFloat3();
    result[0] = inputValue[0];
    result[1] = inputValue[1];
    result[2] = inputValue[2];
    status = outputArrayHandle.jumpToElement(index);
    CHECK_MSTATUS(status);
    MDataHandle outputHandle = outputArrayHandle.outputValue();
    float3 &outputValue = outputHandle.asFloat3();
    outputValue[0] = position[0];
    outputValue[1] = position[1];
    outputValue[2] = position[2];
    return result;
}

MStatus LSGeometryInfo::initialize()
{
    MStatus status;
    MFnMeshData fnMeshData;
    MObject outMeshObject = fnMeshData.create(&status);
    CHECK_MSTATUS(status);

    MFnNumericAttribute numericAttrFn;
    MFnUnitAttribute unitAttrFn;
    aTranslateX = unitAttrFn.create("translateX", "tx", MFnUnitAttribute::kDistance, 0.0);
    aTranslateY = unitAttrFn.create("translateY", "ty", MFnUnitAttribute::kDistance, 0.0);
    aTranslateZ = unitAttrFn.create("translateZ", "tz", MFnUnitAttribute::kDistance, 0.0);
    aTranslate = numericAttrFn.create("translate", "t", aTranslateX, aTranslateY, aTranslateZ);
    CHECK_MSTATUS(numericAttrFn.setStorable(true));
    CHECK_MSTATUS(numericAttrFn.setReadable(true));
    CHECK_MSTATUS(numericAttrFn.setWritable(false));
    CHECK_MSTATUS(numericAttrFn.setArray(true));
    CHECK_MSTATUS(numericAttrFn.setUsesArrayDataBuilder(true));
    CHECK_MSTATUS(addAttribute(aTranslate));

    aRotateX = unitAttrFn.create("rotateX", "rx", MFnUnitAttribute::kAngle, 0.0);
    aRotateY = unitAttrFn.create("rotateY", "ry", MFnUnitAttribute::kAngle, 0.0);
    aRotateZ = unitAttrFn.create("rotateZ", "rz", MFnUnitAttribute::kAngle, 0.0);
    aRotate = numericAttrFn.create("rotate", "r", aRotateX, aRotateY, aRotateZ);
    CHECK_MSTATUS(numericAttrFn.setStorable(true));
    CHECK_MSTATUS(numericAttrFn.setReadable(true));
    CHECK_MSTATUS(numericAttrFn.setWritable(false));
    CHECK_MSTATUS(numericAttrFn.setArray(true));
    CHECK_MSTATUS(numericAttrFn.setUsesArrayDataBuilder(true));
    CHECK_MSTATUS(addAttribute(aRotate));

    MFnMatrixAttribute matrixAttrFn;
    aMatrix = matrixAttrFn.create("matrix", "m", MFnMatrixAttribute::kDouble);
    CHECK_MSTATUS(matrixAttrFn.setUsesArrayDataBuilder(true));
    CHECK_MSTATUS(matrixAttrFn.setReadable(true));
    CHECK_MSTATUS(matrixAttrFn.setWritable(false));
    CHECK_MSTATUS(matrixAttrFn.setArray(true));
    CHECK_MSTATUS(matrixAttrFn.setStorable(true));
    CHECK_MSTATUS(addAttribute(aMatrix));
    aTargetMatrix = matrixAttrFn.create("targetMatrix", "tm", MFnMatrixAttribute::kDouble);
    CHECK_MSTATUS(matrixAttrFn.setReadable(false));
    CHECK_MSTATUS(matrixAttrFn.setWritable(true));
    CHECK_MSTATUS(matrixAttrFn.setStorable(true));
    CHECK_MSTATUS(addAttribute(aTargetMatrix));

    MFnEnumAttribute enumAttrFn;
    aRotateOrder = enumAttrFn.create("rotateOrder", "ro", 0, &status);
    CHECK_MSTATUS(status);
    enumAttrFn.addField("xyz", 0);
    enumAttrFn.addField("yzx", 1);
    enumAttrFn.addField("zxy", 2);
    enumAttrFn.addField("xzy", 3);
    enumAttrFn.addField("yxz", 4);
    enumAttrFn.addField("zyx", 5);
    CHECK_MSTATUS(enumAttrFn.setStorable(true));

    // MFnEnumAttribute enumAttrFn;
    // aCoordType = enumAttrFn.create("coordType", "ctp", 0, &status);
    // CHECK_MSTATUS(status);
    // int typeId = 0;
    // for (auto coordTypeName : coordTypeNames)
    // {
    //     CHECK_MSTATUS(enumAttrFn.addField(coordTypeName.c_str(), typeId++));
    // }
    // CHECK_MSTATUS(enumAttrFn.setStorable(true));

    aIndex = numericAttrFn.create("coordIndex", "cidx", MFnNumericData::kLong, 0, &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(numericAttrFn.setStorable(true));

    aU = unitAttrFn.create("u", "u", MFnUnitAttribute::kDistance, 0.5);
    aV = unitAttrFn.create("v", "v", MFnUnitAttribute::kDistance, 0.5);
    aW = unitAttrFn.create("w", "w", MFnUnitAttribute::kDistance, 0.5);
    unitAttrFn.setHidden(true);
    aUVCoord = numericAttrFn.create("uv", "uv", aU, aV, aW, &status);
    CHECK_MSTATUS(status);

    MFnCompoundAttribute compoundAttrFn;
    aCoordinate = compoundAttrFn.create("coord", "cd", &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(compoundAttrFn.setStorable(true));

    CHECK_MSTATUS(compoundAttrFn.setArray(true));
    // CHECK_MSTATUS(compoundAttrFn.addChild(aCoordType));
    CHECK_MSTATUS(compoundAttrFn.addChild(aRotateOrder));
    CHECK_MSTATUS(compoundAttrFn.addChild(aIndex));
    CHECK_MSTATUS(compoundAttrFn.addChild(aUVCoord));
    CHECK_MSTATUS(compoundAttrFn.setReadable(false));
    CHECK_MSTATUS(compoundAttrFn.setWritable(true));
    CHECK_MSTATUS(addAttribute(aCoordinate));

    MFnTypedAttribute typeAttrFn;

    aIndices = typeAttrFn.create("indexList", "il", MFnData::kIntArray, &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(typeAttrFn.setStorable(true));
    CHECK_MSTATUS(typeAttrFn.setArray(false));
    aParameters = compoundAttrFn.create("kernelParameters", "kp", &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(compoundAttrFn.setStorable(true));
    CHECK_MSTATUS(compoundAttrFn.setArray(false));
    CHECK_MSTATUS(compoundAttrFn.addChild(aIndices));
    CHECK_MSTATUS(addAttribute(aParameters));

    // Create the generic attribute and set the 3 accepts types
    MFnGenericAttribute genericAttrFn;
    aTargetGeometry = genericAttrFn.create("targetGeometry", "tg");
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(genericAttrFn.setReadable(false));
    CHECK_MSTATUS(genericAttrFn.setWritable(true));
    CHECK_MSTATUS(genericAttrFn.setDisconnectBehavior(MFnAttribute::kDelete));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kMesh));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kNurbsSurface));
    // CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kNurbsCurve));
    // CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kSubdSurface));
    CHECK_MSTATUS(addAttribute(aTargetGeometry));

    aDirtyDriver = genericAttrFn.create("dirtyDriver", "dd");
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kAny));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kNumeric));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k2Short));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k3Short));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k2Long));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k3Long));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k2Float));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k3Float));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k2Double));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k3Double));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnNumericData::k4Double));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kPluginGeometry));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kString));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kMatrix));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kStringArray));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kDoubleArray));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kIntArray));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kPointArray));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kVectorArray));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kComponentList));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kMesh));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kLattice));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kNurbsCurve));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kNurbsSurface));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kSphere));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kDynArrayAttrs));
    CHECK_MSTATUS(genericAttrFn.addAccept(MFnData::kSubdSurface));
    CHECK_MSTATUS(genericAttrFn.setArray(true));
    CHECK_MSTATUS(genericAttrFn.setWritable(true));
    CHECK_MSTATUS(genericAttrFn.setHidden(false));
    CHECK_MSTATUS(genericAttrFn.setStorable(false));
    CHECK_MSTATUS(addAttribute(aDirtyDriver));

    CHECK_MSTATUS(attributeAffects(aTargetMatrix, aTranslate));
    CHECK_MSTATUS(attributeAffects(aTargetMatrix, aRotate));
    CHECK_MSTATUS(attributeAffects(aTargetMatrix, aMatrix));

    CHECK_MSTATUS(attributeAffects(aTargetGeometry, aTranslate));
    CHECK_MSTATUS(attributeAffects(aTargetGeometry, aRotate));
    CHECK_MSTATUS(attributeAffects(aTargetGeometry, aMatrix));
    CHECK_MSTATUS(attributeAffects(aDirtyDriver, aTranslate));
    CHECK_MSTATUS(attributeAffects(aDirtyDriver, aRotate));
    CHECK_MSTATUS(attributeAffects(aDirtyDriver, aMatrix));

    CHECK_MSTATUS(attributeAffects(aCoordinate, aTranslate));
    CHECK_MSTATUS(attributeAffects(aCoordinate, aRotate));
    CHECK_MSTATUS(attributeAffects(aCoordinate, aMatrix));
    CHECK_MSTATUS(attributeAffects(aIndex, aTranslate));
    CHECK_MSTATUS(attributeAffects(aIndex, aRotate));
    CHECK_MSTATUS(attributeAffects(aIndex, aMatrix));
    CHECK_MSTATUS(attributeAffects(aIndex, aParameters));
    CHECK_MSTATUS(attributeAffects(aUVCoord, aTranslate));
    CHECK_MSTATUS(attributeAffects(aUVCoord, aRotate));
    CHECK_MSTATUS(attributeAffects(aUVCoord, aMatrix));
    CHECK_MSTATUS(attributeAffects(aUVCoord, aParameters));
    CHECK_MSTATUS(attributeAffects(aCoordinate, aParameters));
    CHECK_MSTATUS(attributeAffects(aRotateOrder, aTranslate));
    CHECK_MSTATUS(attributeAffects(aRotateOrder, aRotate));
    CHECK_MSTATUS(attributeAffects(aRotateOrder, aMatrix));
    CHECK_MSTATUS(attributeAffects(aRotateOrder, aParameters));

    // CHECK_MSTATUS(attributeAffects(aCoordType, aTranslate));
    // CHECK_MSTATUS(attributeAffects(aCoordType, aRotate));
    // CHECK_MSTATUS(attributeAffects(aCoordType, aParameters));
    return MStatus::kSuccess;
}
