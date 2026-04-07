@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Legacy Desktop Docker
echo ==========================================
echo.
echo This mode starts the legacy PyQt desktop container over VNC.
echo It does NOT start the current React Web UI.
echo VNC port: 5901
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

docker compose -f docker-compose.legacy-desktop.yml up -d --build

if errorlevel 1 (
    echo.
    echo Legacy desktop Docker startup failed.
    pause
    exit /b 1
)

echo.
echo Legacy desktop container started.
echo Logs:
echo   docker compose -f docker-compose.legacy-desktop.yml logs -f
echo Stop:
echo   docker compose -f docker-compose.legacy-desktop.yml down
echo.
pause
endlocal
