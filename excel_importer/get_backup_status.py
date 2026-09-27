import os
from datetime import datetime
from config import BACKUP_DIR


def get_backup_status() -> dict:
    if not os.path.exists(BACKUP_DIR):
        return {"last_backup": None, "status": "无备份"}

    backups = []
    for item in os.listdir(BACKUP_DIR):
        if item.startswith("backup_"):
            item_path = os.path.join(BACKUP_DIR, item)
            complete_file = os.path.join(item_path, "backup_complete.txt")
            if os.path.exists(complete_file):
                backups.append({
                    "path": item_path,
                    "time": os.path.getmtime(item_path)
                })

    if not backups:
        return {"last_backup": None, "status": "无备份"}

    latest = max(backups, key=lambda x: x["time"])
    return {
        "last_backup": datetime.fromtimestamp(latest["time"]).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "正常"
    }
