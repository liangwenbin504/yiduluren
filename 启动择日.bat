@echo off
chcp 65001 >nul
title 仪度六壬综合择日系统 - 增强版

cls
echo.
echo ================================================
echo   仪度六壬综合择日系统 - 增强版 v2.0
echo ================================================
echo.
echo 正在启动程序，请稍候...
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.6+
    pause
    exit /b 1
)

echo [√] Python 已安装
echo.

REM 启动主程序
echo [提示] 正在启动择日系统...
echo.
start "仪度六壬择日系统" python enhanced_date_selector_gui.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo [错误] 启动失败！
    echo 可能原因：
    echo 1. Python 未安装或未添加到系统路径
    echo 2. 缺少 tkinter 库
    echo 3. 程序文件损坏
    echo ================================================
    pause
) else (
    echo [√] 程序已成功启动！
    echo.
    echo 操作步骤：
    echo 1. 选择山向 ^（点击 24 山按钮^)
    echo 2. 选择日期范围
    echo 3. 勾选课格类型 ^（如龙德课^)
    echo 4. 点击"开始择日"
    echo 5. 双击结果查看详细信息
    echo.
    echo 按任意键关闭此窗口...
    pause >nul
)
