@echo off
echo ======================================
echo 启动音乐下载器
echo ======================================
echo.

cd /d "%~dp0"

echo [检查1] 检查Python...
python --version
if errorlevel 1 (
    echo [错误] Python未安装或不在PATH中
    pause
    exit /b 1
)

echo.
echo [检查2] 检查依赖...
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [警告] PyQt6未安装，正在安装...
    pip install PyQt6
)

python -c "import musicdl" 2>nul
if errorlevel 1 (
    echo [警告] musicdl未安装，正在安装...
    pip install musicdl
)

echo.
echo [检查3] 检查文件完整性...
if not exist "pyqt_ui\main.py" (
    echo [错误] pyqt_ui\main.py 不存在！
    pause
    exit /b 1
)

if not exist "pyqt_ui\workers.py" (
    echo [错误] pyqt_ui\workers.py 不存在！
    pause
    exit /b 1
)

if not exist "pyqt_ui\batch\models.py" (
    echo [错误] pyqt_ui\batch\models.py 不存在！
    pause
    exit /b 1
)

if not exist "pyqt_ui\batch\match_switcher_dialog.py" (
    echo [错误] pyqt_ui\batch\match_switcher_dialog.py 不存在！
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
    echo 1. Python版本是否为3.7+
    echo 2. PyQt6是否已正确安装
    echo 3. musicdl是否已正确安装
    echo 4. 查看上面的错误信息
)

echo.
pause
