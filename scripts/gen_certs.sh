#!/bin/bash
# ============================================================
# 生成人口通 mTLS 证书：CA + 服务器证书(SAN) + 客户端证书
# ------------------------------------------------------------
# 用法: bash scripts/gen_certs.sh <证书目录> [域名,逗号分隔]
# 环境变量 FORCE=1 可强制重新生成（会覆盖旧证书，旧客户端将失效！）
# ============================================================
set -euo pipefail

CERT_DIR="${1:?缺少证书目录参数}"
DOMAINS_CSV="${2:-}"

mkdir -p "$CERT_DIR"

# 幂等：证书已存在且未强制生成时直接跳过
if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/client.crt" ] && [ "${FORCE:-0}" != "1" ]; then
    echo "[INFO] 证书已存在，跳过生成（如需重新生成请用 FORCE=1）"
    exit 0
fi

# ---- 组装 SAN：localhost + 指定域名 + 本机全部 IP（IPv4/IPv6）----
SAN="DNS:localhost"
if [ -n "$DOMAINS_CSV" ]; then
    IFS=',' read -ra DMS <<< "$DOMAINS_CSV"
    for d in "${DMS[@]}"; do
        d="$(echo "$d" | xargs)"
        [ -n "$d" ] && SAN="$SAN,DNS:$d"
    done
fi
IPS="$(hostname -I 2>/dev/null || true)"
if [ -z "$IPS" ]; then
    IPS="$(ip -o addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | tr '\n' ' ' || true)"
fi
for ip in $IPS; do
    [ -n "$ip" ] && SAN="$SAN,IP:$ip"
done
echo "[INFO] 证书 SAN: $SAN"

# ---- 备份旧证书 ----
if [ -f "$CERT_DIR/server.crt" ]; then
    TS=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$CERT_DIR/backup"
    cp -a "$CERT_DIR/server.crt" "$CERT_DIR/backup/server.crt.$TS" 2>/dev/null || true
    cp -a "$CERT_DIR/server.key" "$CERT_DIR/backup/server.key.$TS" 2>/dev/null || true
    echo "[INFO] 旧证书已备份到 $CERT_DIR/backup/"
fi

# ---- 1/4 CA（自签根证书）----
openssl req -x509 -newkey rsa:2048 \
    -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \
    -days 3650 -nodes \
    -subj "/C=CN/O=PopulationSystem/CN=population-ca" >/dev/null 2>&1

# ---- 2/4 服务器证书（SAN，供 stunnel 对外出示，客户端按指纹校验）----
openssl req -newkey rsa:2048 \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
    -nodes -subj "/C=CN/O=PopulationSystem/CN=population-server" >/dev/null 2>&1
openssl x509 -req -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
    -days 3650 -sha256 \
    -extfile <(echo "subjectAltName=$SAN") \
    -out "$CERT_DIR/server.crt" >/dev/null 2>&1

# ---- 3/4 客户端证书（供桌面端/移动端 mTLS 出示）----
openssl req -newkey rsa:2048 \
    -keyout "$CERT_DIR/client.key" -out "$CERT_DIR/client.csr" \
    -nodes -subj "/C=CN/O=PopulationSystem/CN=population-client" >/dev/null 2>&1
openssl x509 -req -in "$CERT_DIR/client.csr" \
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
    -days 3650 -sha256 \
    -out "$CERT_DIR/client.crt" >/dev/null 2>&1

# ---- 4/4 收尾：权限与清理 ----
chmod 600 "$CERT_DIR"/*.key 2>/dev/null || true
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/client.csr"

echo ""
echo "== 证书生成完成（10 年有效期）=="
echo "  服务器证书(客户端内置校验): $CERT_DIR/server.crt"
echo "  客户端证书(客户端内置出示): $CERT_DIR/client.crt + client.key"
echo "  CA(服务器端校验客户端):     $CERT_DIR/ca.crt + ca.key"
echo "!! 客户端打包必须使用本机生成的这 3 个文件，否则客户端无法连接本服务器 !!"
