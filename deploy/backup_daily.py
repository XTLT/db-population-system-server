"""每日数据库备份（由 systemd timer 调用）。

复用 excel_importer.backup_database(manual=False) 的完整备份流程（数据库 + 照片 + 加密 + 校验文件），
额外按“份数”轮转自动备份，避免每天一份把磁盘写满；手工备份不参与轮转。
"""
import json
import os
import shutil
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import BACKUP_DIR  # noqa: E402
from excel_importer import backup_database  # noqa: E402

KEEP_AUTO = 14
LOG_PATH = os.path.join(BACKUP_DIR, "auto_backup.log")


def _is_auto_backup(path: str) -> bool:
    manifest = os.path.join(path, "backup_complete.txt")
    if not os.path.exists(manifest):
        return False
    try:
        with open(manifest, "r", encoding="utf-8") as f:
            return json.load(f).get("manual") is False
    except Exception:
        return False


def rotate_auto_backups() -> int:
    """只保留最近 KEEP_AUTO 份自动备份，返回删除数量。"""
    if not os.path.isdir(BACKUP_DIR):
        return 0
    items = [
        d for d in os.listdir(BACKUP_DIR)
        if d.startswith("backup_") and os.path.isdir(os.path.join(BACKUP_DIR, d))
    ]
    items.sort(reverse=True)  # 目录名是 backup_YYYYMMDD_HHMMSS，字典序即时间序
    removed = 0
    for name in items[KEEP_AUTO:]:
        path = os.path.join(BACKUP_DIR, name)
        if _is_auto_backup(path):
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
    return removed


def main() -> int:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    result = backup_database(manual=False)
    removed = rotate_auto_backups()

    status = "OK" if result.get("success") else "FAIL"
    line = (
        f"{datetime.now():%Y-%m-%d %H:%M:%S} {status} "
        f"timestamp={result.get('timestamp', '')} "
        f"integrity={result.get('integrity', '')} "
        f"method=sqlite_backup_api "
        f"error={result.get('error', '')} removed={removed}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
