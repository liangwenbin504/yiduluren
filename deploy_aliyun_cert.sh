#!/usr/bin/env bash
# ============================================================
# 仪度六壬择日 HTTPS 部署脚本（阿里云证书版 · 备选方案）
# 用法：
#   1) 在阿里云「数字证书管理服务」下载证书，选 Nginx 格式，
#      得到两个文件：xxx.pem 和 xxx.key
#   2) 把文件放到服务器 /opt/liuren/certs/ 下，命名为：
#        liuren.souhuertong.net.cn.pem
#        liuren.souhuertong.net.cn.key
#   3) 执行：sudo bash deploy_aliyun_cert.sh
# 前置：域名已解析到本机、阿里云安全组放行 443 端口
# ============================================================
set -e

DOMAIN=liuren.souhuertong.net.cn
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$APP_DIR/certs"
PEM="$SRC_DIR/$DOMAIN.pem"
KEY="$SRC_DIR/$DOMAIN.key"
DEST_DIR=/etc/nginx/certs

echo "==> 证书来源目录: $SRC_DIR"
echo "==> 域名: $DOMAIN"

# 0) 前置：openssl 用于校验
command -v openssl >/dev/null 2>&1 || { apt-get install -y openssl; }

# 1) 检查证书文件
mkdir -p "$SRC_DIR"
if [ ! -f "$PEM" ] || [ ! -f "$KEY" ]; then
  echo "❌ 缺少证书文件："
  echo "    $PEM"
  echo "    $KEY"
  echo "   请先把阿里云下载的 Nginx 格式证书（pem + key）放到 $SRC_DIR/ 并改名。"
  exit 1
fi

# 2) 校验 pem 格式
if ! openssl x509 -in "$PEM" -noout -subject -dates >/dev/null 2>&1; then
  echo "❌ $PEM 不是有效的 PEM 证书文件（阿里云下载时请选 Nginx 格式）"
  exit 1
fi
echo "==> 证书信息:"
openssl x509 -in "$PEM" -noout -subject -dates -issuer

# 3) 校验 pem 与 key 是否匹配
PEM_MD5=$(openssl x509 -in "$PEM" -noout -modulus | openssl md5)
KEY_MD5=$(openssl rsa -in "$KEY" -noout -modulus 2>/dev/null | openssl md5)
if [ "$PEM_MD5" != "$KEY_MD5" ]; then
  echo "❌ 证书与私钥不匹配（请确认下载的是同一张证书的 pem/key 对）"
  exit 1
fi
echo "==> ✅ 证书与私钥匹配"

# 4) 部署证书到 nginx 目录
mkdir -p "$DEST_DIR"
cp "$PEM" "$DEST_DIR/$DOMAIN.pem"
cp "$KEY" "$DEST_DIR/$DOMAIN.key"
chmod 644 "$DEST_DIR/$DOMAIN.pem"
chmod 600 "$DEST_DIR/$DOMAIN.key"

# 5) 部署 HTTPS nginx 配置（80 → 301 → 443），移除旧纯 HTTP 配置
echo "==> 部署 nginx HTTPS 配置 ..."
cp "$APP_DIR/nginx-liuren-https-aliyun.conf" /etc/nginx/conf.d/liuren-https.conf
rm -f /etc/nginx/conf.d/liuren.conf

# 6) 校验并重载
nginx -t
systemctl reload nginx

echo ""
echo "========================================================"
echo "✅ HTTPS 已启用：https://$DOMAIN/"
echo "   若浏览器仍打不开，请确认阿里云安全组已放行 443 端口："
echo "   控制台 → ECS 实例 → 安全组 → 入方向 → 添加 TCP 443（0.0.0.0/0）"
echo "   验证：curl -sI https://$DOMAIN/ | head -5"
echo "   证书到期前（阿里云控制台可见有效期）记得重新下载替换，"
echo "   或到期后在控制台申请新免费证书，重复本脚本即可。"
echo "========================================================"
