# Docker Desktop 安装完整指南（2026 版）

## 📋 系统要求

### 最低要求

- **操作系统**: Windows 10 64-bit Pro/Enterprise/Education (Build 15063+) 或 Windows 11
- **CPU**: 支持虚拟化技术（VT-x/AMD-V）
- **内存**: 至少 4GB RAM
- **硬盘**: 至少 10GB 可用空间
- **BIOS**: 已启用虚拟化支持

### 检查系统要求

**方法 1: 使用批处理文件**
```cmd
cd "d:\新建文件夹\仪度六壬择日\yiduluren"
install-docker.bat
```

**方法 2: 手动检查**

1. **检查 Windows 版本**:
   - 按 `Win + R`
   - 输入 `winver`
   - 查看版本信息

2. **检查内存**:
   - 右键点击"此电脑" → "属性"
   - 查看"已安装的内存 (RAM)"

3. **检查磁盘空间**:
   - 打开"此电脑"
   - 查看 C 盘可用空间

4. **检查虚拟化**:
   - 按 `Ctrl + Shift + Esc` 打开任务管理器
   - 点击"性能" → "CPU"
   - 查看"虚拟化"是否显示"已启用"

---

## 📥 安装步骤

### 步骤 1: 下载 Docker Desktop

1. **访问官网**:
   - 打开浏览器
   - 访问：https://docs.docker.com/desktop/install/windows-install/

2. **下载安装程序**:
   - 点击 "Download for Windows" 按钮
   - 等待下载完成（文件大小约 500MB）

**下载内容**:
- 文件名：`DockerDesktopInstaller.exe`
- 大小：~500MB
- 下载时间：根据网络速度，约 2-10 分钟

---

### 步骤 2: 安装 Docker Desktop

1. **运行安装程序**:
   - 双击 `DockerDesktopInstaller.exe`
   - 如果出现 UAC 提示，点击"是"

2. **选择配置**:
   ```
   ☑ Use WSL 2 instead of Hyper-V (推荐)
   ```
   
   **说明**:
   - ✅ **WSL 2**: 更轻量，性能更好，推荐
   - ❌ **Hyper-V**: 较重量，适合企业环境

3. **开始安装**:
   - 点击 "OK" 或 "Install"
   - 等待安装进度条完成

4. **安装完成**:
   - 看到 "Installation successful!" 提示
   - 点击 "Close"

**安装时间**: 约 5-10 分钟

---

### 步骤 3: 首次启动

1. **启动 Docker Desktop**:
   - 从开始菜单找到 "Docker Desktop"
   - 或在桌面双击 Docker Desktop 图标

2. **接受许可协议**:
   - 阅读许可条款
   - 点击 "Accept"

3. **等待初始化**:
   - Docker Desktop 会自动启动引擎
   - 等待右下角鲸鱼图标变绿（约 1-2 分钟）
   - 状态显示 "Docker Desktop is running"

4. **验证安装**:
   ```powershell
   # 打开 PowerShell
   docker --version
   docker-compose --version
   ```
   
   **预期输出**:
   ```
   Docker version 25.x.x, build xxxxxxx
   Docker Compose version v2.x.x
   ```

---

### 步骤 4: 配置 Docker（可选）

1. **打开设置**:
   - 点击 Docker Desktop 右上角齿轮图标

2. **资源配置**（推荐）:
   - **CPUs**: 2-4 核（根据你的 CPU）
   - **Memory**: 2-4GB
   - **Swap**: 1-2GB
   - **Disk image size**: 60GB+

3. **应用并重启**:
   - 点击 "Apply & Restart"

---

## 🚀 部署应用

### 方法 1: 使用 PowerShell 脚本（推荐）

1. **打开 PowerShell（管理员）**:
   ```powershell
   cd "d:\新建文件夹\仪度六壬择日\yiduluren"
   ```

2. **运行部署脚本**:
   ```powershell
   .\docker-deploy.ps1
   ```

3. **选择选项**:
   ```
   请输入选项 (0-8): 1
   ```
   - 选择 `1`: 构建并启动容器

4. **等待构建完成**:
   - 首次构建需要下载基础镜像（约 5-10 分钟）
   - 后续构建只需几秒钟

5. **访问 API**:
   ```
   🌐 API 地址：http://localhost:5000
   📊 健康检查：http://localhost:5000/api/
   ```

---

### 方法 2: 手动命令

1. **构建 Docker 镜像**:
   ```powershell
   docker-compose build
   ```

2. **启动容器**:
   ```powershell
   docker-compose up -d
   ```

3. **查看状态**:
   ```powershell
   docker-compose ps
   ```

4. **查看日志**:
   ```powershell
   docker-compose logs -f
   ```

---

## ✅ 验证安装

### 测试 1: Docker 命令

```powershell
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 查看 Docker 信息
docker info
```

### 测试 2: 运行测试容器

```powershell
# 运行 Hello World
docker run hello-world

# 预期输出:
# Hello from Docker!
# Your installation appears to be working correctly.
```

### 测试 3: 测试 API

```powershell
# 测试 API 是否响应
python -c "import requests; r = requests.get('http://localhost:5000/api/'); print(r.status_code)"

# 测试斗首 API
python -c "import requests; r = requests.get('http://localhost:5000/api/doushou/shanjia_wuxing?mountain=壬'); print(r.json())"

# 测试大六壬 API
python -c "import requests; r = requests.get('http://localhost:5000/api/daliuren/tiandi_pan?yuejiang=亥&shichen=寅'); print(r.json())"
```

---

## 🔧 故障排查

### 问题 1: Docker Desktop 无法启动

**症状**: 鲸鱼图标一直是灰色或红色

**解决**:
1. 检查虚拟化是否启用
2. 重启电脑
3. 以管理员身份运行 Docker Desktop
4. 重新安装 Docker Desktop

---

### 问题 2: WSL 2 未安装

**错误**: "WSL 2 installation not found"

**解决**:
```powershell
# 以管理员身份运行 PowerShell
wsl --install

# 重启电脑

# 安装 Ubuntu
wsl --install -d Ubuntu
```

---

### 问题 3: 端口被占用

**错误**: "Bind for 0.0.0.0:5000 failed: port is already allocated"

**解决**:
```powershell
# 方法 1: 查找并关闭占用端口的进程
netstat -ano | findstr :5000
taskkill /F /PID <进程 ID>

# 方法 2: 修改端口映射
# 编辑 docker-compose.yml，修改：
ports:
  - "8080:5000"  # 使用 8080 端口
```

---

### 问题 4: 容器启动失败

**查看日志**:
```powershell
docker-compose logs yiduluren-api
```

**常见错误**:
- `requirements.txt` 格式错误
- 代码有语法错误
- 缺少必要文件

**解决**:
```powershell
# 重新构建
docker-compose build --no-cache

# 重新启动
docker-compose up -d --force-recreate
```

---

## 📊 常用命令速查

### 容器管理
```powershell
# 启动容器
docker-compose up -d

# 停止容器
docker-compose down

# 重启容器
docker-compose restart

# 查看状态
docker-compose ps
```

### 日志管理
```powershell
# 实时日志
docker-compose logs -f

# 最近 100 行
docker-compose logs --tail=100

# 导出日志
docker-compose logs > logs.txt
```

### 镜像管理
```powershell
# 构建镜像
docker-compose build

# 查看镜像
docker images

# 删除镜像
docker rmi <镜像 ID>
```

### 进入容器
```powershell
# 进入 Shell
docker-compose exec yiduluren-api /bin/bash

# 执行命令
docker-compose exec yiduluren-api python --version
```

---

## 📈 性能优化

### 1. 调整资源限制

编辑 `docker-compose.yml`:
```yaml
services:
  yiduluren-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### 2. 使用 Docker Buildx

```powershell
# 创建 builder
docker buildx create --use

# 构建镜像
docker-compose build
```

### 3. 清理无用资源

```powershell
# 清理停止的容器
docker container prune

# 清理未使用的镜像
docker image prune

# 清理所有未使用的资源
docker system prune -a
```

---

## 🎯 完整流程时间估算

| 步骤 | 预计时间 |
|------|---------|
| 下载 Docker Desktop | 2-10 分钟 |
| 安装 Docker Desktop | 5-10 分钟 |
| 首次启动 Docker | 1-2 分钟 |
| 构建 Docker 镜像（首次） | 5-10 分钟 |
| 启动容器 | 30 秒 |
| **总计** | **15-35 分钟** |

---

## 📚 相关资源

- **Docker 官方文档**: https://docs.docker.com/
- **Docker Desktop 下载**: https://docs.docker.com/desktop/
- **WSL 2 安装指南**: https://docs.microsoft.com/windows/wsl/install
- **Docker Compose 文档**: https://docs.docker.com/compose/

---

## 🆘 获取帮助

### Docker Desktop 内置帮助

1. 打开 Docker Desktop
2. 点击右上角 "?" 图标
3. 选择 "Documentation" 或 "Troubleshooting"

### 社区支持

- **Docker 论坛**: https://forums.docker.com/
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/docker
- **GitHub Issues**: https://github.com/docker/for-win/issues

---

**最后更新**: 2026-03-30  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪

祝你安装顺利！如有问题，请查看故障排查章节或联系技术支持。
