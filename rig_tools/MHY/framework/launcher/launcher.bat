@echo off

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

REM Install all packages listed in requirements.txt
python -m pip install -r requirements.txt

rem Run script
cd /d "%~dp0core\framework"
start /B python launcher.py


