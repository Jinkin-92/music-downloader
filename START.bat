@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Web
echo ==========================================
echo.
echo Starting:
echo   - Backend FastAPI: http://localhost:8003
echo   - Frontend Vite:    http://localhost:5173
echo.
echo For PyQt desktop version, use:
echo   START_DESKTOP.bat
echo.

start "Music Downloader Backend" cmd /k "cd /d %~dp0 && \"C:\Python313\python.exe\" -m uvicorn backend.main:app --host 0.0.0.0 --port 8003"
start "Music Downloader Frontend" cmd /k "cd /d %~dp0 && npm --prefix frontend run dev"

echo Waiting for services to start...
timeout /t 8 /nobreak >nul

start http://localhost:5173

echo.
echo Web frontend/backend started in new windows.
echo If frontend dependencies not installed, run first:
echo   npm --prefix frontend install
echo.
pause
endlocal