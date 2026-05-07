@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Desktop
echo ==========================================
echo.
echo Starting PyQt desktop window...
"C:\Python313\python.exe" -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo Desktop version failed. Please check:
    echo   1. Python dependencies installed
    echo   2. PyQt6 installed
    echo.
    pause
)

endlocal