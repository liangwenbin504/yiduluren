# ============================================================
# 仪度六壬择日 - 阿里云 OSS 部署指南
# ============================================================
# 
# 场景：本地 Windows → 阿里云 OSS → 云服务器
# 优势：绕过 SCP 密码交互，支持断点续传、大文件稳定上传
#
# 前提条件：
#   1. 已安装 ossutil (阿里云 OSS 命令行工具)
#      下载: https://help.aliyun.com/zh/oss/developer-reference/install-ossutil
#   2. 或使用 aliyun CLI (需要 AccessKey)
#
# ============================================================

# ============ 步骤 0: 准备工作 ============

# 切换到项目目录
cd e:\仪度六壬择日\yiduluren

# 确认部署包存在
dir liuren-deploy-update.zip

# ============ 步骤 1: 配置 ossutil ============

# 首次使用需要配置 AccessKey
# 如果已经配置过，可跳过此步
ossutil config

# 按提示输入：
# - AccessKey ID: 你的阿里云 AK
# - AccessKey Secret: 你的阿里云 SK
# - Endpoint: oss-cn-shenzhen.aliyuncs.com (根据你的地域)
# - Bucket: 你的 Bucket 名称

# ============ 步骤 2: 上传部署包到 OSS ============

# 使用 ossutil 上传（推荐）
ossutil cp "liuren-deploy-update.zip" "oss://liuren-deploy/liuren-deploy-update.zip" -f

# 如果需要指定配置文件
ossutil cp "liuren-deploy-update.zip" "oss://liuren-deploy/liuren-deploy-update.zip" -f -c ~/.ossutilconfig

# 使用 aliyun CLI 上传 (备选)
# 安装: pip install aliyun-python-sdk-oss
# 或使用: aliyun oss cp liuren-deploy-update.zip oss://liuren-deploy/

# ============ 步骤 3: 在云服务器上下载并部署 ============

# 登录服务器
ssh root@47.97.244.134

# 在服务器上执行：

# 方式 A: 使用 wget 下载 (需要 OSS 设置为公共读)
# 如果 Bucket 是公共读：
wget -O /tmp/liuren-deploy-update.zip \
  "https://liuren-deploy.oss-cn-shenzhen.aliyuncs.com/liuren-deploy-update.zip"

# 方式 B: 使用 ossutil 在服务器上下载 (推荐，更安全)
# 1. 在服务器上安装 ossutil
# curl -o /usr/local/bin/ossutil https://gosspublic.alicdn.com/ossutil/1.7.14/ossutil64
# chmod +x /usr/local/bin/ossutil

# 2. 配置 AccessKey (在服务器上)
# ossutil config

# 3. 下载文件
ossutil cp "oss://liuren-deploy/liuren-deploy-update.zip" "/tmp/liuren-deploy-update.zip" -f

# ============ 步骤 4: 服务器上部署 ============

# 在服务器上执行部署脚本
cd /tmp

# 解压
if command -v unzip &>/dev/null; then
    unzip -o liuren-deploy-update.zip -d liuren_temp
elif command -v python3 &>/dev/null; then
    python3 -c "import zipfile; zipfile.ZipFile('liuren-deploy-update.zip').extractall('liuren_temp')"
fi

# 备份旧版本并部署
if [ -d /opt/liuren ]; then
    cp -r /opt/liuren /opt/liuren.bak_$(date +%Y%m%d_%H%M%S)
fi

# 复制到目标目录
cp -rf liuren_temp/* /opt/liuren/

# 运行安装脚本
cd /opt/liuren
bash install_on_server.sh

# 清理
cd /tmp
rm -rf liuren_temp liuren-deploy-update.zip

# ============ 步骤 5: 验证 ============

# 检查服务状态
systemctl status liuren

# 查看日志
journalctl -u liuren -n 50 --no-pager

# 测试 API
curl -s http://127.0.0.1:5555/ | head -20

# 外网访问
curl -s https://liuren.souhuertong.net.cn/ | head -20


# ============================================================
# 快捷命令汇总（一行式）
# ============================================================

# 【本地 Windows】一键上传到 OSS
# ossutil cp "e:\仪度六壬择日\yiduluren\liuren-deploy-update.zip" "oss://liuren-deploy/liuren-deploy-update.zip" -f

# 【服务器】一键部署（需要已配置 ossutil）
# ssh root@47.97.244.134 'cd /tmp && ossutil cp oss://liuren-deploy/liuren-deploy-update.zip ./ -f && unzip -o liuren-deploy-update.zip -d liuren_temp && [ -d /opt/liuren ] && cp -r /opt/liuren /opt/liuren.bak_$(date +%Y%m%d_%H%M%S) && cp -rf liuren_temp/* /opt/liuren/ && cd /opt/liuren && bash install_on_server.sh && rm -rf /tmp/liuren_temp /tmp/liuren-deploy-update.zip'


# ============================================================
# 故障排查
# ============================================================

# 如果 ossutil 上传失败：
# 1. 检查 Bucket 是否存在：ossutil ls oss://liuren-deploy/
# 2. 检查权限：Bucket ACL 需要为公共读或使用 STS Token
# 3. 检查网络：ping oss-cn-shenzhen.aliyuncs.com

# 如果服务器下载失败：
# 1. 检查 ossutil 是否已安装：which ossutil
# 2. 检查 AccessKey 是否正确：cat ~/.ossutilconfig
# 3. 检查 Bucket 区域是否匹配

# 如果部署后服务无法启动：
# 1. 查看日志：journalctl -u liuren -n 100
# 2. 检查端口：ss -tlnp | grep 5555
# 3. 检查 Nginx：nginx -t && systemctl status nginx
