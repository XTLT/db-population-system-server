"""确保各数据子目录存在。"""

import os


def ensure_dirs():
    import config as _cfg

    os.makedirs(_cfg.PHOTOS_DIR, exist_ok=True)
    os.makedirs(_cfg.BACKUP_DIR, exist_ok=True)
    os.makedirs(_cfg.LOG_DIR, exist_ok=True)
    os.makedirs(_cfg.CERT_DIR, exist_ok=True)
    os.makedirs(_cfg.REPORTS_DIR, exist_ok=True)
    os.makedirs(_cfg.UPDATES_DIR, exist_ok=True)
