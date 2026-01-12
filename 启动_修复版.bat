@echo off
REM 设置UTF-8编码以正确显示中文
chcp 65001 >nul 2>&1

cd /d "%~dp0"

echo ======================================
echo 启动音乐下载器
echo ======================================
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo.
echo [2/4] Checking dependencies...
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [WARNING] PyQt6 not installed, installing...
    pip install PyQt6
)

python -c "import musicdl" 2>nul
if errorlevel 1 (
    echo [WARNING] musicdl not installed, installing...
    pip install musicdl
)

echo.
echo [3/4] Checking files...
if not exist "pyqt_ui\main.py" (
    echo [ERROR] pyqt_ui\main.py not found!
    pause
    exit /b 1
)

if not exist "pyqt_ui\workers.py" (
    echo [ERROR] pyqt_ui\workers.py not found!
    pause
    exit /b 1
)

if not exist "pyqt_ui\batch\models.py" (
    echo [ERROR] pyqt_ui\batch\models.py not found!
    pause
    exit /b 1
)

if not exist "pyqt_ui\batch\match_switcher_dialog.py" (
    echo [ERROR] pyqt_ui\batch\match_switcher_dialog.py not found!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All checks passed!
echo.
echo [4/4] Starting application...
echo ======================================
echo.

python -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start!
    echo.
    echo Please check:
    echo 1. Python version 3.7+
    echo 2. PyQt6 installed correctly
    echo 3. musicdl installed correctly
    echo 4. Error messages above
)

echo.
pause
