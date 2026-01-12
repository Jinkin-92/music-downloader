@echo off
REM Music Downloader Launcher
REM No Chinese characters to avoid encoding issues

cd /d "%~dp0"

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.7+
    pause
    exit /b 1
)

REM Launch application
echo.
echo Starting Music Downloader...
echo.

python run_app.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo Check error messages above
)

echo.
pause
