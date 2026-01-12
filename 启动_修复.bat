@echo off
setlocal enabledelayedexpansion

echo ======================================
echo 启动音乐下载器
echo ======================================
echo.

rem 切换到项目目录
cd /d "%~dp0"

rem 尝试使用venv中的Python
set PYTHON_CMD=python

if exist "venv\Scripts\python.exe" (
    echo [信息] 检测到venv环境
    set PYTHON_CMD=venv\Scripts\python.exe
) else (
    echo [信息] 未检测到venv，使用系统Python
)

rem 检查关键文件
echo [检查] 验证核心文件...
set /a file_check=0

if exist "pyqt_ui\main.py" (
    echo [OK] pyqt_ui\main.py
    set /a file_check+=1
)

if exist "pyqt_ui\workers.py" (
    echo [OK] pyqt_ui\workers.py
    set /a file_check+=1
)

if exist "pyqt_ui\batch\models.py" (
    echo [OK] pyqt_ui\batch\models.py
    set /a file_check+=1
)

if exist "pyqt_ui\batch\match_switcher_dialog.py" (
    echo [OK] pyqt_ui\batch\match_switcher_dialog.py
    set /a file_check+=1
)

if %file_check% LSS 4 (
    echo.
    echo [错误] 缺少核心文件！
    echo 期望文件：
    echo   - pyqt_ui\main.py
    echo   - pyqt_ui\workers.py
    echo   - pyqt_ui\batch\models.py
    echo   - pyqt_ui\batch\match_switcher_dialog.py
    echo.
    pause
    exit /b 1
)

rem 检查依赖
echo [检查] 验证依赖包...
%PYTHON_CMD% -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [警告] PyQt6未安装，正在安装...
    %PYTHON_CMD% -m pip install PyQt6
    if errorlevel 1 (
        echo [错误] PyQt6安装失败
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -c "import musicdl" 2>nul
if errorlevel 1 (
    echo [警告] musicdl未安装，正在安装...
    %PYTHON_CMD% -m pip install musicdl
    if errorlevel 1 (
        echo [错误] musicdl安装失败
        pause
        exit /b 1
    )
)

echo.
echo [成功] 所有检查通过！
echo.
echo [启动] 启动音乐下载器...
echo ======================================
echo.

rem 启动程序
%PYTHON_CMD% -m pyqt_ui.main

if errorlevel 1 (
    echo.
    echo [错误] 程序启动失败！
    echo.
    echo 请检查：
    echo   1. Python版本是否为3.7+
    echo   2. PyQt6是否已正确安装
    echo   3. musicdl是否已正确安装
    echo   4. 查看日志文件 logs/app.log
)

echo.
pause
