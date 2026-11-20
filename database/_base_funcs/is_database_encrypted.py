"""判断数据库是否处于加密状态（存在 .enc 文件）。"""

import os


def is_database_encrypted() -> bool:
    from .._base import DB_PATH
    return os.path.exists(DB_PATH + '.enc')
