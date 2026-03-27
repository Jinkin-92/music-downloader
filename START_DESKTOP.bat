@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Desktop
echo ==========================================
echo.
echo 启动 PyQt 本地窗口...
python -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo 桌面版启动失败。请确认：
    echo   1. 已安装 Python 依赖
    echo   2. 已安装 PyQt6
    echo.
    pause
)

endlocal
