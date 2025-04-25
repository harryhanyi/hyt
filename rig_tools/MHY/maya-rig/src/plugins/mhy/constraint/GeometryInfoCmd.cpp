#include "GeometryInfoCmd.h"
#include <maya/MStatus.h>
#include <maya/MSelectionList.h>
#include <maya/MGlobal.h>

#define kIndexFlagLong "index"
#define kIndexFlag "idx"
#define kSetTranslateFlagLong "setTranslate"
#define kSetTranslateFlag "st"
#define kSetRotateFlagLong "setRotate"
#define kSetRotateFlag "sr"
GeometryInfoCmd::GeometryInfoCmd() : index(-1),
                                     setTranslate(false),
                                     setRotate(false)
{
}
GeometryInfoCmd::~GeometryInfoCmd() {}

void *GeometryInfoCmd::creator()
{
    return new GeometryInfoCmd();
}

MStatus GeometryInfoCmd::printErr()
{
    MGlobal::displayError("Usage: GeometryInfoCmd geometryInfoNodeName\n"
                          "  [-setTranslate p.x p.y p.z]\n"
                          "  [-setRotate r.x r.y r.z]\n");
    return MS::kFailure;
}
LSGeometryInfo *GeometryInfoCmd::getNode()
{
    MStatus status;
    MFnDependencyNode nodeFn(nodeObj);
    MPxNode *pNode = nodeFn.userNode(&status);
    CHECK_MSTATUS(status);
    return dynamic_cast<LSGeometryInfo *>(pNode);
}

MSyntax GeometryInfoCmd::cmdSyntax()
{
    MSyntax syntax;
    syntax.addFlag(kIndexFlag, kIndexFlagLong, MSyntax::kLong);
    syntax.addFlag(kSetTranslateFlag, kSetTranslateFlagLong, MSyntax::kDouble, MSyntax::kDouble, MSyntax::kDouble);
    syntax.addFlag(kSetRotateFlag, kSetRotateFlagLong, MSyntax::kDouble, MSyntax::kDouble, MSyntax::kDouble);
    syntax.enableQuery(false);
    syntax.enableEdit(false);
    // Allow the user to select the nodes we will operate on, as well as allow
    // him/her to specify the node on the command line.
    //
    syntax.useSelectionAsDefault(true);
    syntax.setObjectType(MSyntax::kSelectionList);
    syntax.setMinObjects(1);
    return syntax;
}

MStatus GeometryInfoCmd::doIt(const MArgList &args)
{
    MStatus         status;
    MArgDatabase    argData(syntax(), args, &status);
    if (MStatus::kSuccess != status) {
        return(status);
    }
    if (!argData.isFlagSet(kIndexFlag))
    {
        printErr();
        return MS::kFailure;
    }

    CHECK_MSTATUS(argData.getFlagArgument(kIndexFlag, 0, index));
    double value = 0.0;
    if (argData.isFlagSet(kSetTranslateFlag))
    {
        setTranslate = true;
        for (int i = 0; i < 3; ++i)
        {
            CHECK_MSTATUS(argData.getFlagArgument(kSetTranslateFlag, i, value));
            translate[i] = value;
        }
    }
    if (argData.isFlagSet(kSetRotateFlag))
    {
        setRotate = true;
        for (int i = 0; i < 3; ++i)
        {
            CHECK_MSTATUS(argData.getFlagArgument(kSetRotateFlag, i, value));
            rotate[i] = value;
        }
    }
    //
    MSelectionList sList;
    status = argData.getObjects(sList);
    if (MS::kSuccess != status) {
        MGlobal::displayError(
            "nodeIcon: could not query the selection list");
        return(MS::kFailure);
    }
    int count = sList.length();
    if (MS::kSuccess != status || 1 != count) {
        MGlobal::displayError(
            "nodeIcon: you need to specify at least one node");
        return(MS::kFailure);
    }
    status = sList.getDependNode(0, nodeObj);
    if (MS::kSuccess != status) {
        MGlobal::displayError(
            "nodeIcon: only nodes can be selected");
        return(MS::kFailure);
    }
    return redoIt();
}

MStatus GeometryInfoCmd::redoIt()
{
    LSGeometryInfo *pNode = getNode();
    if (pNode)
    {
        if (setTranslate)
        {
            oldTranslate = pNode->setValue(LSGeometryInfo::aTranslate, index, translate);
        }
        if (setRotate)
        {
            oldRotate = pNode->setValue(LSGeometryInfo::aRotate, index, rotate);
        }
        return MStatus::kSuccess;
    }
    MGlobal::displayError("Invalid node type! Only a lsGeometryInfo can be specified!");
    return MStatus::kFailure;
}

MStatus GeometryInfoCmd::undoIt()
{
    LSGeometryInfo *pNode = getNode();
    if (pNode)
    {
        if (setTranslate)
        {
            translate = pNode->setValue(LSGeometryInfo::aTranslate, index, oldTranslate);
        }
        if (setRotate)
        {
            rotate = pNode->setValue(LSGeometryInfo::aRotate, index, oldRotate);
        }
        return MStatus::kSuccess;
    }
    MGlobal::displayError("Invalid node type! Only a lsGeometryInfo can be specified!");
    return MStatus::kFailure;
}
