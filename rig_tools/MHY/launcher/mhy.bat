@echo off

if "%1" == "--help" (
start https://git.code.oa.com/MHY/launcher
goto :end
)
pushd %~dp0

set RESTVAR=%*
set pipe_line=%cd%\default.pipeline
set workspace=""
if NOT "%1" == "-ws" goto :skip_pipeline_parse
set RESTVAR=
set workspace=%2
if "%workspace%" == "" (
echo Missing workspace argument
exit /b 1
)
shift
shift
:start_shift
if "%1"=="" goto skip_pipeline_parse
set RESTVAR=%RESTVAR% %1
shift
goto start_shift

:skip_pipeline_parse

echo Launching MHY environment with pipeline:  ""%pipe_line%" ...

python py/launcher_env_builder.py -p "%pipe_line%" -ws %workspace%
popd
set ORIGINALPATH=%cd%
pushd %~dp0

setlocal enableDelayedExpansion
for /f "eol=# delims=" %%a in (.env_temp) do (
for /f "tokens=1,2 delims=?" %%G in ("%%a") do (
	set %%G=%%H
)
)
del .env_temp
popd

call %RESTVAR%
endlocal

cd %ORIGINALPATH%
:end


