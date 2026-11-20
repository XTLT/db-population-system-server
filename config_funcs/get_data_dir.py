"""读取数据目录：配置文件里解出的有效路径优先，否则回落到 BASE_DIR。"""

import os

from .decrypt_path import decrypt_path


def get_data_dir():
    import config as _cfg

    if os.path.exists(_cfg.CONFIG_FILE):
        try:
            with open(_cfg.CONFIG_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()
            if token:
                path = decrypt_path(token)
                if os.path.isdir(path):
                    return path
        except Exception:
            pass
    return _cfg.BASE_DIR
