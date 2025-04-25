#pragma once
#include <maya/MString.h>
#include <maya/MColor.h>
#include <maya/MUserData.h>
#include <maya/MPointArray.h>
#include <Maya/MBoundingBox.h>
#include <Maya/MDagPath.h>
#include <Maya/MFnDependencyNode.h>
#include <Maya/MMatrix.h>
#include <functional>
#include <map>
#include <json/json.h>
class LSController;
class LSControllerDrawData : public MUserData
{
public:
	struct DrawData
	{
		typedef std::vector<DrawData> List;
		MPointArray points;
		void add(const MPoint &p0, const MPoint &p1)
		{
			points.append(p0);
			points.append(p1);
		}
	};
	class Handle
	{
	public:
		typedef std::vector<Handle> List;
		Handle(const char *name);
		void addWireframe(const MPointArray &lines, const MColor &color);
		void addShaded(const MPointArray &triangles, const MColor &color);
		MString name;
		DrawData::List linesArray;
		DrawData::List trianglesArray;

	private:
		static void makeCube(DrawData &line);
		static void makeCircle(DrawData &line, const int segment, const double offsetAngle = 0.0);
	};
	typedef std::function<bool(LSControllerDrawData::Handle *, const Json::Value &)> LoaderFunc;
	LSControllerDrawData(const char *name = "circle");
	~LSControllerDrawData() override{};
	void update(const MDagPath &controllerDag);
	MColor fColor;
	MMatrix fMatrix;
	DrawData::List fLines;
	DrawData::List fTriangles;
	MString fText;
	static LoaderFunc getLoader(const std::string &version);
	MString fControllerPath;

private:
	typedef std::map<std::string, LoaderFunc> LoaderFuncMap;
	static LoaderFuncMap shapeLoaderImplements;
	MPoint getTransformedPoint(const MPoint &preTransformPosition) const;
	MPoint getTransformedPoint(const double x, const double y, const double z) const;
	void makeShape(MBoundingBox &bbox, int shapeTypeId, const MMatrix &matrix);
};
