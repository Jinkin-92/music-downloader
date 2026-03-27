@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Web
echo ==========================================
echo.
echo START.bat 默认启动当前主界面：Web 版
echo 如需启动遗留桌面版，请使用：
echo   START_DESKTOP.bat
echo   START_DOCKER_DESKTOP.bat
echo.

call START_WEB.bat

endlocal
