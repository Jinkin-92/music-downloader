@echo off
chcp 65001 >nul
title 音乐下载器 Web端启动 (新版本)

echo ========================================
echo 音乐下载器 Web端启动 (新版本)
echo ========================================
echo.

REM 获取项目目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo [1/5] 强制清理所有旧进程...
echo 使用 WMIC 清理所有 uvicorn 进程...
wmic process where "CommandLine like '%%uvicorn%%' and CommandLine like '%%8002%%'" delete 2>nul
timeout /t 3 /nobreak >nul

echo.
echo [2/5] 确认8002端口已清空...
netstat -ano | findstr ":8002.*LISTENING"
if errorlevel 1 (
    echo 端口8002已清空，可以继续
) else (
    echo 端口仍被占用，强制清理所有Python进程...
    taskkill /IM python.exe /F 2>nul
    timeout /t 3 /nobreak >nul
)

echo.
echo [3/5] 启动后端服务 (端口8002)...
echo 使用 uvicorn 启动，支持热重载
start "音乐下载器-后端" cmd /k "cd /d "%PROJECT_DIR%\backend" && chcp 65001 && echo ======================================== && echo 后端启动中... (使用 uvicorn) && echo ======================================== && python -m uvicorn main:app --host 0.0.0.0 --port 8002"
echo 等待后端启动...
timeout /t 8 /nobreak >nul

echo.
echo [4/5] 启动前端服务 (端口5173)...
start "音乐下载器-前端" cmd /k "cd /d "%PROJECT_DIR%\frontend" && chcp 65001 && echo ======================================== && echo 前端启动中... && echo ======================================== && npm run dev"
echo 等待前端启动...
timeout /t 8 /nobreak >nul

echo.
echo [5/5] 打开Web浏览器...
start http://localhost:5173/playlist

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo 后端地址: http://localhost:8002
echo 前端地址: http://localhost:5173
echo API文档: http://localhost:8002/docs
echo ========================================
echo.
echo 查看后端日志请检查 "音乐下载器-后端" 窗口
echo 查看前端日志请检查 "音乐下载器-前端" 窗口
echo.
echo 如需重启，请先关闭所有窗口，然后重新运行此脚本
echo.
pause
