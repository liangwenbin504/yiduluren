#!/usr/bin/env bash
# ============================================================
# 仪度六壬择日 HTTPS 一键启用脚本（Let's Encrypt / certbot 版 · 推荐）
# 在服务器 /opt/liuren 下执行：sudo bash enable_https.sh
#
# 前置条件：
#   1) 域名 liuren.souhuertong.net.cn 已解析到本服务器（HTTP 能访问即满足）
#   2) 服务器可访问外网（Let's Encrypt 签发）
#   3) 阿里云安全组放行 443 端口（脚本只能检测本机，云控制台需手动放行）
#
# 流程：安装 certbot → 签发 Let's Encrypt 证书 → 部署 HTTPS 配置 → 重载 nginx
# 续期：certbot renew（自带 systemd timer 自动续期，无需手动）
# ============================================================
set -e

DOMAIN=liuren.souhuertong.net.cn
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
HTTP_CONF="$APP_DIR/nginx-liuren.conf"
HTTPS_CONF="$APP_DIR/nginx-liuren-https.conf"
# 如需接收续期提醒邮件，把下面改为你的邮箱（否则用 --register-unsafely-without-email）
CERTBOT_EMAIL=""

echo "==> 应用目录: $APP_DIR"
echo "==> 域名: $DOMAIN"

# 0) 前置检查
if ! command -v nginx >/dev/null 2>&1; then
  echo "❌ 未检测到 nginx（请先按 install_on_server.sh 完成部署）"
  exit 1
fi
if ! systemctl is-active --quiet nginx; then
  echo "==> nginx 未运行，先启动 ..."
  systemctl start nginx
fi

# 0.5) 80 端口必须能访问（ACME HTTP-01 挑战需要；浏览器能开不代表本机 curl 能通）
if ! curl -s -o /dev/null --max-time 10 "http://$DOMAIN/"; then
  echo "⚠️  本机 curl 无法访问 http://$DOMAIN —— 请确认域名解析和 80 端口安全组放行"
  echo "    继续尝试签发（可能失败）……"
fi

# 1) 确保签发前 80 端口是普通反代（certbot --nginx 需要可注入验证路径的 location /）
if [ ! -f /etc/nginx/conf.d/liuren.conf ]; then
  echo "==> 恢复 80 端口反代配置（供证书签发验证用）..."
  cp "$HTTP_CONF" /etc/nginx/conf.d/liuren.conf
  nginx -t && systemctl reload nginx
fi

# 2) 安装 certbot（含 nginx 插件，仅用于签发，不改动现有配置）
if ! command -v certbot >/dev/null 2>&1; then
  echo "==> 安装 certbot ..."
  apt-get update >/dev/null 2>&1 || true
  apt-get install -y certbot python3-certbot-nginx
fi

# 3) 签发证书（certonly：只签发证书，不自动改 nginx 配置）
echo "==> 签发 Let's Encrypt 证书 ..."
EMAIL_ARGS=()
if [ -n "$CERTBOT_EMAIL" ]; then
  EMAIL_ARGS=(-m "$CERTBOT_EMAIL" --no-eff-email)
else
  EMAIL_ARGS=(--register-unsafely-without-email)
fi
certbot certonly --nginx -d "$DOMAIN" --agree-tos "${EMAIL_ARGS[@]}" --non-interactive \
  || { echo "❌ 证书签发失败（常见原因：80 端口挑战不通 / 服务器无法访问 Let's Encrypt）"; exit 1; }

# 4) 部署 HTTPS 配置（总是覆盖，避免残留旧证书路径）
echo "==> 部署 HTTPS nginx 配置 ..."
cp -f "$HTTPS_CONF" /etc/nginx/conf.d/liuren-https.conf
# 移除旧纯 HTTP 配置，避免与 80→443 重定向冲突
rm -f /etc/nginx/conf.d/liuren.conf

# 5) 校验并重载 nginx
echo "==> 校验并重载 nginx ..."
nginx -t
systemctl reload nginx

# 6) 启用自动续期（certbot 安装时自带 certbot.timer）
systemctl enable certbot.timer >/dev/null 2>&1 || true
systemctl start certbot.timer >/dev/null 2>&1 || true

echo ""
echo "========================================================"
echo "✅ HTTPS 已启用：https://$DOMAIN/"
echo "   提醒：若浏览器仍打不开，请在阿里云控制台确认安全组已放行 443 端口"
echo "   （ECS 实例 → 安全组 → 入方向规则 → 添加 TCP 443）"
echo "   证书自动续期：certbot renew（timer 已启用）"
echo "   验证：curl -sI https://$DOMAIN/ | head -5"
echo "========================================================"
