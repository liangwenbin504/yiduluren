@echo off
chcp 65001 >nul
echo ========================================
echo   OpenClaw Gateway 启动脚本
echo ========================================
echo.

set OPENCLAW_CONFIG=%~dp0openclaw_config.json

echo [1/3] 检查配置文件...
if not exist "%OPENCLAW_CONFIG%" (
    echo 错误: 找不到配置文件 %OPENCLAW_CONFIG%
    pause
    exit /b 1
)
echo ✓ 配置文件已找到
echo.

echo [2/3] 设置环境变量...
set OPENCLAW_GATEWAY_PASSWORD=openclaw-local-token-123456
echo ✓ 环境变量已设置
echo.

echo [3/3] 启动 OpenClaw Gateway...
echo.
echo OpenClaw 将在 http://127.0.0.1:18789 启动
echo API 端点: http://127.0.0.1:18789/v1/chat/completions
echo API 密钥: openclaw-local-token-123456
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

openclaw gateway --config "%OPENCLAW_CONFIG%" --verbose

pause
