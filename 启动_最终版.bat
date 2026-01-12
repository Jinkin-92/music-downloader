@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo 启动音乐下载器（最终版）
echo ======================================
echo.

echo [检查] 验证Python和依赖...
python --version
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [错误] PyQt6 未安装
    pause
    exit /b 1
)

python -c "import musicdl" 2>nul
if errorlevel 1 (
    echo [错误] musicdl 未安装
    pause
    exit /b 1
)

echo.
echo [成功] 所有依赖已就绪！
echo.
echo [启动] 启动音乐下载器...
echo ======================================
echo.

python -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo.
    pause
) else (
    echo.
    echo [成功] 程序已启动！
    echo.
    pause
)
