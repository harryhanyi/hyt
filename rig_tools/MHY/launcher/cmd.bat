@echo off
pushd %~dp0
:: Check for Python Installation
python --version 2 > nul 2>&1
if "%1"=="" (
set "app=cmd.exe"
) else (
    set "app=%1"
)
if "%MAYA_VERSION%"=="" (
    set "MAYA_VERSION=2020"
)
if "%HOUDINI_VERSION%"=="" (
    set "HOUDINI_VERSION=18.5.596"
)
if errorlevel 1 goto tryPowerShell
python env/env.py %app%
goto:eof
:tryPowerShell
powershell -Command "python --version 2" > nul 2>&1
if errorlevel 1 goto echoNoPython
powershell -Command "python env/env.py %app%"
goto:eof
:echoNoPython
@echo on
@echo "Can't find python. Please add python to your path."
@echo off
@timeout 30
popd
:end
