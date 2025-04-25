#pragma once

#include <maya/MPxNode.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnMeshData.h>
#include <maya/MItMeshVertex.h>
#include <maya/MDoubleArray.h>
class tensionNode : public MPxNode
{
public:
    tensionNode() {}
    virtual MStatus compute(const MPlug& plug, MDataBlock& data);
    static void* creator(){ return new tensionNode(); }
    static MStatus initialize();
    void updateTension(MObject neutralMeshObj, MObject deformMeshObj);
public:
    static MTypeId id;
    static MObject aNeutralMesh;
    static MObject aDeformedMesh;
    static MObject aOutMesh;
    static MObject aTension;
    MDoubleArray tensionArray;
};

