@echo off
REM ========================================
REM 歌单导入完整闭环E2E测试运行脚本
REM ========================================

SETLOCAL EnableDelayedExpansion

echo.
echo ========================================
echo 歌单导入完整闭环E2E测试
echo ========================================
echo.
echo 测试歌单: https://music.163.com/m/playlist?id=6922195323&creatorId=610906171
echo.

REM 检查Node.js
echo [1/5] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)
echo ✅ Node.js环境正常

REM 检查后端服务
echo.
echo [2/5] 检查后端服务...
curl -s http://localhost:8002/docs >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 后端服务未运行
    echo 请先启动后端: cd backend ^&^& python -m uvicorn main:app --port 8002
    pause
    exit /b 1
)
echo ✅ 后端服务运行中 (http://localhost:8002)

REM 检查前端服务
echo.
echo [3/5] 检查前端服务...
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 前端服务未运行
    echo 请先启动前端: cd frontend ^&^& npm run dev
    pause
    exit /b 1
)
echo ✅ 前端服务运行中 (http://localhost:5173)

REM 安装依赖
echo.
echo [4/5] 检查并安装依赖...
cd /d "%~dp0"
if not exist "node_modules" (
    echo 首次运行，安装依赖...
    call npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)
echo ✅ 依赖检查完成

REM 创建截图目录
if not exist "screenshots" mkdir screenshots

REM 运行测试
echo.
echo [5/5] 开始运行E2E测试...
echo.
echo ========================================
echo 测试场景:
echo   1. 音乐源默认选择验证
echo   2. 歌单URL解析和表格显示
echo   3. 批量搜索和相似度显示验证
echo   4. 下载按钮和路径输入框验证
echo   5. 完整下载流程验证 (仅前3首)
echo   6. 候选源切换功能验证
echo   7. 错误处理和恢复
echo   8. 完整闭环流程验证 (仅前2首)
echo ========================================
echo.
echo 预计耗时: 10-15分钟
echo.

REM 询问运行模式
set /p MODE="选择运行模式 (1=正常 2=UI模式 3=调试模式): "

if "%MODE%"=="2" (
    echo.
    echo 🎨 启动UI模式...
    call npx playwright test playlist-complete-flow.spec.ts --ui
) else if "%MODE%"=="3" (
    echo.
    echo 🐛 启动调试模式...
    call npx playwright test playlist-complete-flow.spec.ts --debug
) else (
    echo.
    echo 🚀 启动正常模式...
    call npx playwright test playlist-complete-flow.spec.ts
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo ❌ 测试失败
    echo ========================================
    echo.
    echo 请查看测试报告:
    echo   npm run test:e2e:report
    echo.
    echo 或查看截图:
    echo   screenshots\
    echo.
) else (
    echo.
    echo ========================================
    echo ✅ 所有测试通过
    echo ========================================
    echo.
    echo 查看测试报告:
    echo   npm run test:e2e:report
    echo.
    echo 查看截图:
    echo   screenshots\
    echo.
)

pause
