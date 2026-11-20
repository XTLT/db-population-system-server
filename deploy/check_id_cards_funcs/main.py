"""全库身份证体检命令行入口。"""

import argparse
import os
import tempfile
from collections import Counter
from datetime import datetime

from config import DB_PATH, LOG_DIR
from .scan import scan
from .write_csv import write_csv


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
