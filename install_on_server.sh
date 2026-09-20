#!/usr/bin/env bash
# 仪度六壬择日 部署脚本（服务器 /opt/liuren 解压后运行：sudo bash install_on_server.sh）
# 安全设计：
#   1) 若服务器已装 Nginx —— 只往现有 Nginx 追加反代，绝不重装、不删暑假守护等现有站点。
#   2) 若未装 Nginx 且 80 空闲 —— 才安装 Nginx 并加反代。
#   3) 若未装 Nginx 但 80 被非 Nginx 占用 —— 跳过，提示手动加反代。
#   4) 绝不删除任何已有 Nginx 配置 / default 站点。
set -e

APP_DIR=/opt/liuren
echo "==> 应用目录: $APP_DIR"

# 1) 修复 EOL 系统 apt 源（Ubuntu 23.04 已 EOL，标准源失效 → 切 old-releases）
if ! apt-get update >/dev/null 2>&1; then
  echo "==> apt 标准源失效，切到 old-releases（EOL 系统）"
  codename=$(. /etc/os-release 2>/dev/null; echo "${VERSION_CODENAME:-lunar}")
  cat > /etc/apt/sources.list <<EOF
deb http://old-releases.ubuntu.com/ubuntu/ ${codename} main restricted universe multiverse
deb http://old-releases.ubuntu.com/ubuntu/ ${codename}-updates main restricted universe multiverse
deb http://old-releases.ubuntu.com/ubuntu/ ${codename}-security main restricted universe multiverse
EOF
  apt-get update || { echo "❌ apt 仍失败，请手动处理软件源后重试"; exit 1; }
fi

# 2) 基础系统依赖（不含 nginx，nginx 在第 5 步按需处理）
DEBS="python3-venv python3-pip build-essential python3-dev"
apt-get install -y $DEBS

# 3) 虚拟环境 + 依赖（用阿里云镜像，国内服务器速度快）
cd "$APP_DIR"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-deploy.txt

# 4) systemd 服务（始终安装，独立于 Nginx）
cp "$APP_DIR/liuren.service" /etc/systemd/system/liuren.service
systemctl daemon-reload
systemctl enable liuren
systemctl restart liuren
sleep 2
if systemctl is-active --quiet liuren; then
  echo "✅ liuren 服务已启动 (127.0.0.1:5555)"
else
  echo "⚠️  liuren 服务未正常运行，查看: journalctl -u liuren -n 50"
fi

# 5) Nginx 反代（智能：追加 / 安装 / 跳过）
if command -v nginx >/dev/null 2>&1; then
  echo "==> 检测到已安装 Nginx，追加 liuren 反代（不重装、不删现有站点）"
  # 保护机制：若现有 liuren.conf 已配置 HTTPS(443)，保留不覆盖，防止证书配置丢失
  if grep -qF "listen 443 ssl" /etc/nginx/conf.d/liuren.conf 2>/dev/null; then
    echo "==> 现有 liuren.conf 已配置 HTTPS(443)，保留不覆盖以保护证书配置"
  else
    cp "$APP_DIR/nginx-liuren.conf" /etc/nginx/conf.d/liuren.conf
  fi
  if nginx -t 2>/dev/null; then
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    systemctl enable nginx 2>/dev/null || true
    echo "✅ 已在现有 Nginx 追加反代 -> https://liuren.souhuertong.net.cn"
  else
    echo "⚠️  nginx -t 失败，请检查现有 Nginx 配置是否冲突（暑假守护等）"
  fi
else
  # Nginx 未安装：看 80 端口是否空闲
  PORT80=0
  if command -v ss >/dev/null 2>&1; then
    ss -tlnp 2>/dev/null | grep -qE ':80\b' && PORT80=1 || true
  fi
  if [ "$PORT80" -eq 1 ]; then
    echo "❌ 80 端口已被非 Nginx 服务占用，未安装 Nginx。"
    echo "   请在该服务上加反代指向 127.0.0.1:5555（location / { proxy_pass http://127.0.0.1:5555; }），"
    echo "   或在释放 80 端口后重跑此步。Python 服务与 systemd 已就绪。"
  else
    echo "==> 80 端口空闲，安装 Nginx"
    apt-get install -y nginx
    # 新安装 Nginx，liuren.conf 不存在，直接写入模板（已含 HTTP+HTTPS，后续再用 certbot 签发证书）
    cp "$APP_DIR/nginx-liuren.conf" /etc/nginx/conf.d/liuren.conf
    if nginx -t 2>/dev/null; then
      systemctl restart nginx && systemctl enable nginx
      echo "✅ Nginx 已安装并配置反代 -> https://liuren.souhuertong.net.cn"
      echo "   注：首次部署后请用 certbot 签发 HTTPS 证书（模板已指向 /etc/letsencrypt/live/liuren.souhuertong.net.cn/）"
    else
      echo "⚠️  nginx -t 失败，请检查 /etc/nginx/conf.d/liuren.conf"
    fi
  fi
fi

echo ""
echo "==> 部署脚本执行完毕。"
echo "   外部访问需：阿里云安全组放行 80/443 端口"
echo "   HTTPS 证书：certbot.timer 已启用自动续期（首次部署需 certbot run --nginx -d liuren.souhuertong.net.cn 签发）"
echo "   本地自检：curl -s http://127.0.0.1:5555/ | head"
echo "   外网自检：curl -s https://liuren.souhuertong.net.cn/ -k | head"
