"""逐条检查 persons.id_card，返回结果列表（只读）。"""

import re
import sqlite3

from utils.common.validate_id_card import validate_id_card
from .constants import PROBLEM_BY_MSG
from .gender_from_id import gender_from_id


def scan(db_path, limit=None):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        sql = "SELECT id, hu_hao, name, id_card, is_dead FROM persons"
        if limit:
            sql += " LIMIT %d" % int(limit)
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        raw = row["id_card"] or ""
        clean = re.sub(r"\s+", "", raw).upper()

        ok, msg = validate_id_card(raw)
        problem = "" if ok else PROBLEM_BY_MSG.get(msg, msg or "未知")
        detail = "" if ok else msg

        # 合法但存储值本身带空白/小写：查询、比对会出错，算"格式不规范"
        if ok and raw != clean:
            problem = "含空白字符"
            detail = "存储值含空白字符或小写 x，建议规范为纯数字大写"

        results.append({
            "id": row["id"],
            "name": row["name"] or "",
            "hu_hao": row["hu_hao"] or "",
            "id_card": raw,
            "is_dead": row["is_dead"] or "",
            "problem": problem,
            "detail": detail,
            "gender_by_id": gender_from_id(clean) if ok else "",
            "valid": bool(ok),
        })
    return results
