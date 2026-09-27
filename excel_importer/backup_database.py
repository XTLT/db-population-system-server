import os
import shutil
import tarfile
import json
from datetime import datetime
from config import DB_PATH, BACKUP_DIR, PHOTOS_DIR
from database import get_db_password
from ._encrypt_backup import _encrypt_backup
from ._calculate_file_hash import _calculate_file_hash
from ._cleanup_old_backups import _cleanup_old_backups


def backup_database(manual: bool = False) -> dict:
    if not os.path.exists(DB_PATH):
        return {"success": False, "error": "数据库文件不存在"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    try:
        db_backup = os.path.join(backup_dir, "population.db")
        shutil.copy2(DB_PATH, db_backup)

        photos_backup = os.path.join(backup_dir, "photos.tar.gz")
        if os.path.exists(PHOTOS_DIR) and os.listdir(PHOTOS_DIR):
            with tarfile.open(photos_backup, "w:gz") as tar:
                tar.add(PHOTOS_DIR, arcname="Photos")

        password = get_db_password()
        if password:
            _encrypt_backup(backup_dir, password)

        db_hash = _calculate_file_hash(db_backup)
        manifest = {
            "timestamp": timestamp,
            "manual": manual,
            "db_hash": db_hash,
            "encrypted": bool(password),
            "complete": True
        }
        with open(os.path.join(backup_dir, "backup_complete.txt"), "w") as f:
            json.dump(manifest, f)

        _cleanup_old_backups()

        # 不返回完整路径，防止服务器路径泄露
        return {"success": True, "timestamp": timestamp}
    except Exception as e:
        return {"success": False, "error": str(e)}
