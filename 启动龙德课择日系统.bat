@echo off
chcp 65001 >nul
title 龙德课到山到向择日系统

echo ================================================================================
echo                         龙德课到山到向择日系统
echo ================================================================================
echo.
echo 功能说明：
echo   1. 龙德课判断（太岁/月将乘贵人发用）
echo   2. 贵人禄马到山到向分析
echo   3. 二十四山支持
echo   4. 智能筛选吉日良辰
echo.
echo 请选择启动方式：
echo.
echo   [1] 启动图形界面 (GUI)
echo   [2] 运行测试脚本
echo   [3] 查看使用手册
echo   [4] 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 正在启动图形界面...
    python src\ui\long_de_ke_gui.py
    if errorlevel 1 (
        echo.
        echo 启动失败！请检查 Python 环境是否正确安装。
        pause
    )
) else if "%choice%"=="2" (
    echo.
    echo 正在运行测试脚本...
    python src\engine\long_de_ke_selector.py
    if errorlevel 1 (
        echo.
        echo 测试失败！请查看错误信息。
        pause
    )
) else if "%choice%"=="3" (
    echo.
    echo 正在打开使用手册...
    if exist "docs\龙德课到山到向系统使用手册.md" (
        start docs\龙德课到山到向系统使用手册.md
    ) else (
        echo 未找到使用手册文件！
        pause
    )
) else if "%choice%"=="4" (
    exit
) else (
    echo.
    echo 无效的选项！请按 1-4 选择。
    pause
)

goto :eof
