# 仪度六壬择日 - 阿里云部署脚本
# 使用方法：在 PowerShell 中运行 .\deploy_to_aliyun.ps1

param(
    [string]$ServerIP = "47.97.244.134",
    [string]$ServerUser = "root",
    [string]$RemotePath = "/opt/liuren",
    [string]$LocalZip = "liuren-deploy-update.zip"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 仪度六壬择日 - 阿里云部署" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务器: $ServerIP" -ForegroundColor Yellow
Write-Host "用户: $ServerUser" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host ""

# 切换到脚本所在目录
Set-Location (Split-Path $MyInvocation.MyCommand.Path)

# 检查部署包是否存在
if (!(Test-Path $LocalZip)) {
    Write-Host "❌ 部署包不存在: $LocalZip" -ForegroundColor Red
    Write-Host "请先在项目根目录运行: Compress-Archive ..." -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 部署包大小: $([math]::Round((Get-Item $LocalZip).Length / 1MB, 2)) MB" -ForegroundColor Green
Write-Host ""

Write-Host "📤 步骤1：上传部署包到服务器..." -ForegroundColor Cyan
Write-Host "   请在弹出的密码提示中输入服务器密码" -ForegroundColor Yellow
Write-Host ""

# 上传文件
scp -o StrictHostKeyChecking=no ".\$LocalZip" "${ServerUser}@${ServerIP}:/tmp/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 上传失败，请检查网络或密码" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 上传成功" -ForegroundColor Green
Write-Host ""

Write-Host "🔧 步骤2：在服务器上解压并部署..." -ForegroundColor Cyan
Write-Host ""

# SSH 执行远程命令
ssh -o StrictHostKeyChecking=no "${ServerUser}@${ServerIP}" @"
set -e

# 如果存在旧版本，备份
if [ -d "$RemotePath" ]; then
    cp -r "$RemotePath" "$RemotePath.bak_\$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
fi

# 创建目录
mkdir -p $RemotePath

# 解压部署包到临时目录
cd /tmp
rm -rf liuren_deploy_temp
mkdir -p liuren_deploy_temp

# 解压（优先使用 unzip）
if command -v unzip &>/dev/null; then
    unzip -o liuren-deploy-update.zip -d liuren_deploy_temp/
elif command -v python3 &>/dev/null; then
    python3 -c "import zipfile; zipfile.ZipFile('liuren-deploy-update.zip').extractall('liuren_deploy_temp')"
else
    echo "❌ 无法解压，请安装 unzip 或 python3"
    exit 1
fi

# 复制到目标目录
cp -rf liuren_deploy_temp/* $RemotePath/

# 设置权限
chmod +x $RemotePath/install_on_server.sh 2>/dev/null || true

# 运行安装脚本
cd $RemotePath
bash install_on_server.sh

# 清理
rm -rf /tmp/liuren_deploy_temp /tmp/liuren-deploy-update.zip

echo ""
echo "✅ 部署完成！"
echo "   服务状态: systemctl status liuren"
echo "   查看日志: journalctl -u liuren -f"
echo "   访问地址: https://liuren.souhuertong.net.cn"
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  远程部署可能未完全成功，请手动检查服务器" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 部署流程完成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 访问地址: https://liuren.souhuertong.net.cn" -ForegroundColor Yellow
Write-Host "📊 本地测试: http://localhost:5555" -ForegroundColor Yellow
