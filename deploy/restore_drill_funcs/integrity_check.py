"""对指定库执行 PRAGMA integrity_check。"""

import sqlite3


def integrity_check(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return "; ".join(str(r[0]) for r in rows)
    finally:
        conn.close()
