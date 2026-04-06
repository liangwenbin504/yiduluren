@echo off
chcp 65001 >nul
title 本地安全对话API服务
color 0A

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║        🚀  本地安全对话API服务  🚀                        ║
echo ║                                                            ║
echo ║        🔒 100% 本地处理 · 数据不上传 🔒                   ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo [启动中...]
echo.

cd /d "%~dp0"
node local_openai_api.js

if errorlevel 1 (
    echo.
    echo [错误] 服务启动失败！
    echo.
    pause
)
