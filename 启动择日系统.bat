@echo off
chcp 65001 >nul
title 仪度六壬综合择日系统 - 增强版

echo.
echo ================================================
echo   仪度六壬综合择日系统 - 增强版
echo   版本：2.0
echo ================================================
echo.
echo 正在启动 GUI 界面...
echo.
echo 提示：
echo 1. 选择山向（点击 24 山按钮）
echo 2. 选择日期范围
echo 3. 勾选课格类型（如龙德课）
echo 4. 点击"开始择日"按钮
echo.
echo 按任意键启动...
pause >nul

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
    echo 错误详情：
    python enhanced_date_selector_gui.py
    echo ================================================
    pause
)
