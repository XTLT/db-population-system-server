import os
import subprocess
from config import PHOTOS_DIR
from ._validate_path_for_shell import _validate_path_for_shell


def open_photos_folder():
    """打开照片文件夹

    安全修复：使用 subprocess 替代 os.system 防止命令注入
    """
    # 验证路径安全性
    if not _validate_path_for_shell(PHOTOS_DIR):
        print(f"警告：照片目录路径包含不安全字符，拒绝打开: {PHOTOS_DIR}")
        return False

    if not os.path.isdir(PHOTOS_DIR):
        print(f"照片目录不存在: {PHOTOS_DIR}")
        return False

    try:
        if os.name == "nt":
            os.startfile(PHOTOS_DIR)
        else:
            # 使用 subprocess.run 替代 os.system，参数列表形式防止注入
            subprocess.run(['xdg-open', PHOTOS_DIR], check=False)
        return True
    except Exception as e:
        print(f"打开照片文件夹失败: {e}")
        return False
