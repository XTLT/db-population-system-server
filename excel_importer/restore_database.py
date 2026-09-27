import os
import shutil
import tarfile
import json
from datetime import datetime
from config import DB_PATH, PHOTOS_DIR
from ._decrypt_backup import _decrypt_backup


def restore_database(backup_path: str, password: str = None) -> dict:
    """
    从备份恢复数据库

    Args:
        backup_path: 备份目录路径
        password: 解密密码（如果备份已加密）

    Returns:
        恢复结果字典
    """
    if not os.path.exists(backup_path):
        return {"success": False, "error": "备份文件不存在"}

    complete_file = os.path.join(backup_path, "backup_complete.txt")
    if not os.path.exists(complete_file):
        return {"success": False, "error": "备份不完整"}

    try:
        # 读取清单
        with open(complete_file, "r") as f:
            manifest = json.load(f)

        # 如果备份已加密，需要解密
        if manifest.get("encrypted"):
            if not password:
                return {"success": False, "error": "需要解密密码"}

            _decrypt_backup(backup_path, password)

        # 恢复数据库
        db_backup = os.path.join(backup_path, "population.db")
        if not os.path.exists(db_backup):
            return {"success": False, "error": "数据库备份文件不存在"}

        # 备份当前数据库
        current_backup = f"{DB_PATH}.before_restore"
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, current_backup)

        # 恢复数据库
        shutil.copy2(db_backup, DB_PATH)

        # 恢复照片
        photos_backup = os.path.join(backup_path, "photos.tar.gz")
        if os.path.exists(photos_backup):
            if os.path.exists(PHOTOS_DIR):
                shutil.rmtree(PHOTOS_DIR)
            os.makedirs(PHOTOS_DIR, exist_ok=True)

            # 安全解压：防止 Tar Slip 路径遍历攻击
            with tarfile.open(photos_backup, "r:gz") as tar:
                for member in tar.getmembers():
                    # 检查路径是否在允许的目录内
                    member_path = os.path.join(PHOTOS_DIR, member.name)
                    real_member_path = os.path.realpath(os.path.abspath(member_path))

                    # 防止路径遍历
                    if not real_member_path.startswith(os.path.realpath(PHOTOS_DIR)):
                        raise ValueError(f"检测到恶意路径: {member.name}")

                    # 防止绝对路径
                    if member.name.startswith('/') or ':' in member.name:
                        raise ValueError(f"检测到非法路径: {member.name}")

                    # 防止符号链接攻击
                    if member.issym() or member.islnk():
                        raise ValueError("不允许符号链接")

                    tar.extract(member, PHOTOS_DIR)

        return {
            "success": True,
            "timestamp": manifest.get("timestamp"),
            "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # 清理解密后的文件
        if manifest.get("encrypted"):
            for filename in os.listdir(backup_path):
                if filename.endswith(".db") or filename.endswith(".tar.gz"):
                    filepath = os.path.join(backup_path, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
