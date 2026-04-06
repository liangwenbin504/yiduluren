@echo off
chcp 65001 >nul
title 仪度六壬综合择日系统 - 增强版

echo ================================================
echo   仪度六壬综合择日系统 - 增强版
echo   版本：2.0
echo ================================================
echo.
echo 正在启动 GUI 界面...
echo.

cd /d "%~dp0"
python enhanced_date_selector_gui.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo 启动失败！可能的原因：
    echo 1. Python 未安装或未添加到系统路径
    echo 2. 缺少 tkinter 库
    echo 3. 依赖模块缺失
    echo.
    echo 请检查错误信息后重试
    echo ================================================
    pause
)
