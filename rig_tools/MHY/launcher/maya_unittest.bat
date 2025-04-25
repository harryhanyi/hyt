@echo off
if "%1" == "" (
    set MAYA_VERSION=2022
    echo %MAYA_VERSION%
) else (
    set MAYA_VERSION=%1
)
mhy maya_test
