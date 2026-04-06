# Docker Desktop 安装前检查

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Docker Desktop 安装前系统检查" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Windows 版本
Write-Host "Windows 版本信息:" -ForegroundColor Yellow
systeminfo | Select-String "OS Name|OS Version"

# 检查内存
Write-Host "`n内存信息:" -ForegroundColor Yellow
$mem = Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
$totalMemGB = [math]::Round($mem.Sum / 1GB, 2)
Write-Host "  总内存：$totalMemGB GB" -ForegroundColor Gray

if ($totalMemGB -ge 4) {
    Write-Host "  ✅ 内存满足要求（>= 4GB）" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  内存不足 4GB" -ForegroundColor Yellow
}

# 检查磁盘空间
Write-Host "`n磁盘空间:" -ForegroundColor Yellow
$disk = Get-Volume -DriveLetter C | Select-Object SizeRemaining
$freeSpaceGB = [math]::Round($disk.SizeRemaining / 1GB, 2)
Write-Host "  C 盘可用空间：$freeSpaceGB GB" -ForegroundColor Gray

if ($freeSpaceGB -ge 10) {
    Write-Host "  ✅ 磁盘空间满足要求（>= 10GB）" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  磁盘空间不足 10GB" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "安装步骤" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 访问官网下载页面:" -ForegroundColor Yellow
Write-Host "   https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor White
Write-Host ""
Write-Host "2. 点击 'Download for Windows' 按钮" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. 运行下载的安装程序" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. 安装完成后重启电脑" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. 启动 Docker Desktop，等待鲸鱼图标变绿" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
