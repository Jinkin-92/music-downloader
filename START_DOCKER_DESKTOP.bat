@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Desktop Docker
echo ==========================================
echo.
echo 该模式启动的是桌面版 PyQt 容器，不是 React Web 版。
echo 通过 VNC 访问容器桌面，端口：5901
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo Docker 未运行，请先启动 Docker Desktop。
    pause
    exit /b 1
)

docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo Docker 桌面版启动失败。
    pause
    exit /b 1
)

echo.
echo 已启动桌面版 Docker 容器。
echo 查看日志：
echo   docker-compose logs -f
echo 停止服务：
echo   docker-compose down
echo.
pause
endlocal
