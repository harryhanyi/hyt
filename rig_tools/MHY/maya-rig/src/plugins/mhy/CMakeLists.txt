cmake_minimum_required(VERSION 3.16)
cmake_policy(SET CMP0091 NEW)
project(mhy)

set(PROJECT_NAME mhy)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(Maya REQUIRED)

set(CMAKE_INSTALL_PREFIX ${CMAKE_CURRENT_BINARY_DIR}/../output/${MAYA_VERSION})

file(GLOB SOURCE_FILES plugin.cpp controller/*.cpp constraint/*.cpp viewportPicker/*.cpp tensionNode/*.cpp angleSliceSolver/*.cpp controller/*.h constraint/*.h viewportPicker/*.h tensionNode/*.h angleSliceSolver/*.h )

include_directories(${MAYA_INCLUDE_DIR} ${INCLUDE_DIRS})
link_directories(${MAYA_LIBRARY_DIR})
add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES})
target_link_libraries(${PROJECT_NAME} ${MAYA_LIBRARIES} ${JSONCPP_LIBRARIES} ${PACKAGE_STATIC_LIBS})

MAYA_PLUGIN(${PROJECT_NAME})
#install(TARGETS ${PROJECT_NAME} DESTINATION blur/plug-ins)
if (MSVC)
    # remove default warning level from CMAKE_CXX_FLAGS_INIT
    set(CMAKE_CXX_FLAGS_INIT ${CMAKE_CXX_FLAGS_INIT} /DVersion=${VersionOutput})
    # /bigobj - some object files become very large so we need this
    # When compile the debug version of mhy,
    # demBonesCmd.cpp : fatal error C1128: number of sections exceeded object file format limit: compile with /bigobj
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
    set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT ${PROJECT_NAME})
    message(STATUS "MSVC_RUNTIME_LIBRARY=${MSVC_RUNTIME_LIBRARY}")
    set_property(TARGET ${PROJECT_NAME} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    set_property(TARGET ${PROJECT_NAME} PROPERTY VS_DEBUGGER_COMMAND "${MAYA_LOCATION}/bin/maya.exe")
endif()
