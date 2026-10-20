#!/bin/bash
# ============================================================
# 证书轮换脚本（26 服务器）
# 用法: sudo bash scripts/rotate_cert.sh
# 注意: 轮换后所有客户端（桌面端/移动端）内置证书校验将失败，
#       必须同步重新打包三端客户端！
# ============================================================
set -e

# systemd 服务实际使用的证书目录（与 population-server.service 的
# --certfile/--keyfile 路径一致，不要改到 config 的 CERT_DIR）
CERT_DIR=/root/population-system/data/certs
TS=$(date +%Y%m%d_%H%M%S)

echo "== 1/5 备份旧证书 =="
mkdir -p "$CERT_DIR/backup"
[ -f "$CERT_DIR/server.crt" ] && cp -a "$CERT_DIR/server.crt" "$CERT_DIR/backup/server.crt.$TS"
[ -f "$CERT_DIR/server.key" ] && cp -a "$CERT_DIR/server.key" "$CERT_DIR/backup/server.key.$TS"
echo "备份完成: $CERT_DIR/backup/server.{crt,key}.$TS"

echo "== 2/5 生成新证书（10年，含 SAN） =="
openssl req -x509 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days 3650 -nodes \
    -subj "/C=CN/ST=Local/L=Local/O=PopulationSystem/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:tension02.ren,IP:192.168.9.26"
chmod 600 "$CERT_DIR/server.key"
echo "新证书生成完成"

echo "== 3/5 重启服务加载新证书 =="
systemctl restart population-server
sleep 4
ACTIVE=$(systemctl is-active population-server)
echo "服务状态: $ACTIVE"
if [ "$ACTIVE" != "active" ]; then
    echo "!! 服务未启动，正在回滚证书 !!"
    cp -a "$CERT_DIR/backup/server.crt.$TS" "$CERT_DIR/server.crt"
    cp -a "$CERT_DIR/backup/server.key.$TS" "$CERT_DIR/server.key"
    systemctl restart population-server
    echo "已回滚"
    exit 1
fi

echo "== 4/5 验证新证书 =="
echo | openssl s_client -connect 127.0.0.1:5000 -servername tension02.ren 2>/dev/null | openssl x509 -noout -subject -dates

echo "== 5/5 完成 =="
echo "!!! 重要：必须同步重新打包三端客户端（桌面端/移动端内置证书校验）!!!"
echo "新证书文件: $CERT_DIR/server.crt（拷出用于客户端打包）"
