@echo off
if "%1" == "" (
    set MAYA_VERSION=2022
    echo %MAYA_VERSION%
) else (
    set MAYA_VERSION=%1
)

:: Add the current directory to the PATH
set PATH=%PATH%;%~dp0

:: Add cmt to maya module
set MAYA_MODULE_PATH=D:\chad\cmt;%MAYA_MODULE_PATH%

:: Add local tools
set PYTHONPATH=D:\hyt\rig_tools;%PYTHONPATH%

mhy maya