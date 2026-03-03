@echo off
chcp 65001 >nul
title 后端日志监控

echo ========================================
echo 后端日志实时监控
echo ========================================
echo.

set LOG_DIR=%~dp0logs

if not exist "%LOG_DIR%" (
    echo 日志目录不存在: %LOG_DIR%
    echo 请先启动后端服务
    pause
    exit /b
)

echo 监控文件: %LOG_DIR%\backend.log (后端API日志)
echo 按 Ctrl+C 停止监控
echo ========================================
echo.

powershell -Command "Get-Content '%LOG_DIR%\backend.log' -Wait -Tail 50 -Encoding UTF8"
