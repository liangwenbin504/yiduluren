@echo off
chcp 65001 >nul
title 一键解锁文件锁
echo 正在运行一键解锁脚本...
python "E:\仪度六壬择日\yiduluren\_memory\_unlock_all.py"
if errorlevel 1 (
  echo.
  echo [提示] 如果提示找不到 python，请改用第二种方式（见说明）。
  pause
)
