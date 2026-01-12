@echo off
REM Music Downloader Launcher
REM UTF-8 encoding fix included

REM Set UTF-8 code page for Chinese characters
chcp 65001 >nul 2>&1

REM Change to script directory
cd /d "%~dp0"

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.7+ from https://www.python.org
    pause
    exit /b 1
)

REM Launch application
echo.
echo Starting Music Downloader...
echo.

REM Use Python launcher (more reliable than batch file)
python run_app.py

REM If fallback needed, uncomment below:
REM python -m pyqt_ui.main

pause
