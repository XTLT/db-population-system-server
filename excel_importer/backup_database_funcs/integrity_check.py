"""对库文件跑 PRAGMA integrity_check，返回结果文本（正常为 "ok"）。"""

import sqlite3


def integrity_check(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return "; ".join(str(r[0]) for r in rows)
    finally:
        conn.close()
