@echo off
chcp 65001 >nul
echo ============================================
echo   Chat2API 一键启动脚本
echo   统一 AI 网关 - 聚合多平台模型
echo ============================================
echo.
echo [1/2] 启动 Chat2API 统一网关...
start "" "D:\AI-Tools\Chat2API\Chat2API-1.4.0-x64-portable.exe"
echo.
echo [2/2] 网关已启动！
echo.
echo   管理面板: http://127.0.0.1:8080
echo   代理接口: http://127.0.0.1:8080/v1
echo.
echo   如需抓取 PC 客户端流量，另开窗口执行：
echo     mitmweb --listen 127.0.0.1:8081
echo.
echo ============================================
pause
