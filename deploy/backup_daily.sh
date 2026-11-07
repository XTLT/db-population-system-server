#!/bin/bash
# 每日备份入口：自动定位部署目录并选择 venv 或系统 python
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(dirname "$SCRIPT_DIR")"
PY="$BASE/venv/bin/python"
if [ ! -x "$PY" ]; then
    PY="$(command -v python3)"
fi
exec "$PY" "$BASE/deploy/backup_daily.py"
