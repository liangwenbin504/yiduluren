@echo off
REM 仪度六壬择日 — 一键启动脚本
echo ============================================
echo   仪度六壬择日系统 — 一键启动
echo ============================================
echo.

set PY=python -X utf8
set ROOT=%~dp0
cd /d %ROOT%

REM 1. API服务器 (端口8000)
echo [1/3] 启动 API服务器 (port 8000)...
start "仪度六壬API" %PY% api_server.py 8000

REM 2. 股票仪表盘 (端口5556)
echo [2/3] 启动 股票仪表盘 (port 5556)...
start "仪度六壬仪表盘" %PY% stock_dashboard.py 5556

REM 3. 调度器
echo [3/3] 启动 自动调度器...
start "仪度六壬调度器" %PY% auto_scheduler.py

echo.
echo ============================================
echo   启动完成!
echo   API:      http://localhost:8000
echo   仪表盘:   http://localhost:5556
echo   调度器:   后台运行中
echo ============================================
pause
