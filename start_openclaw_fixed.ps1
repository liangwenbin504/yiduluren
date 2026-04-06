# OpenClaw Gateway 启动脚本 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenClaw Gateway 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置配置文件路径
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptPath "openclaw_config.json"

Write-Host "[1/3] 检查配置文件..." -ForegroundColor Yellow
if (-not (Test-Path $configPath)) {
    Write-Host "错误: 找不到配置文件 $configPath" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "✓ 配置文件已找到" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] 设置环境变量..." -ForegroundColor Yellow
$env:OPENCLAW_GATEWAY_PASSWORD = "openclaw-local-token-123456"
Write-Host "✓ 环境变量已设置" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] 启动 OpenClaw Gateway..." -ForegroundColor Yellow
Write-Host ""
Write-Host "OpenClaw 将在 http://127.0.0.1:18789 启动" -ForegroundColor Cyan
Write-Host "API 端点: http://127.0.0.1:18789/v1/chat/completions" -ForegroundColor Cyan
Write-Host "API 密钥: openclaw-local-token-123456" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动 OpenClaw
openclaw gateway --config $configPath --verbose