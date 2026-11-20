"""列出所有带 manifest 的备份目录，按目录名（即时间）倒序。"""

import json
import os

from config import BACKUP_DIR
from .constants import MANIFEST_NAME


def list_backups():
    items = []
    if not os.path.isdir(BACKUP_DIR):
        return items
    for name in os.listdir(BACKUP_DIR):
        if not name.startswith("backup_"):
            continue
        path = os.path.join(BACKUP_DIR, name)
        if not os.path.isdir(path):
            continue
        manifest_path = os.path.join(path, MANIFEST_NAME)
        if not os.path.exists(manifest_path):
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            continue
        items.append({"name": name, "path": path, "manifest": manifest})
    items.sort(key=lambda x: x["name"], reverse=True)
    return items
