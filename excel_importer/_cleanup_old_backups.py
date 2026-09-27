import os
import shutil
from datetime import datetime
from config import BACKUP_DIR


def _cleanup_old_backups():
    if not os.path.exists(BACKUP_DIR):
        return

    cutoff_date = datetime.now().timestamp() - (60 * 24 * 60 * 60)

    for item in os.listdir(BACKUP_DIR):
        item_path = os.path.join(BACKUP_DIR, item)
        if os.path.isdir(item_path) and item.startswith("backup_"):
            try:
                dir_time = os.path.getmtime(item_path)
                if dir_time < cutoff_date:
                    complete_file = os.path.join(item_path, "backup_complete.txt")
                    if os.path.exists(complete_file):
                        shutil.rmtree(item_path)
            except Exception:
                pass
