"""从旧应用名目录迁移配置文件到新目录（仅升级时执行一次）。"""

import os
import shutil


def migrate_old_appdata():
    import config as _cfg

    if not os.path.isdir(_cfg._OLD_APPDATA_DIR):
        return
    os.makedirs(_cfg.APPDATA_DIR, exist_ok=True)
    for item in os.listdir(_cfg._OLD_APPDATA_DIR):
        src = os.path.join(_cfg._OLD_APPDATA_DIR, item)
        dst = os.path.join(_cfg.APPDATA_DIR, item)
        if os.path.exists(dst):
            continue
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
