@echo off
setlocal
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%" || goto :project_error

if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul && set "PYTHON=py -3"
)

if not defined PYTHON goto :python_missing

set "PYTHONPATH=%PROJECT_DIR%src"
%PYTHON% -c "import PIL, reportlab" >nul 2>nul || goto :dependencies_missing
%PYTHON% -m xray_mouth.cli %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%

:project_error
echo Error: could not open the XRay Mouth project directory.
pause
exit /b 1

:python_missing
echo Error: Python 3 was not found. Install Python 3.11 or newer, then try again.
pause
exit /b 1

:dependencies_missing
echo Error: Pillow and ReportLab are required but not installed for this Python.
echo Run: python -m pip install -e ".[dev]"
pause
exit /b 1
