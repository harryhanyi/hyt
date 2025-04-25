#include "tensionNode.h"
#include <maya/MFnMesh.h>
#include <maya/MFnDoubleArrayData.h>

MTypeId tensionNode::id(0x001357c6);
MObject tensionNode::aNeutralMesh;
MObject tensionNode::aDeformedMesh;
MObject tensionNode::aOutMesh;
MObject tensionNode::aTension;

MStatus tensionNode::initialize()
{
    MStatus status;
    MFnTypedAttribute typeAttrFn;
    aNeutralMesh = typeAttrFn.create("neutralMesh", "nm", MFnMeshData::kMesh);
    typeAttrFn.setStorable(true);

    aDeformedMesh = typeAttrFn.create("deformedMesh", "dm", MFnMeshData::kMesh);
    typeAttrFn.setStorable(true);

    aOutMesh = typeAttrFn.create("outputMesh", "om", MFnMeshData::kMesh);
    typeAttrFn.setWritable(false);
    typeAttrFn.setStorable(false);

    aTension = typeAttrFn.create("tension", "ts", MFnData::kDoubleArray, &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(typeAttrFn.setStorable(true));
    CHECK_MSTATUS(typeAttrFn.setArray(false));
    
    addAttribute(aNeutralMesh);
    addAttribute(aDeformedMesh);
    addAttribute(aOutMesh);
    addAttribute(aTension);

    attributeAffects(aNeutralMesh, aOutMesh);
    attributeAffects(aDeformedMesh, aOutMesh);
    attributeAffects(aNeutralMesh, aTension);
    attributeAffects(aDeformedMesh, aTension);    

    return MStatus::kSuccess;
}

MStatus tensionNode::compute(const MPlug& plug, MDataBlock& data)
{
    MStatus status;

    if (plug == aOutMesh || plug == aTension)
    {
        MObject thisObj = thisMObject();
        MDataHandle origHandle = data.inputValue(aNeutralMesh, &status);
        CHECK_MSTATUS(status);
        MDataHandle deformedHandle = data.inputValue(aDeformedMesh, &status);
        CHECK_MSTATUS(status);
        MDataHandle outHandle = data.outputValue(aOutMesh, &status);
        CHECK_MSTATUS(status);
        MObject neutralObj = origHandle.asMesh();
        MObject deformedObj = deformedHandle.asMesh();
        updateTension(neutralObj, deformedObj);

        MObject outMesh = outHandle.asMesh();
        outHandle.copy(deformedHandle);
        outMesh = outHandle.asMesh();
        outHandle.set(outMesh);

        MDataHandle tensionHandle = data.outputValue(aTension, &status);
        CHECK_MSTATUS(status);
        //update tension attribute.
        MFnDoubleArrayData doubleDataFn;
        MObject tensionData = doubleDataFn.create(tensionArray, &status);
        CHECK_MSTATUS(status);
        status = tensionHandle.set(tensionData);
        CHECK_MSTATUS(status);

        //set vertex color.
        MFnMesh meshFn(outMesh, &status);
        CHECK_MSTATUS(status);
        int numVerts = tensionArray.length();
        if (numVerts > 0)
        {
            MColorArray vertColors;
            MIntArray vertIds;
            CHECK_MSTATUS(vertColors.setLength(numVerts));
            CHECK_MSTATUS(vertIds.setLength(numVerts));
            for (int i = 0; i < numVerts; ++i)
            {
                double tension = tensionArray[i];
                MColor vertColor(0.0, 0.0, 0.0f, 1.0f);
                if (tension>=0.0)
                {
                    vertColor.g = tension; 
                }
                else
                {
                    vertColor.r = -tension;
                }
                vertColors.set(vertColor, i);
                vertIds.set(i, i);
            }
            CHECK_MSTATUS(meshFn.setVertexColors(vertColors, vertIds));
        };
    }
    data.setClean(plug);
    return MStatus::kSuccess;
}



void tensionNode::updateTension(MObject neutralMeshObj, MObject deformMeshObj)
{
    MStatus status;
    MItMeshVertex neutralVIt0(neutralMeshObj, &status);
    MItMeshVertex neutralVIt1(neutralMeshObj, &status);
    MItMeshVertex deformVIt0(deformMeshObj, &status);
    MItMeshVertex deformVIt1(deformMeshObj, &status);
    MPoint neutralP0;
    MPoint neutralP1;
    MPoint deformP0;
    MPoint deformP1;
    MVector neutralV;
    MVector deformV;
    MVector tensionV;
    int dummy;
    tensionArray.setLength(neutralVIt0.count());
    while (!neutralVIt0.isDone())
    {
        double lengthSum = 0.0;
        MIntArray connectedVertices;
        neutralVIt0.getConnectedVertices(connectedVertices);
        tensionV = MVector::zero;
        double delta = 1.0;
        int edgeNum = connectedVertices.length();
        for (int i = 0; i < edgeNum; i++)
        {
            int oppositeVertexId;
            neutralVIt1.setIndex(connectedVertices[i], dummy);
            deformVIt1.setIndex(connectedVertices[i], dummy);
            neutralP0 = neutralVIt0.position();
            neutralP1 = neutralVIt1.position();
            deformP0 = deformVIt0.position();
            deformP1 = deformVIt1.position();
            deformV = deformP1 - deformP0;
            neutralV = neutralP1 - neutralP0;
            delta *= deformV.length()/neutralV.length();
        }
        delta = pow(delta, 1.0 / edgeNum);
        int id = neutralVIt0.index();
        if (delta > 1.0)//stretch
        {
            tensionArray[id] = 1.0-1.0 / delta;
        }
        else//compress
        {
            tensionArray[id] = delta-1.0;
        }
        neutralVIt0.next();
        deformVIt0.next();
    }
}
