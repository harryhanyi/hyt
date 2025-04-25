@echo off
set "output_modules_path=%1"
if not exist "%output_modules_path%" mkdir "%output_modules_path%"

set "current_module_path=%~dp0"
set "search=<PATH>"
set "replace=%current_module_path%"

set "input_mod=%~dp0/mhy_face.rawmod"
set "output_mod=%output_modules_path%/mhy_face.mod"

setlocal EnableExtensions EnableDelayedExpansion
break>"%output_mod%"
REM replace <PATH> with user's absolute path
for /f "delims=" %%i in ('type "%input_mod%"') do (
    set "oldline=%%i"
    set "newline=!oldline:%search%=%replace%!"
    echo !newline!>>"%output_mod%"
)
endlocal

rem current_module_path has '/' as ending
set "MAYA_SHELF_PATH=%MAYA_SHELF_PATH%;%current_module_path%resource/shelves"