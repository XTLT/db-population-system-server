#!/bin/bash
# ============================================================
# 导出客户端打包用证书（server.crt + client.crt + client.key）
# ------------------------------------------------------------
# 用法: bash scripts/export_client_certs.sh [输出目录]
# 默认输出到 <安装目录>/export_cert/
# ============================================================
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$INSTALL_DIR/certs"
OUT="${1:-$INSTALL_DIR/export_cert}"

for f in server.crt client.crt client.key; do
    [ -f "$CERT_DIR/$f" ] || { echo "缺少 $CERT_DIR/$f，请先运行 install.sh 生成证书" >&2; exit 1; }
done

mkdir -p "$OUT"
TAR="$OUT/population_client_certs_$(date +%Y%m%d).tar.gz"
tar -czf "$TAR" -C "$CERT_DIR" server.crt client.crt client.key

echo ""
echo "== 已导出: $TAR =="
echo "打包桌面端/移动端时，把包内 3 个文件分别放入："
echo "  桌面端:  desktop/certs/       （server.crt + client.crt + client.key）"
echo "  移动端:  mobile/assets/certs/ （server.crt + client.crt + client.key）"
echo "打包完成后客户端即可连接本服务器。"
