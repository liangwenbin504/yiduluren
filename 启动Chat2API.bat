@echo off
chcp 65001 >nul
title Chat2API 统一 AI 网关
echo ============================================
echo   Chat2API 统一 AI 网关 (Web模式)
echo   聚合豆包 / GLM / DeepSeek / Kimi
echo ============================================
echo.
echo [1/2] 正在启动 Chat2API 服务...
echo.

cd /d "D:\迅雷下载\Chat2API-1.4.0"
set WEB_MODE=true
set DATA_DIR=%USERPROFILE%\.chat2api
set API_PORT=8080
set WEB_PORT=3000
set API_HOST=0.0.0.0
set WEB_HOST=0.0.0.0
set NODE_ENV=production

start "Chat2API" cmd /k "cd /d D:\迅雷下载\Chat2API-1.4.0 && set WEB_MODE=true && set DATA_DIR=%USERPROFILE%\.chat2api && set API_PORT=8080 && set WEB_PORT=3000 && set API_HOST=0.0.0.0 && set WEB_HOST=0.0.0.0 && set NODE_ENV=production && tsx src/main/web-server.ts"

echo [2/2] 服务启动中，请稍候 5 秒...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   ✅  启动成功！
echo ============================================
echo.
echo   管理面板: http://127.0.0.1:3000
echo   代理接口: http://127.0.0.1:8080/v1
echo   API Key : sk-local-free (任意填写)
echo.
echo   关闭此窗口不会停止服务，
echo   如需停止请关闭弹出的 cmd 窗口。
echo.
echo ============================================
echo.
start http://127.0.0.1:3000
pause
