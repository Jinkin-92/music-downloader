@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader - One-click start
echo ==========================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python 3.10+ not found
    echo.
    echo Please install Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check dependencies
"C:\Python313\python.exe" -c "import fastapi, uvicorn, requests, musicdl" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing dependencies...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo.
        echo [Error] Dependency installation failed!
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
    echo.
)

echo ==========================================
echo   Starting services...
echo ==========================================
echo.
echo Visit after startup: http://localhost:8003
echo.

:: Start backend (static frontend included)
start "Music Downloader" cmd /k "cd /d %~dp0 && \"C:\Python313\python.exe\" -m uvicorn backend.main:app --host 0.0.0.0 --port 8003"

:: Wait for service to start
echo Waiting for service to start...
timeout /t 5 /nobreak >nul

:: Open browser
start http://localhost:8003

echo.
echo Service started!
echo To stop, close the black command window above.
echo.
pause
endlocal