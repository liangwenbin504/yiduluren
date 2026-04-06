@echo off
chcp 65001 >nul
echo 启动 API 服务器...
cd /d "%~dp0"
python http_api_server.py 2>&1
pause
