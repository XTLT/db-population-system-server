#!/bin/bash
# ============================================================
# 发布更新包到服务器（服务器即更新主源）
# ------------------------------------------------------------
# 用法: bash scripts/publish_update.sh <端> <文件> <版本号> <版本code> [更新说明]
#   端:   desktop | mobile | server
#   版本code: 整数，如 desktop v0.0.28 -> 28，mobile 0.0.24+24 -> 24
#   示例:
#     bash scripts/publish_update.sh desktop 人口通_安装程序_v0.0.28.exe 0.0.28 28 "修复若干问题"
#     bash scripts/publish_update.sh mobile  人口通_mobile_v0.0.24.apk  0.0.24 24 "新增小组字段"
#
# 发布后客户端（已配置服务器地址）即可检查到更新并从服务器下载。
# 更新包与 version.json 会写入 <安装目录>/updates/<端>/
# ============================================================
set -euo pipefail

TYPE="${1:?缺少端类型（desktop/mobile/server）}"
FILE="${2:?缺少更新包文件路径}"
VERSION="${3:?缺少版本号（如 0.0.28）}"
CODE="${4:?缺少版本code（如 28）}"
NOTES="${5:-}"

case "$TYPE" in
    desktop|mobile|server) ;;
    *) echo "端类型必须是 desktop/mobile/server" >&2; exit 1 ;;
esac

INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UPDATES_DIR="$INSTALL_DIR/updates/$TYPE"

[ -f "$FILE" ] || { echo "更新包不存在: $FILE" >&2; exit 1; }

mkdir -p "$UPDATES_DIR"
BASENAME="$(basename "$FILE")"
DST="$UPDATES_DIR/$BASENAME"

echo "== 1/3 复制更新包 =="
cp -a "$FILE" "$DST"
SIZE=$(stat -c %s "$DST" 2>/dev/null || wc -c < "$DST" | tr -d ' ')
SHA=$(sha256sum "$DST" | awk '{print $1}')
echo "  文件: $DST"
echo "  大小: $SIZE 字节，SHA256: $SHA"

echo "== 2/3 写入版本元数据 =="
cat > "$UPDATES_DIR/version.json" <<EOF
{
  "latest_version": "$VERSION",
  "version_code": $CODE,
  "file": "$BASENAME",
  "file_size": $SIZE,
  "sha256": "$SHA",
  "release_notes": "$NOTES",
  "updated_at": "$(date '+%Y-%m-%d %H:%M:%S')"
}
EOF
echo "  元数据: $UPDATES_DIR/version.json"

echo "== 3/4 清理旧更新包（只保留当前版本） =="
REMOVED=0
for f in "$UPDATES_DIR"/*; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    if [ "$base" != "$BASENAME" ] && [ "$base" != "version.json" ]; then
        rm -f "$f"
        REMOVED=$((REMOVED + 1))
        echo "  删除旧包: $base"
    fi
done
echo "  共清理 $REMOVED 个旧包（历史包不再积累，防止 updates 目录无限膨胀）"

echo "== 4/4 完成 =="
echo "已发布 $TYPE v$VERSION（code=$CODE）。客户端检查更新即可从服务器下载。"
