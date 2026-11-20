"""创建（或复用）SQLite engine，并设置 WAL / busy_timeout 等 PRAGMA。"""

from sqlalchemy import create_engine, event


def get_engine():
    from .. import _base

    if _base._engine is None:
        # timeout=30：WAL 下写是串行的，多 worker/多线程并发写时延长等待，
        # 避免批量导入等场景偶发 "database is locked"（sqlite3 默认仅 5 秒）。
        engine = create_engine(f"sqlite:///{_base.DB_PATH}", echo=False,
                               connect_args={"timeout": 30})

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            # WAL：读写不互相阻塞，gunicorn 多 worker + 多线程下不再频繁 database is locked
            cursor.execute("PRAGMA journal_mode=WAL")
            # NORMAL：WAL 下只有 checkpoint 时刷盘，事务提交本身仍是原子的
            cursor.execute("PRAGMA synchronous=NORMAL")
            # busy_timeout 与 connect_args 的 timeout=30 等价（都是 30000ms），
            # 这里显式再设一次，保证每个物理连接都带足等待时间
            cursor.execute("PRAGMA busy_timeout=30000")
            # WAL 文件上限 64MB：checkpoint 后自动截断，避免 -wal 无限增长占盘
            cursor.execute("PRAGMA journal_size_limit=67108864")
            # 刻意不开 mmap_size：多进程写入 + mmap 会放大 WAL reset 竞态，
            # 实测出现过 "database disk image is malformed"（只能 .recover 捞数据）。
            # 本机是 gunicorn 多 worker 共享一个库，风险不可接受。
            #
            # 刻意不开 foreign_keys=ON：现有数据存在软删除/迁移/换户主等先删后插的
            # 写入路径，开启后可能拒绝历史数据上的合法写入；且与"防锁死/防损坏"
            # 这个目标无关，属于独立的行为变更，不在本轮范围。
            cursor.close()

        _base._engine = engine
    return _base._engine
