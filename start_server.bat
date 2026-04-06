@echo off
chcp 65001 >nul
echo ============================================================
echo 仪度六壬择日系统 - 启动服务
echo ============================================================
echo.

echo [1/2] 启动 Flask API 服务...
start "Flask API Server" cmd /k "cd /d %~dp0 && python api_server.py"

echo 等待 API 服务启动...
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
echo.
echo ============================================================
echo 服务已启动：
echo   - API 服务: http://localhost:5000
echo   - 前端页面: 请在浏览器中打开 主界面.html
echo ============================================================
echo.
echo 按任意键退出此窗口（API服务将继续运行）...
pause >nul
