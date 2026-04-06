#!/bin/bash

# 仪度六壬择日系统 - Docker 部署脚本

set -e

echo "============================================================"
echo "仪度六壬择日系统 - Docker 部署"
echo "============================================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 版本：$(docker --version)"
echo "✅ Docker Compose 版本：$(docker-compose --version)"
echo ""

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p uploads/gifs logs
chmod 755 uploads/gifs logs

# 创建 requirements.txt（如果不存在）
if [ ! -f requirements.txt ]; then
    echo "📝 创建 requirements.txt..."
    cat > requirements.txt << 'EOF'
flask==2.3.3
flask-cors==4.0.0
requests==2.31.0
waitress==3.0.2
EOF
fi

echo ""
echo "============================================================"
echo "选择操作："
echo "============================================================"
echo "1. 构建并启动容器"
echo "2. 启动已存在的容器"
echo "3. 停止容器"
echo "4. 重启容器"
echo "5. 查看容器日志"
echo "6. 进入容器 Shell"
echo "7. 重新构建镜像"
echo "8. 清理（删除容器和镜像）"
echo "0. 退出"
echo ""

read -p "请输入选项 (0-8): " choice

case $choice in
    1)
        echo ""
        echo "🔨 构建 Docker 镜像..."
        docker-compose build
        
        echo ""
        echo "🚀 启动容器..."
        docker-compose up -d
        
        echo ""
        echo "✅ 容器已启动！"
        echo "📊 查看状态：docker-compose ps"
        echo "📝 查看日志：docker-compose logs -f"
        echo "🌐 访问地址：http://localhost:5000"
        ;;
        
    2)
        echo ""
        echo "🚀 启动容器..."
        docker-compose up -d
        echo "✅ 容器已启动！"
        ;;
        
    3)
        echo ""
        echo "⏹️  停止容器..."
        docker-compose down
        echo "✅ 容器已停止！"
        ;;
        
    4)
        echo ""
        echo "🔄 重启容器..."
        docker-compose restart
        echo "✅ 容器已重启！"
        ;;
        
    5)
        echo ""
        echo "📝 查看日志（Ctrl+C 退出）..."
        docker-compose logs -f
        ;;
        
    6)
        echo ""
        echo "🔧 进入容器 Shell..."
        docker-compose exec yiduluren-api /bin/bash
        ;;
        
    7)
        echo ""
        echo "🔨 重新构建镜像（无缓存）..."
        docker-compose build --no-cache
        
        echo ""
        echo "🔄 重启容器..."
        docker-compose up -d --force-recreate
        echo "✅ 容器已重启！"
        ;;
        
    8)
        echo ""
        echo "🧹 清理容器和镜像..."
        read -p "确认删除所有容器和镜像？(y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker-compose down -v --rmi all
            echo "✅ 清理完成！"
        else
            echo "❌ 取消清理"
        fi
        ;;
        
    0)
        echo "👋 退出"
        exit 0
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "部署完成！"
echo "============================================================"
echo "🌐 API 地址：http://localhost:5000"
echo "📊 健康检查：http://localhost:5000/api/"
echo "📝 查看日志：docker-compose logs -f"
echo "============================================================"
