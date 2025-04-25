#pragma once
#include "GeometryInfo.h"
#include <maya/MPxCommand.h>
#include <maya/MArgList.h>
#include <maya/MString.h>
#include <maya/MVector.h>
#include <maya/MSyntax.h>
class GeometryInfoCmd : public MPxCommand
{
        MStatus printErr();
public:
        GeometryInfoCmd();
        virtual ~GeometryInfoCmd(); 
        MStatus doIt( const MArgList& args ) override;
        MStatus undoIt() override;
        MStatus redoIt() override;
        bool isUndoable() const override
        {
            return true;
        }
        static void* creator();
        static MSyntax cmdSyntax();
        LSGeometryInfo* getNode();
        int index;
        MObject nodeObj;
        bool setTranslate;
        bool setRotate;
        MVector translate;
        MVector rotate;
        MVector oldTranslate;
        MVector oldRotate;
};