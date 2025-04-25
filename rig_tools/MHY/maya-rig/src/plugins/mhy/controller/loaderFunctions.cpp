#include "miControllerDrawData.h"
#include <algorithm>
#include <json/json.h>
namespace
{
	template <typename ValueType>
	inline bool loadFloat3(ValueType &value, const Json::Value &jsonValue)
	{
		if (!jsonValue.isArray())
		{
			return false;
		}
		if (jsonValue[0].isNumeric() && jsonValue[1].isNumeric() && jsonValue[2].isNumeric())
		{
			value = ValueType(jsonValue[0].asFloat(), jsonValue[1].asFloat(), jsonValue[2].asFloat());
		}
		else
		{
			return false;
		}
		return true;
	}

	template <typename ValueType>
	inline bool loadFloat4(ValueType &value, const Json::Value &jsonValue)
	{
		bool result = true;
		if (!jsonValue.isArray())
		{
			result = false;
		}
		if (jsonValue.isArray() && jsonValue.size() >= 4)
		{
			value = ValueType(jsonValue[0].asFloat(), jsonValue[1].asFloat(), jsonValue[2].asFloat(), jsonValue[3].asFloat());
		}
		else
		{
			result = false;
		}
		return result;
	}

	bool loadVertices(MPointArray &points, const Json::Value &jsonPointArray)
	{
		if (!jsonPointArray.isArray())
		{
			return false;
		}
		bool result = true;
		Json::ArrayIndex pointNum = jsonPointArray.size();
		points.setLength(pointNum);
		for (Json::ArrayIndex i = 0; i < pointNum; ++i)
		{
			const Json::Value &jsonPoint = jsonPointArray[i];
			result = result && loadFloat3(points[i], jsonPoint);
		}
		return result;
	}
}

bool makeShapeFromJsonV1_0_0(LSControllerDrawData::Handle *handle, const Json::Value &jsonValue)
{
	bool result = true;
	auto shapes = jsonValue["shapes"];
	if (shapes.isArray())
	{
		for (auto shape : shapes)
		{
			auto wireframe = shape["wireframe"];
			auto shaded = shape["shaded"];
			auto colorValue = shape["color"];
			MColor color(0.0, 0.0, 1.0);
			//color is optional value. So don't need check loadFloat3 result.
			loadFloat3(color, colorValue);
			MPointArray vertices;
			// add wireframe geometry
			if (!wireframe.isNull())
			{
				if (!loadVertices(vertices, wireframe))
				{
					return false;
				}
				if (vertices.length() != 0)
				{
					handle->addWireframe(vertices, color);
				}
			}
			if (!shaded.isNull())
			{
				// add shaded geometry
				if (!loadVertices(vertices, shaded))
				{
					return false;
				}
				if (vertices.length() != 0)
				{
					handle->addShaded(vertices, color);
				}
			}
		}
	}
	return result;
}
