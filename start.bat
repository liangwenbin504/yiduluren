@echo off
chcp 65001 >nul
echo ========================================
echo   仪度六壬择日软件
echo ========================================
echo.
echo 正在启动程序...
echo.
cd /d "%~dp0src"
python main.py
pause
