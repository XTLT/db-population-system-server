"""全库身份证体检：格式 / 校验位 / 出生日期，输出问题清单。

**只读不改数据**：只对 persons.id_card 做检查，不修正、不写库。
合法性判定复用服务端基准实现 utils/common/validate_id_card.py，
保证与三端录入校验口径完全一致。

用法：
    python deploy/check_id_cards.py                    # 扫线上库，输出 CSV 到 logs/
    python deploy/check_id_cards.py --output x.csv
    python deploy/check_id_cards.py --db /path/to/population.db
    python deploy/check_id_cards.py --limit 50         # 只扫前 50 条（自测用）
    python deploy/check_id_cards.py --include-ok       # CSV 里也写入合法行

说明：persons 表没有 gender 字段，无法做"第 17 位与性别一致性"比对；
本脚本只输出由身份证推算的性别供人工核对，不做断言。
"""
import argparse
import csv
import os
import re
import sqlite3
import sys
import tempfile
from collections import Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import DB_PATH, LOG_DIR  # noqa: E402
from utils.common.validate_id_card import validate_id_card  # noqa: E402

# validate_id_card 的 8 句固定文案 -> 体检问题分类
PROBLEM_BY_MSG = {
    "身份证号不能为空": "缺失",
    "身份证号必须为18位": "位数错误",
    "身份证号前17位必须为数字": "前17位非数字",
    "身份证号最后一位必须为数字或X": "末位非法",
    "身份证号校验位错误": "校验位错误",
    "身份证号出生年份无效": "出生年份无效",
    "身份证号出生月份无效": "出生月份无效",
    "身份证号出生日期无效": "出生日期无效",
}


def _gender_from_id(clean_id):
    """按第 17 位（索引 16）奇偶推算性别；仅对合法 18 位号有效。"""
    if len(clean_id) != 18:
        return ""
    ch = clean_id[16]
    if not re.fullmatch(r"[0-9]", ch):
        return ""
    return "男" if int(ch) % 2 == 1 else "女"


def scan(db_path, limit=None):
    """返回逐条检查结果列表。"""
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
            "gender_by_id": _gender_from_id(clean) if ok else "",
            "valid": bool(ok),
        })
    return results


def write_csv(results, output, include_ok=False):
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
    written = 0
    # utf-8-sig：Excel 直接双击打开不乱码
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "户号", "身份证（库中原文）", "问题类型", "说明",
                         "是否死亡", "推算性别", "内部ID"])
        for r in results:
            if not include_ok and r["valid"] and not r["problem"]:
                continue
            writer.writerow([r["name"], r["hu_hao"], r["id_card"], r["problem"],
                             r["detail"], r["is_dead"], r["gender_by_id"], r["id"]])
            written += 1
    return written


def main():
    parser = argparse.ArgumentParser(description="全库身份证体检（只读，不改数据）")
    parser.add_argument("--db", default=DB_PATH, help="数据库路径，默认用 config.DB_PATH")
    parser.add_argument("--output", help="CSV 输出路径，默认 logs/id_card_check_<时间>.csv")
    parser.add_argument("--limit", type=int, help="只扫描前 N 条（自测用）")
    parser.add_argument("--include-ok", action="store_true", help="CSV 里也写入合法记录")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"数据库不存在: {args.db}")
        return 1

    started = datetime.now()
    results = scan(args.db, limit=args.limit)

    total = len(results)
    problem_rows = [r for r in results if r["problem"]]
    ok_count = sum(1 for r in results if r["valid"] and not r["problem"])
    by_type = Counter(r["problem"] for r in problem_rows)
    male = sum(1 for r in results if r["gender_by_id"] == "男")
    female = sum(1 for r in results if r["gender_by_id"] == "女")

    output = args.output
    if not output:
        os.makedirs(LOG_DIR, exist_ok=True)
        output = os.path.join(LOG_DIR, f"id_card_check_{started:%Y%m%d_%H%M%S}.csv")
    try:
        written = write_csv(results, output, include_ok=args.include_ok)
    except PermissionError:
        # 以普通用户手动跑时 logs/ 可能属 root，退到临时目录，别让清单静默丢失
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(output))
        written = write_csv(results, fallback, include_ok=args.include_ok)
        output = fallback
        print(f"默认目录无写权限，CSV 已改写到: {output}")

    print(f"数据库: {args.db}")
    print(f"扫描 {total} 条：合法 {ok_count} 条，问题 {len(problem_rows)} 条"
          f"（CSV 写入 {written} 行，{'含' if args.include_ok else '不含'}合法记录）")
    if by_type:
        print("问题分类：")
        for name, count in by_type.most_common():
            print(f"  {name:12s} {count}")
    print(f"按身份证推算性别：男 {male} / 女 {female}"
          f"（persons 无 gender 字段，仅供人工核对）")
    print(f"问题清单: {output}")
    print(f"耗时: {(datetime.now() - started).total_seconds():.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
