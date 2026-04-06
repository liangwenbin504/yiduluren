@echo off
chcp 65001 >nul
echo ================================================
echo 仪度六壬综合择日系统
echo ================================================
echo.
echo 正在启动综合择日 GUI 界面...
echo.

python comprehensive_date_selector_gui.py

if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. Python 是否正确安装
    echo 2. tkinter 库是否已安装
    echo 3. 依赖模块是否完整
    echo.
    pause
)
