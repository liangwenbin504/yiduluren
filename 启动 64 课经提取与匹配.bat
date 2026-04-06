@echo off
chcp 65001 >nul
title 大六壬 64 课经完整系统 - 提取与匹配
cd /d %~dp0

echo ================================================================
echo 大六壬 64 课经完整系统
echo ================================================================
echo.

echo [1/3] 正在从 PDF 提取课经...
python src\engine\complete_ke_jing_system.py

echo.
echo ================================================================
echo 处理完成！
echo ================================================================
echo.
echo 生成的文件：
echo   - data\64_ke_jing.json (课经数据)
echo   - data\720_ke_li.json (课例数据库)
echo   - output\课经测试报告.txt (测试报告)
echo.

pause
