"""用 SQLite 在线备份 API 生成一致快照。

不能直接 copy 数据库文件：WAL 模式下已提交但还没 checkpoint 的事务只存在于
<db>-wal 里，拷主库会漏数据；并发写入时还可能拷到写了一半的页。
Connection.backup() 由 SQLite 自己持读锁逐页拷贝，得到的是一致快照，
且会把 WAL 里已提交的内容一并写进目标库。
"""

import sqlite3


def sqlite_backup(src_path: str, dst_path: str) -> None:
    src = sqlite3.connect(src_path, timeout=30)
    dst = sqlite3.connect(dst_path)
    try:
        src.backup(dst)
    finally:
        try:
            dst.close()
        finally:
            src.close()
