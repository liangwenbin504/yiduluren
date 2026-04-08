# 仪度六壬择日系统 - 云平台部署指南

本文档介绍如何将仪度六壬择日系统部署到各大云平台上！

---

## 🎯 推荐方案（免费）

### 方案一：Render（最推荐，完全免费）

**Render** 是最适合小白的免费云平台！

#### 部署步骤：

1. **注册 Render 账号**
   - 访问：https://render.com
   - 使用 GitHub 账号登录（一键关联）

2. **创建新服务**
   - 点击右上角 "New +" → "Web Service"
   - 选择您的 GitHub 仓库：`liangwenbin504/yiduluren`
   - 点击 "Connect"

3. **配置服务**
   - **Name**: `yiduluren`（或您喜欢的名字）
   - **Region**: 选择离您近的（如 Singapore）
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_with_waitress.py`
   - **Plan**: 选择 **Free**（免费）

4. **点击 "Create Web Service"**
   - 等待 2-5 分钟部署完成
   - 完成后会给您一个网址，如：`https://yiduluren.onrender.com`

5. **访问您的网站**
   - 打开浏览器访问分配的网址！

---

### 方案二：Railway（免费额度）

**Railway** 也是不错的选择，每月有 $5 免费额度！

#### 部署步骤：

1. **访问 Railway**
   - 网址：https://railway.app
   - 使用 GitHub 登录

2. **新建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择您的仓库

3. **配置**
   - 自动检测 Python 项目
   - 确认配置后点击 "Deploy"

4. **等待部署完成**
   - 完成后会分配域名

---

### 方案三：Fly.io（免费额度）

**Fly.io** 适合需要全球部署的项目！

#### 部署步骤：

1. **注册 Fly.io**
   - 访问：https://fly.io
   - 注册账号（需要信用卡验证，但不收费）

2. **安装 Fly CLI**
   ```powershell
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

3. **登录并部署**
   ```bash
   fly auth login
   fly launch
   fly deploy
   ```

---

## 📋 配置文件说明

项目已包含以下部署配置文件：

| 文件 | 用途 |
|------|------|
| `render.yaml` | Render 平台配置（已创建） |
| `Dockerfile` | Docker 容器配置 |
| `docker-compose.yml` | Docker Compose 配置 |
| `start_with_waitress.py` | 生产服务器启动脚本 |

---

## 🎉 部署成功后

部署成功后，您将获得：

- ✅ 永久免费的公网网址
- ✅ 自动 HTTPS 加密
- ✅ 自动部署（每次推送代码自动更新）
- ✅ 全球 CDN 加速
- ✅ 免费 SSL 证书

---

## ⚠️ 注意事项

1. **免费方案的限制**：
   - Render 免费版：每月 750 小时运行时间（足够个人使用）
   - 休眠时间：15 分钟无访问会自动休眠（首次访问稍慢）

2. **如何保持活跃**：
   - 可以使用 https://uptimerobot.com 免费监控网站
   - 每 5 分钟自动访问一次，防止休眠

---

## 🆘 需要帮助？

如果部署过程中遇到问题：
1. 查看平台的日志输出
2. 提交 Issue 到 GitHub 仓库
3. 联系项目维护者

---

**祝您部署顺利！** 🚀
