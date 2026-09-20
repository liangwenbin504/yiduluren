@echo off
chcp 65001 >nul
title SSE 流式清洗网关
echo ========================================
echo   SSE 流式清洗网关启动器
echo ========================================
echo.
echo 正在启动 SSE 清洗中间件...
echo 监听端口: 8081
echo 代理目标: Chat2API (8080)
echo.
node "%~dp0sse-cleaner-middleware.js"
pause