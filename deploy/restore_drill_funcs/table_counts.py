"""返回 {table: count}；表不存在或读取失败记 None。"""

import sqlite3


def table_counts(db_path, tables):
    conn = sqlite3.connect(db_path, timeout=30)
    result = {}
    try:
        for table, _label in tables:
            try:
                result[table] = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
            except Exception:
                result[table] = None
    finally:
        conn.close()
    return result
