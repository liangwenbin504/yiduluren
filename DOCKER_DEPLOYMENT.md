# 仪度六壬择日系统 - Docker 部署指南

## 📋 前提条件

### 1. 安装 Docker Desktop

**Windows 用户**:
1. 访问：https://docs.docker.com/desktop/install/windows-install/
2. 下载 Docker Desktop for Windows
3. 运行安装程序
4. 启动 Docker Desktop

**验证安装**:
```bash
docker --version
docker-compose --version
```

---

## 🚀 快速开始

### 方法 1: 使用 PowerShell 脚本（推荐）

```powershell
# 打开 PowerShell（管理员）
cd "d:\新建文件夹\仪度六壬择日\yiduluren"

# 运行部署脚本
.\docker-deploy.ps1

# 选择选项 1: 构建并启动容器
```

### 方法 2: 手动命令

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动容器
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

---

## 🧪 测试 API

容器启动后，测试 API 是否正常：

```bash
# 测试 1: 简单 API
curl http://localhost:5000/api/doushou/shanjia_wuxing?mountain=壬

# 测试 2: 大六壬 API
curl http://localhost:5000/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅

# 测试 3: 使用 Python
python -c "import requests; r = requests.get('http://localhost:5000/api/'); print(r.json())"
```

---

## 📊 常用命令

### 查看容器状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 实时日志
docker-compose logs -f

# 最近 100 行
docker-compose logs --tail=100

# 只看应用日志
docker-compose logs yiduluren-api
```

### 停止容器
```bash
docker-compose down
```

### 重启容器
```bash
docker-compose restart
```

### 进入容器
```bash
# 进入 Shell
docker-compose exec yiduluren-api /bin/bash

# 直接进入 Python
docker-compose exec yiduluren-api python
```

### 重新构建
```bash
# 使用缓存
docker-compose build

# 不使用缓存（完全重新构建）
docker-compose build --no-cache
```

---

## 🔧 故障排查

### 问题 1: 端口被占用

**错误**: `Bind for 0.0.0.0:5000 failed: port is already allocated`

**解决**:
```bash
# 方法 1: 停止占用端口的进程
netstat -ano | findstr :5000
taskkill /F /PID <进程 ID>

# 方法 2: 修改 docker-compose.yml 使用其他端口
ports:
  - "8080:5000"  # 使用 8080 端口
```

### 问题 2: Docker Desktop 未启动

**错误**: `Error response from daemon: ...`

**解决**:
1. 启动 Docker Desktop
2. 等待右下角鲸鱼图标变绿
3. 重试命令

### 问题 3: 构建失败

**错误**: `failed to solve: ...`

**解决**:
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache
```

### 问题 4: 容器启动后立即退出

**查看日志**:
```bash
docker-compose logs yiduluren-api
```

**常见原因**:
- requirements.txt 格式错误
- 代码有语法错误
- 缺少必要文件

---

## 📁 数据持久化

### 挂载的卷

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `./uploads` | `/app/uploads` | 上传的 GIF 文件 |
| `./logs` | `/app/logs` | 日志文件 |

### 备份数据
```bash
# 备份上传文件
tar -czf uploads-backup.tar.gz uploads/

# 备份日志
tar -czf logs-backup.tar.gz logs/
```

---

## 🔒 安全建议

### 生产环境配置

1. **修改默认端口**:
```yaml
# docker-compose.yml
ports:
  - "127.0.0.1:5000:5000"  # 只允许本地访问
```

2. **添加环境变量**:
```yaml
# docker-compose.yml
environment:
  - FLASK_ENV=production
  - SECRET_KEY=<your-secret-key>
```

3. **使用 Nginx 反向代理**:
```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

---

## 📈 性能优化

### 1. 增加工作进程
```yaml
# docker-compose.yml
environment:
  - WAITRESS_WORKERS=4  # 增加 Waitress 工作进程
```

### 2. 使用 Docker Buildx（加速构建）
```bash
docker buildx create --use
docker-compose build
```

### 3. 资源限制
```yaml
# docker-compose.yml
services:
  yiduluren-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 🎯 完整部署流程

### 开发环境
```bash
# 1. 构建并启动
docker-compose up -d

# 2. 查看日志
docker-compose logs -f

# 3. 测试 API
curl http://localhost:5000/api/

# 4. 停止
docker-compose down
```

### 生产环境
```bash
# 1. 构建优化镜像
docker-compose build --no-cache

# 2. 启动容器
docker-compose up -d

# 3. 健康检查
docker-compose ps

# 4. 查看资源使用
docker stats yiduluren-api

# 5. 设置自动重启
# docker-compose.yml 中已配置：restart: unless-stopped
```

---

## 📚 参考资料

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Waitress 文档](https://docs.pylonsproject.org/projects/waitress/en/stable/)
- [Flask 部署指南](https://flask.palletsprojects.com/en/2.0.x/deploying/)

---

## 🆘 获取帮助

### 查看容器信息
```bash
docker-compose exec yiduluren-api python --version
docker-compose exec yiduluren-api pip list
```

### 导出日志
```bash
docker-compose logs > deployment.log 2>&1
```

### 重置一切
```bash
# 删除容器、网络、卷
docker-compose down -v

# 删除镜像
docker-compose down --rmi all

# 清理系统
docker system prune -a
```

---

**最后更新**: 2026-03-30  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪
