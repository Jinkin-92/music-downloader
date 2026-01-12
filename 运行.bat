@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pyqt_ui.main
pause
