@echo off
setlocal
cd /d "%~dp0"

:menu
cls
echo ==========================================
echo   Music Downloader Launcher
echo ==========================================
echo.
echo   1. 启动 Web 版（本地前后端）
echo   2. 启动桌面版（PyQt 本地窗口）
echo   3. 启动桌面版 Docker/VNC（docker-compose.yml）
echo   4. 退出
echo.
set /p choice=请选择启动方式 [1-4]:

if "%choice%"=="1" call START_WEB.bat & goto end
if "%choice%"=="2" call START_DESKTOP.bat & goto end
if "%choice%"=="3" call START_DOCKER_DESKTOP.bat & goto end
if "%choice%"=="4" goto end

echo.
echo 输入无效，请重新选择。
timeout /t 2 /nobreak >nul
goto menu

:end
endlocal
