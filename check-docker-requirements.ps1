#!/usr/bin/env powershell
# Docker Desktop 安装检查脚本

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Docker Desktop 安装前系统检查" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Windows 版本
Write-Host "📋 检查系统要求..." -ForegroundColor Yellow
$os = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "  Windows 版本：$($os.Caption) $($os.Version)" -ForegroundColor Gray

# 检查系统架构
$systemInfo = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "  系统架构：$($os.OSArchitecture)" -ForegroundColor Gray

# 检查内存
$mem = Get-WmiObject -Class Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
$totalMemGB = [math]::Round($sum.Sum / 1GB, 2)
Write-Host "  总内存：$totalMemGB GB" -ForegroundColor Gray

if ($totalMemGB -ge 4) {
    Write-Host "  ✅ 内存满足要求（>= 4GB）" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  内存不足 4GB，可能影响 Docker 性能" -ForegroundColor Yellow
}

# 检查磁盘空间
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
Write-Host "  C 盘可用空间：$freeSpaceGB GB" -ForegroundColor Gray

if ($freeSpaceGB -ge 10) {
    Write-Host "  ✅ 磁盘空间满足要求（>= 10GB）" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  磁盘空间不足 10GB，建议清理" -ForegroundColor Yellow
}

# 检查虚拟化是否启用
Write-Host ""
Write-Host "🔍 检查虚拟化支持..." -ForegroundColor Yellow
try {
    $bios = Get-WmiObject -Class Win32_BIOS
    $virtualizationEnabled = $false
    
    # 检查 Hyper-V 状态
    $hyperV = Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V -Online -ErrorAction SilentlyContinue
    if ($hyperV) {
        Write-Host "  Hyper-V 状态：$($hyperV.State)" -ForegroundColor Gray
        if ($hyperV.State -eq 'Enabled') {
            Write-Host "  ✅ Hyper-V 已启用" -ForegroundColor Green
            $virtualizationEnabled = $true
        }
    }
    
    # 检查 WSL2
    $wsl = Get-WindowsOptionalFeature -FeatureName Microsoft-Windows-Subsystem-Linux -Online -ErrorAction SilentlyContinue
    if ($wsl) {
        Write-Host "  WSL 状态：$($wsl.State)" -ForegroundColor Gray
        if ($wsl.State -eq 'Enabled') {
            Write-Host "  ✅ WSL 已启用" -ForegroundColor Green
        }
    }
    
    if (-not $virtualizationEnabled) {
        Write-Host "  ⚠️  Hyper-V 未启用，Docker 可能需要它" -ForegroundColor Yellow
        Write-Host "  提示：可以在'启用或关闭 Windows 功能'中启用 Hyper-V" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️  无法检查虚拟化状态" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "检查结论" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($totalMemGB -ge 4 -and $freeSpaceGB -ge 10) {
    Write-Host "✅ 系统满足 Docker Desktop 安装要求" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作：" -ForegroundColor Yellow
    Write-Host "1. 访问：https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor White
    Write-Host "2. 下载 Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. 运行安装程序" -ForegroundColor White
    Write-Host "4. 安装完成后重启电脑" -ForegroundColor White
    Write-Host "5. 启动 Docker Desktop" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  系统可能不满足要求，请检查上述警告" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
