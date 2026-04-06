@echo off
chcp 65001 >nul
echo ================================================
echo 九宗门起课法 - 720 课例关联查看器
echo ================================================
echo.
echo 正在启动查看器...
python view_jiu_zong_men_720.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. Python 是否安装
    echo 2. tkinter 模块是否可用
    echo.
    pause
)
