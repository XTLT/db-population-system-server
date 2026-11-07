import os
import sqlite3
import tarfile
import json
import shutil
from datetime import datetime
from config import DB_PATH, BACKUP_DIR, PHOTOS_DIR
from database import get_db_password
from ._encrypt_backup import _encrypt_backup
from ._calculate_file_hash import _calculate_file_hash
from ._cleanup_old_backups import _cleanup_old_backups


def _sqlite_backup(src_path: str, dst_path: str) -> None:
    """用 SQLite 在线备份 API 生成一致快照。

    不能直接 copy 数据库文件：WAL 模式下已提交但还没 checkpoint 的事务只存在于
    <db>-wal 里，拷主库会漏数据；并发写入时还可能拷到写了一半的页。
    Connection.backup() 由 SQLite 自己持读锁逐页拷贝，得到的是一致快照，
    且会把 WAL 里已提交的内容一并写进目标库。
    """
    src = sqlite3.connect(src_path, timeout=30)
    dst = sqlite3.connect(dst_path)
    try:
        src.backup(dst)
    finally:
        try:
            dst.close()
        finally:
            src.close()


def _integrity_check(db_path: str) -> str:
    """对库文件跑 PRAGMA integrity_check，返回结果文本（正常为 "ok"）。"""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return "; ".join(str(r[0]) for r in rows)
    finally:
        conn.close()


def backup_database(manual: bool = False) -> dict:
    if not os.path.exists(DB_PATH):
        return {"success": False, "error": "数据库文件不存在"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    try:
        db_backup = os.path.join(backup_dir, "population.db")
        _sqlite_backup(DB_PATH, db_backup)

        # 备份完立刻校验：损坏的备份宁可不留，也不能让它冒充"完整备份"
        integrity = _integrity_check(db_backup)
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
