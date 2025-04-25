#pragma once
#include <maya/MPxNode.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnMeshData.h>
#include <maya/MItMeshVertex.h>
#include <maya/MDoubleArray.h>
#include <maya/MVectorArray.h>

class AngleSliceSolver final: public MPxNode
{
public:
    AngleSliceSolver() = default;
    MStatus compute(const MPlug& plug, MDataBlock& data) override;
    static void* creator(){ return new AngleSliceSolver(); }
    static MStatus initialize();
private:
    // update AngleSliceSolver data from maya attributes.
    MStatus updateAttributes(MDataBlock& data);
    // compute output values.
    void computeOutputValues(MArrayDataHandle& outArrayHandle, const bool clamp);
    // return radians between dir and AngleSliceSolver.startDir.
    double computeRadians(const MVector& dir);
    // update AngleSliceSolver.floorIndex and AngleSliceSolver.ceilIndex, which are the indices two input values of the smallest pie covered current Dir.
    void updateBlendIndices();
public:
    static MTypeId id;
    static MObject aClamp;
    static MObject aLocation;
    static MObject aLocationX;
    static MObject aLocationY;
    static MObject aInputName;
    static MObject aInputLocationX;
    static MObject aInputLocationY;
    static MObject aInputValue;
    static MObject aInputList;
    static MObject aOutputValue;
    MDoubleArray splitAngles;
    MDoubleArray splitMagnitudes;
    MDoubleArray values;
    MVector startDir;
    double currentAngle;
    double currentMagnitude;
    int floorIndex;
    int ceilIndex;
    int elementNum;
    // MVector dir;
};

