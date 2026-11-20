"""生成一份完整数据库备份（含照片、可选加密、清单与清理）。"""

import json
import os
import shutil
import tarfile
from datetime import datetime

from config import DB_PATH, BACKUP_DIR, PHOTOS_DIR
from database import get_db_password
from .._encrypt_backup import _encrypt_backup
from .._calculate_file_hash import _calculate_file_hash
from .._cleanup_old_backups import _cleanup_old_backups
from .sqlite_backup import sqlite_backup
from .integrity_check import integrity_check


def backup_database(manual: bool = False) -> dict:
    if not os.path.exists(DB_PATH):
        return {"success": False, "error": "数据库文件不存在"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    try:
        db_backup = os.path.join(backup_dir, "population.db")
        sqlite_backup(DB_PATH, db_backup)

        # 备份完立刻校验：损坏的备份宁可不留，也不能让它冒充"完整备份"
        integrity = integrity_check(db_backup)
        if integrity.lower() != "ok":
            raise RuntimeError(f"备份完整性校验失败: {integrity}")

        photos_backup = os.path.join(backup_dir, "photos.tar.gz")
        if os.path.exists(PHOTOS_DIR) and os.listdir(PHOTOS_DIR):
            with tarfile.open(photos_backup, "w:gz") as tar:
                tar.add(PHOTOS_DIR, arcname="Photos")

        # 先算 hash 再加密：_encrypt_backup 会把 population.db 换成 population.db.enc，
        # 之后 _calculate_file_hash 就找不到明文文件了（设置库密码时备份曾因此整体失败）
        db_hash = _calculate_file_hash(db_backup)

        password = get_db_password()
        if password:
            _encrypt_backup(backup_dir, password)

        manifest = {
            "timestamp": timestamp,
            "manual": manual,
            "db_hash": db_hash,
            "encrypted": bool(password),
            "integrity": integrity,
            "method": "sqlite_backup_api",
            "complete": True
        }
        with open(os.path.join(backup_dir, "backup_complete.txt"), "w") as f:
            json.dump(manifest, f)

        _cleanup_old_backups()

        # 不返回完整路径，防止服务器路径泄露
        return {"success": True, "timestamp": timestamp, "integrity": integrity}
    except Exception as e:
        # 没有 backup_complete.txt 的半成品目录既不会被 get_backup_list 列出，
        # 也不会被 _cleanup_old_backups 删除（后者要求 manifest 存在），必须自己清掉
        shutil.rmtree(backup_dir, ignore_errors=True)
        return {"success": False, "error": str(e)}
