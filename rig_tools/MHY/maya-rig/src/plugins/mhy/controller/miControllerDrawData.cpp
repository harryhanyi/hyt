#include "miControllerDrawData.h"
#include "miController.h"
#include <Maya/MObject.h>
#include <Maya/MFnDagNode.h>

namespace
{
	void transformPointArray(MPointArray &targetPoints, MBoundingBox &bbox, const MPointArray &sourcePoints, const MMatrix &matrix)
	{
		//build lines.
		const int verticesNum = sourcePoints.length();
		targetPoints.setLength(verticesNum);
		for (int j = 0; j < verticesNum; ++j)
		{
			targetPoints[j] = (matrix * sourcePoints[j]);
			bbox.expand(targetPoints[j]);
		}
	}
	void transformShapeArray(LSControllerDrawData::DrawData::List &target, MBoundingBox &bbox, const LSControllerDrawData::DrawData::List &source, const MMatrix &matrix)
	{
		int linesShapeNum = int(source.size());
		target.resize(linesShapeNum);
		for (int i = 0; i < linesShapeNum; ++i)
		{
			const MPointArray &vertices = source[i].points;
			MPointArray &targetVertices = target[i].points;
			transformPointArray(targetVertices, bbox, vertices, matrix);
		}
	}
} // namespace
extern std::string sphereStr;
extern std::string donutStr;
extern std::string sphereCurveStr;
bool makeShapeFromJsonV1_0_0(LSControllerDrawData::Handle *handle, const Json::Value &jsonValue);
void LSControllerDrawData::Handle::makeCircle(DrawData &line, const int segment, const double offsetAngle)
{
	double segmentAngle = 2.0 * M_PI / segment;
	double angle = offsetAngle;
	MPoint curPoint;
	MPoint prePoint = MPoint(1.0 * cos(angle), 0.0, 1.0 * sin(angle));
	angle += segmentAngle;
	for (int i = 0; i < segment; i++)
	{
		curPoint = MPoint(1.0 * cos(angle), 0.0, 1.0 * sin(angle));
		line.add(prePoint, curPoint);
		//update iterate variables.
		prePoint = curPoint;
		angle += segmentAngle;
	}
}

void LSControllerDrawData::Handle::makeCube(DrawData &lines)
{
	lines.add(MPoint(-1.0, -1.0, -1.0), MPoint(1.0, -1.0, -1.0));
	lines.add(MPoint(1.0, -1.0, -1.0), MPoint(1.0, -1.0, 1.0));
	lines.add(MPoint(1.0, -1.0, 1.0), MPoint(-1.0, -1.0, 1.0));
	lines.add(MPoint(-1.0, -1.0, 1.0), MPoint(-1.0, -1.0, -1.0));
	lines.add(MPoint(-1.0, 1.0, -1.0), MPoint(1.0, 1.0, -1.0));
	lines.add(MPoint(1.0, 1.0, -1.0), MPoint(1.0, 1.0, 1.0));
	lines.add(MPoint(1.0, 1.0, 1.0), MPoint(-1.0, 1.0, 1.0));
	lines.add(MPoint(-1.0, 1.0, 1.0), MPoint(-1.0, 1.0, -1.0));
	lines.add(MPoint(-1.0, -1.0, -1.0), MPoint(-1.0, 1.0, -1.0));
	lines.add(MPoint(1.0, -1.0, -1.0), MPoint(1.0, 1.0, -1.0));
	lines.add(MPoint(1.0, -1.0, 1.0), MPoint(1.0, 1.0, 1.0));
	lines.add(MPoint(-1.0, -1.0, 1.0), MPoint(-1.0, 1.0, 1.0));
}

LSControllerDrawData::Handle::Handle(const char *name) : name(name)
{
	int fsegment = 60;
	if (strcmp(name, "circle")==0)
	{
		linesArray.resize(1);
		double offsetangle = M_PI / fsegment;
		makeCircle(linesArray[0], fsegment, offsetangle);
	}
	else if (strcmp(name, "cube") == 0)
	{
		linesArray.resize(1);
		makeCube(linesArray[0]);
	}
	else if (strcmp(name, "square") == 0)
	{
		fsegment = 4;
		linesArray.resize(1);
		double offsetangle = M_PI / fsegment;
		makeCircle(linesArray[0], fsegment, offsetangle);
	}
	else if (strcmp(name, "triangle") == 0)
	{
		fsegment = 3;
		linesArray.resize(1);
		makeCircle(linesArray[0], fsegment);
	}
	else if (strcmp(name, "hexagram") == 0)
	{
		fsegment = 3;
		linesArray.resize(1);
		double offsetangle = M_PI / fsegment;
		makeCircle(linesArray[0], fsegment);
		makeCircle(linesArray[0], fsegment, offsetangle);
	}
	else if (strcmp(name, "sphere") == 0)
	{
        Json::Value shapeJson;
        Json::Reader reader;
        reader.parse(sphereStr, shapeJson);
        std::string version = shapeJson["version"].asString();
        std::string name = shapeJson["name"].asString();
        auto loader = LSControllerDrawData::getLoader(version);
        loader(this, shapeJson);
	}
	else if (strcmp(name, "donut") == 0)
	{
        Json::Value shapeJson;
        Json::Reader reader;
        reader.parse(donutStr, shapeJson);
        std::string version = shapeJson["version"].asString();
        std::string name = shapeJson["name"].asString();
        auto loader = LSControllerDrawData::getLoader(version);
        loader(this, shapeJson);
	}
	else if (strcmp(name, "sphereCurve") == 0)
	{
        Json::Value shapeJson;
        Json::Reader reader;
        reader.parse(sphereCurveStr, shapeJson);
        std::string version = shapeJson["version"].asString();
        std::string name = shapeJson["name"].asString();
        auto loader = LSControllerDrawData::getLoader(version);
        loader(this, shapeJson);
	}
}

void LSControllerDrawData::Handle::addWireframe(const MPointArray &lines, const MColor &color)
{
	LSControllerDrawData::DrawData drawData;
	drawData.points = lines;
	linesArray.push_back(drawData);
}

void LSControllerDrawData::Handle::addShaded(const MPointArray &triangles, const MColor &color)
{
	LSControllerDrawData::DrawData drawData;
	drawData.points = triangles;
	trianglesArray.push_back(drawData);
}

LSControllerDrawData::LoaderFunc LSControllerDrawData::getLoader(const std::string &version)
{
	auto it = shapeLoaderImplements.find(version);
	if (it != shapeLoaderImplements.end())
	{
		return it->second;
	}
	return shapeLoaderImplements.begin()->second;
}

LSControllerDrawData::LoaderFuncMap LSControllerDrawData::shapeLoaderImplements = {
	{"1.0.0", makeShapeFromJsonV1_0_0}};

LSControllerDrawData::LSControllerDrawData(const char *name) : MUserData(false)
{
}

void LSControllerDrawData::makeShape(MBoundingBox &bbox, int shapeTypeId, const MMatrix &matrix)
{
	bbox.clear();
	//build lines.
	transformShapeArray(fLines, bbox, LSController::sHandleList[shapeTypeId].linesArray, matrix);
	//build shaded triangles.
	transformShapeArray(fTriangles, bbox, LSController::sHandleList[shapeTypeId].trianglesArray, matrix);
}

void LSControllerDrawData::update(const MDagPath &controllerDag)
{
	LSController *pController = LSController::getController(controllerDag);
	if (pController == nullptr)
	{
		return;
	}
	fColor = pController->getColor();
	int shapeTypeId = pController->getShapeTypeId();
	fMatrix = pController->getMatrix();
	fText = pController->getLabel();
	bool needRebuild = pController->needRebuild();
	//The dagpath change won't triggor rebuild shape.
	//Add dagpath check here.
	if (controllerDag.fullPathName() != fControllerPath)
	{
		needRebuild = true;
		fControllerPath = controllerDag.fullPathName();
	}
	if (needRebuild)
	{
		MBoundingBox bbox;
		makeShape(bbox, shapeTypeId, fMatrix);
		pController->updateBBox(bbox);
	}
}

inline MPoint LSControllerDrawData::getTransformedPoint(const MPoint &preTransformPosition) const
{
	return fMatrix * preTransformPosition;
}

inline MPoint LSControllerDrawData::getTransformedPoint(const double x, const double y, const double z) const
{
	return getTransformedPoint(MPoint(x, y, z));
}
