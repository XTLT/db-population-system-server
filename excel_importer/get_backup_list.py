import os
import json
from datetime import datetime
from config import BACKUP_DIR


def get_backup_list() -> list:
    """
    获取所有备份列表

    Returns:
        备份信息列表，每项包含：
        - timestamp: 备份时间戳
        - time: 格式化时间
        - path: 备份路径
        - size: 备份大小（字节）
        - encrypted: 是否加密
        - manual: 是否手动备份
    """
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for item in os.listdir(BACKUP_DIR):
        if item.startswith("backup_"):
            item_path = os.path.join(BACKUP_DIR, item)
            complete_file = os.path.join(item_path, "backup_complete.txt")

            if os.path.exists(complete_file):
                try:
                    with open(complete_file, "r") as f:
                        manifest = json.load(f)

                    # 计算备份大小
                    total_size = 0
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)

                    backups.append({
                        "timestamp": manifest.get("timestamp", ""),
                        "time": datetime.fromtimestamp(os.path.getmtime(item_path)).strftime("%Y-%m-%d %H:%M:%S"),
                        "name": item,  # 只返回备份目录名，不返回完整路径
                        "size": total_size,
                        "encrypted": manifest.get("encrypted", False),
                        "manual": manifest.get("manual", False)
                    })
                except Exception:
                    pass

    # 按时间倒序排列
    backups.sort(key=lambda x: x["time"], reverse=True)
    return backups
