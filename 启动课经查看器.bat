@echo off
chcp 65001 >nul
title 大六壬 64 课经查看器
cd /d %~dp0
python src\ui\ke_jing_viewer_gui.py
pause
