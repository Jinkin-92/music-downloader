@echo off
echo ==========================================
echo   Music Downloader Web - Quick Start
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    echo Please start Docker Desktop first
    pause
    exit /b 1
)

REM Create data directories
if not exist "data\musicdl_outputs" mkdir "data\musicdl_outputs"
if not exist "data\logs" mkdir "data\logs"

echo Building and starting services...
echo This may take 5-10 minutes (first build)
echo.

REM Build and start
docker-compose -f docker-compose.web.yml up -d --build

if errorlevel 1 (
    echo.
    echo Error: Startup failed!
    pause
    exit /b 1
)

echo.
echo Waiting for services to start...
timeout /t 20 /nobreak >nul

echo.
echo ==========================================
echo   Services Started Successfully!
echo ==========================================
echo.
echo Access URLs:
echo   - Web UI:  http://localhost
echo   - API Docs: http://localhost:8000/docs
echo.
echo Press any key to open browser...
pause >nul

start http://localhost

echo.
echo To view logs:
echo   docker-compose -f docker-compose.web.yml logs -f
echo.
echo To stop services:
echo   docker-compose -f docker-compose.web.yml down
echo.
pause
