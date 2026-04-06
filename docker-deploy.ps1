# 仪度六壬择日系统 - Docker 部署脚本 (PowerShell)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "仪度六壬择日系统 - Docker 部署" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否安装
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 版本：$dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：Docker 未安装" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://docs.docker.com/desktop/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 检查 Docker Compose 是否安装
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose 版本：$composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：Docker Compose 未安装" -ForegroundColor Red
    Write-Host "Docker Desktop 已包含 Docker Compose" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 创建必要目录
Write-Host "📁 创建必要目录..." -ForegroundColor Cyan
if (!(Test-Path "uploads\gifs")) {
    New-Item -ItemType Directory -Force -Path "uploads\gifs" | Out-Null
    Write-Host "  ✅ 创建 uploads/gifs 目录" -ForegroundColor Green
} else {
    Write-Host "  ✅ uploads/gifs 目录已存在" -ForegroundColor Green
}

if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Force -Path "logs" | Out-Null
    Write-Host "  ✅ 创建 logs 目录" -ForegroundColor Green
} else {
    Write-Host "  ✅ logs 目录已存在" -ForegroundColor Green
}

# 创建 requirements.txt（如果不存在）
if (!(Test-Path "requirements.txt")) {
    Write-Host "📝 创建 requirements.txt..." -ForegroundColor Cyan
    @'
flask==2.3.3
flask-cors==4.0.0
requests==2.31.0
waitress==3.0.2
'@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
    Write-Host "  ✅ requirements.txt 已创建" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "选择操作：" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "1. 构建并启动容器"
Write-Host "2. 启动已存在的容器"
Write-Host "3. 停止容器"
Write-Host "4. 重启容器"
Write-Host "5. 查看容器日志"
Write-Host "6. 进入容器 Shell"
Write-Host "7. 重新构建镜像"
Write-Host "8. 清理（删除容器和镜像）"
Write-Host "0. 退出"
Write-Host ""

$choice = Read-Host "请输入选项 (0-8)"

Write-Host ""

switch ($choice) {
    "1" {
        Write-Host "🔨 构建 Docker 镜像..." -ForegroundColor Cyan
        docker-compose build
        
        Write-Host ""
        Write-Host "🚀 启动容器..." -ForegroundColor Cyan
        docker-compose up -d
        
        Write-Host ""
        Write-Host "✅ 容器已启动！" -ForegroundColor Green
        Write-Host "📊 查看状态：docker-compose ps" -ForegroundColor Yellow
        Write-Host "📝 查看日志：docker-compose logs -f" -ForegroundColor Yellow
        Write-Host "🌐 访问地址：http://localhost:5000" -ForegroundColor Yellow
    }
    
    "2" {
        Write-Host "🚀 启动容器..." -ForegroundColor Cyan
        docker-compose up -d
        Write-Host "✅ 容器已启动！" -ForegroundColor Green
    }
    
    "3" {
        Write-Host "⏹️  停止容器..." -ForegroundColor Cyan
        docker-compose down
        Write-Host "✅ 容器已停止！" -ForegroundColor Green
    }
    
    "4" {
        Write-Host "🔄 重启容器..." -ForegroundColor Cyan
        docker-compose restart
        Write-Host "✅ 容器已重启！" -ForegroundColor Green
    }
    
    "5" {
        Write-Host "📝 查看日志（Ctrl+C 退出）..." -ForegroundColor Cyan
        docker-compose logs -f
    }
    
    "6" {
        Write-Host "🔧 进入容器 Shell..." -ForegroundColor Cyan
        docker-compose exec yiduluren-api /bin/bash
    }
    
    "7" {
        Write-Host "🔨 重新构建镜像（无缓存）..." -ForegroundColor Cyan
        docker-compose build --no-cache
        
        Write-Host ""
        Write-Host "🔄 重启容器..." -ForegroundColor Cyan
        docker-compose up -d --force-recreate
        Write-Host "✅ 容器已重启！" -ForegroundColor Green
    }
    
    "8" {
        Write-Host "🧹 清理容器和镜像..." -ForegroundColor Cyan
        $confirm = Read-Host "确认删除所有容器和镜像？(y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            docker-compose down -v --rmi all
            Write-Host "✅ 清理完成！" -ForegroundColor Green
        } else {
            Write-Host "❌ 取消清理" -ForegroundColor Yellow
        }
    }
    
    "0" {
        Write-Host "👋 退出" -ForegroundColor Cyan
        exit 0
    }
    
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🌐 API 地址：http://localhost:5000" -ForegroundColor Yellow
Write-Host "📊 健康检查：http://localhost:5000/api/" -ForegroundColor Yellow
Write-Host "📝 查看日志：docker-compose logs -f" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
