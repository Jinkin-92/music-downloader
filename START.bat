@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Music Downloader Web
echo ==========================================
echo.
echo 将启动：
echo   - 后端 FastAPI: http://localhost:8003
echo   - 前端 Vite:    http://localhost:5173
echo.
echo 如需启动 PyQt 桌面版，请使用：
echo   START_DESKTOP.bat
echo.

start "Music Downloader Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8003"
start "Music Downloader Frontend" cmd /k "cd /d %~dp0 && npm --prefix frontend run dev"

echo 等待服务启动...
timeout /t 8 /nobreak >nul

start http://localhost:5173

echo.
echo 已在新窗口中启动 Web 前后端。
echo 如果前端依赖尚未安装，请先执行：
echo   npm --prefix frontend install
echo.
pause
endlocal
