import os
import shutil
from datetime import datetime
from config import DB_PATH, BACKUP_DIR


def backup_database():
    if not os.path.exists(DB_PATH):
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"population_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path
