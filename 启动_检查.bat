@echo off
setlocal enabledelayedexpansion

echo ======================================
echo 启动音乐下载器
echo ======================================
echo.

rem 切换到项目目录
cd /d "%~dp0"

rem 检查 Python
echo [1/4] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo 请先安装 Python 3.7+
    echo.
    pause
    exit /b 1
)

rem 检查 PyQt6
echo [2/4] 检查 PyQt6...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [警告] PyQt6 未安装，正在安装...
    pip install PyQt6
    if errorlevel 1 (
        echo [错误] PyQt6 安装失败
        pause
        exit /b 1
    )
)

rem 检查 musicdl
echo [3/4] 检查 musicdl...
python -c "import musicdl" >nul 2>&1
if errorlevel 1 (
    echo [警告] musicdl 未安装，正在安装...
    pip install musicdl
    if errorlevel 1 (
        echo [错误] musicdl 安装失败
        pause
        exit /b 1
    )
)

rem 检查关键文件
echo [4/4] 检查关键文件...
set missing_files=0

if not exist "pyqt_ui\main.py" (
    echo [错误] pyqt_ui\main.py 不存在
    set missing_files=1
)

if not exist "pyqt_ui\workers.py" (
    echo [错误] pyqt_ui\workers.py 不存在
    set missing_files=1
)

if not exist "pyqt_ui\batch\models.py" (
    echo [错误] pyqt_ui\batch\models.py 不存在
    set missing_files=1
)

if not exist "pyqt_ui\batch\match_switcher_dialog.py" (
    echo [错误] pyqt_ui\batch\match_switcher_dialog.py 不存在
    set missing_files=1
)

if %missing_files%==1 (
    echo.
    echo [失败] 缺少关键文件，请检查项目结构
    pause
    exit /b 1
)

echo.
echo [成功] 所有检查通过！
echo.
echo [启动] 启动音乐下载器...
echo ======================================
echo.

python -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo [错误] 程序启动失败！
    echo.
    echo 请检查：
    echo   1. 错误信息（上方）
    echo   2. Python 版本是否为 3.7+
    echo   3. PyQt6 是否已正确安装
    echo   4. musicdl 是否已正确安装
    echo   5. 查看日志文件 logs/app.log
)

echo.
pause
