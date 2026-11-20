"""建表并执行列迁移（多进程并发启动时串行化，避免建表竞态）。"""

import os

from .get_engine import get_engine
from .migrate_db import migrate_db


def init_db():
    from .. import _base

    # 确保所有模型类已注册到 Base.metadata 后再建表
    from .. import models  # noqa: F401
    engine = get_engine()
    # 多进程并发启动（gunicorn 多 worker）时串行化建表/迁移，避免建表竞态
    lock_path = os.path.join(os.path.dirname(os.path.abspath(_base.DB_PATH)), '.init_db.lock')
    try:
        import fcntl
        with open(lock_path, 'w') as _lock_file:
            fcntl.flock(_lock_file, fcntl.LOCK_EX)
            _base.Base.metadata.create_all(engine)
            migrate_db(engine)
    except ImportError:
        _base.Base.metadata.create_all(engine)
        migrate_db(engine)
