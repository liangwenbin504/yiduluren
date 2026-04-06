# Docker 安装和部署完整指南

## ⚠️ 当前状态

**Docker 未安装** - 需要先安装 Docker Desktop

---

## 📥 方案 1: 安装 Docker Desktop（推荐）

### Windows 用户

#### 步骤 1: 检查系统要求

- Windows 10 64-bit: Pro, Enterprise, or Education (Build 15063+)
- Windows 11: Home, Pro, Enterprise, or Education
- 虚拟化支持：BIOS 中已启用 VT-x/AMD-V
- RAM: 至少 4GB
- 硬盘空间：至少 10GB

#### 步骤 2: 下载 Docker Desktop

1. **访问官网**: https://docs.docker.com/desktop/install/windows-install/
2. **下载安装程序**: `Docker Desktop Installer.exe`
3. **运行安装程序**: 双击安装
4. **等待安装完成**: 约 5-10 分钟

#### 步骤 3: 启动 Docker Desktop

1. 启动 Docker Desktop
2. 等待右下角鲸鱼图标变绿（约 1-2 分钟）
3. 打开 PowerShell 测试：
```powershell
docker --version
docker-compose --version
```

#### 步骤 4: 部署应用

```powershell
cd "d:\新建文件夹\仪度六壬择日\yiduluren"
.\docker-deploy.ps1
# 选择选项 1: 构建并启动容器
```

---

## 🚀 方案 2: 使用 WSL2 + Ubuntu（备选）

如果你不想安装 Docker Desktop，可以使用 WSL2。

### 步骤 1: 安装 WSL2

```powershell
# 以管理员身份运行 PowerShell
wsl --install

# 重启电脑
```

### 步骤 2: 安装 Ubuntu

```powershell
# 在 Microsoft Store 中搜索 "Ubuntu"
# 安装 Ubuntu 22.04 LTS
```

### 步骤 3: 在 Ubuntu 中安装 Docker

```bash
# 更新包
sudo apt update

# 安装 Docker
sudo apt install -y docker.io docker-compose

# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 重启 WSL
exit
```

### 步骤 4: 部署应用

```bash
cd /mnt/d/新建文件夹/仪度六壬择日/yiduluren
docker-compose build
docker-compose up -d
```

---

## 🔧 方案 3: 使用端口 8080（快速测试）

如果 Docker 安装太慢，可以先测试更换端口方案。

### 步骤 1: 修改启动脚本

编辑 `start_with_waitress.py`:

```python
# 修改端口从 5000 改为 8080
serve(
    app,
    host='0.0.0.0',
    port=8080,  # 改为 8080
    threads=4,
)
```

### 步骤 2: 启动服务器

```powershell
python start_with_waitress.py
```

### 步骤 3: 测试 API

```powershell
python -c "import requests; r = requests.get('http://localhost:8080/api/doushou/shanjia_wuxing?mountain=壬'); print(r.status_code, r.text[:200])"
```

---

## 📋 Docker 部署文件说明

### 已创建的文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `Dockerfile` | Docker 镜像定义 | 定义容器环境 |
| `docker-compose.yml` | Docker Compose 配置 | 编排容器 |
| `.dockerignore` | Docker 忽略文件 | 排除不必要文件 |
| `docker-deploy.ps1` | PowerShell 部署脚本 | 一键部署 |
| `docker-deploy.sh` | Bash 部署脚本 | Linux/Mac 部署 |
| `requirements.txt` | Python 依赖 | 安装 Python 包 |
| `DOCKER_DEPLOYMENT.md` | 详细部署指南 | 完整文档 |

### 文件位置

所有文件都已保存在：
```
d:\新建文件夹\仪度六壬择日\yiduluren\
```

---

## 🎯 快速测试（无需 Docker）

### 方法 1: 使用不同端口

```powershell
# 1. 编辑 start_with_waitress.py，修改 port=8080
# 2. 启动
python start_with_waitress.py

# 3. 测试
python simple_api_test.py
```

### 方法 2: 使用 127.0.0.1

```powershell
# 编辑 start_debug.py，修改 host='127.0.0.1'
python start_debug.py

# 测试
curl http://127.0.0.1:5000/api/
```

### 方法 3: 重置网络栈（推荐尝试）

```powershell
# 以管理员身份运行 PowerShell

# 重置 Winsock
netsh winsock reset

# 重置 TCP/IP
netsh int ip reset

# 刷新 DNS
ipconfig /flushdns

# 重启电脑后测试
python start_debug.py
```

---

## 📊 Docker 优势

使用 Docker 部署的优势：

| 特性 | 本地部署 | Docker 部署 |
|------|---------|------------|
| 环境一致性 | ❌ 依赖本地环境 | ✅ 完全隔离 |
| 端口冲突 | ❌ 容易冲突 | ✅ 可映射任意端口 |
| 依赖管理 | ❌ 容易冲突 | ✅ 独立环境 |
| 部署速度 | ✅ 快 | ✅ 快（首次慢） |
| 日志管理 | ❌ 分散 | ✅ 集中管理 |
| 资源隔离 | ❌ 无 | ✅ 完全隔离 |
| 生产就绪 | ❌ 需要配置 | ✅ 开箱即用 |

---

## 🔍 故障排查

### 问题：Docker Desktop 安装失败

**解决**:
1. 检查 BIOS 虚拟化是否启用
2. 关闭 Hyper-V（如果启用）
3. 以管理员身份运行安装程序
4. 重启电脑后重试

### 问题：容器启动失败

**解决**:
```bash
# 查看日志
docker-compose logs

# 检查容器状态
docker-compose ps

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 问题：无法访问 API

**解决**:
```bash
# 检查端口
netstat -ano | findstr :5000

# 检查容器日志
docker-compose logs yiduluren-api

# 进入容器调试
docker-compose exec yiduluren-api /bin/bash
```

---

## 📝 下一步行动

### 推荐顺序

1. **立即尝试**（无需 Docker）:
   ```powershell
   # 重置网络栈
   netsh winsock reset
   # 重启电脑
   
   # 使用端口 8080 测试
   python start_with_waitress.py
   ```

2. **短期方案**（今天）:
   - 安装 Docker Desktop
   - 运行 `.\docker-deploy.ps1`

3. **长期方案**（本周）:
   - 配置 Nginx 反向代理
   - 设置自动部署
   - 配置监控系统

---

## 📚 资源链接

- **Docker Desktop 下载**: https://docs.docker.com/desktop/
- **Docker 教程**: https://docs.docker.com/get-started/
- **Docker Compose 文档**: https://docs.docker.com/compose/
- **WSL2 安装指南**: https://docs.microsoft.com/windows/wsl/install

---

**创建时间**: 2026-03-30  
**状态**: ✅ 就绪  
**推荐**: 方案 1（Docker Desktop）或 方案 3（端口 8080 测试）
