@echo off
chcp 65001 >nul
title 重启服务 - 加载所有修复

echo ========================================
echo 重启服务 - 加载所有修复
echo ========================================
echo.
echo 本脚本将：
echo 1. 强制终止旧的 Python 和 Node 进程
echo 2. 启动后端服务（包含 download_url 修复）
echo 3. 启动前端服务（包含相似度分解UI）
echo 4. 打开浏览器到批量下载页面
echo.

REM 获取项目目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM ==================== 步骤1: 清理旧进程 ====================
echo [1/5] 清理旧进程...
echo.

REM 使用 WMIC 清理 uvicorn (端口8003)
echo 清理后端 uvicorn 进程...
wmic process where "CommandLine like '%%uvicorn%%' and CommandLine like '%%main:app%%'" delete 2>nul
timeout /t 2 /nobreak >nul

REM 清理前端 vite (端口5173)
echo 清理前端 vite 进程...
wmic process where "CommandLine like '%%vite%%' and CommandLine like '%%5173%%'" delete 2>nul
timeout /t 2 /nobreak >nul

REM 验证端口已清空
echo 验证端口状态...
netstat -ano | findstr ":8003.*LISTENING" >nul
if errorlevel 1 (
    echo [OK] 端口8003已清空
) else (
    echo [WARN] 端口8003仍被占用，强制清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8003.*LISTENING"') do (
        taskkill /PID %%a /F 2>nul
    )
)

netstat -ano | findstr ":5173.*LISTENING" >nul
if errorlevel 1 (
    echo [OK] 端口5173已清空
) else (
    echo [WARN] 端口5173仍被占用，强制清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
        taskkill /PID %%a /F 2>nul
    )
)

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   修复已加载！
echo ========================================
echo.
echo 后端修复:
echo   - download_url 字段保存
echo   - 直接使用URL下载（不重新搜索）
echo   - 35秒时长过滤
echo   - 相似度分解计算
echo.
echo 前端修复:
echo   - 相似度分解Tooltip显示
echo   - 下载路径快捷选择
echo   - 移除无效浏览按钮
echo.
echo ========================================
echo.

REM ==================== 步骤2: 启动后端 ====================
echo [2/5] 启动后端服务 (端口8003)...
start "音乐下载器-后端" cmd /k "cd /d "%PROJECT_DIR%\backend" && chcp 65001 && echo. && echo ======================================== && echo 后端服务启动中... && echo 包含以下修复: && echo - download_url 字段 && echo - 直接下载功能 && echo - 35秒时长过滤 && echo - 相似度分解 && echo ======================================== && echo. && python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"

echo 等待后端启动...
timeout /t 10 /nobreak >nul

REM 验证后端启动
curl -s http://localhost:8003/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] 后端可能未完全启动，请检查 "音乐下载器-后端" 窗口
) else (
    echo [OK] 后端服务已启动
)

REM ==================== 步骤3: 启动前端 ====================
echo.
echo [3/5] 启动前端服务 (端口5173)...
start "音乐下载器-前端" cmd /k "cd /d "%PROJECT_DIR%\frontend" && chcp 65001 && echo. && echo ======================================== && echo 前端服务启动中... && echo 包含以下修复: && echo - 相似度分解Tooltip && echo - 下载路径快捷选择 && echo - 浏览按钮已移除 && echo ======================================== && echo. && npm run dev"

echo 等待前端启动...
timeout /t 10 /nobreak >nul

REM ==================== 步骤4: 打开浏览器 ====================
echo.
echo [4/5] 打开浏览器...
timeout /t 3 /nobreak >nul
start http://localhost:5173/batch

REM ==================== 完成 ====================
echo.
echo [5/5] 启动完成！
echo.
echo ========================================
echo   所有修复已加载！
echo ========================================
echo.
echo 服务地址:
echo   后端: http://localhost:8003
echo   前端: http://localhost:5173
echo   API文档: http://localhost:8003/docs
echo.
echo 修复内容:
echo   [后端]
echo   1. download_url 字段 - 直接下载
echo   2. 35秒时长过滤 - 过滤试听片段
echo   3. 相似度分解 - name/singer/album
echo.
echo   [前端]
echo   1. 相似度Tooltip - 显示详细分解
echo   2. 下载路径输入 - 快捷选择
echo   3. 浏览按钮移除 - UI优化
echo.
echo 验证方法:
echo   1. 输入歌曲搜索
echo   2. Hover相似度标签查看分解
echo   3. 选择下载目录（快捷选择）
echo   4. 点击下载验证
echo.
echo ========================================
echo.
echo 查看日志:
echo   后端: 检查 "音乐下载器-后端" 窗口
echo   前端: 检查 "音乐下载器-前端" 窗口
echo.
pause
