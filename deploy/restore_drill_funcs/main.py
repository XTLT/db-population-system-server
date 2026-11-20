"""恢复演练命令行入口。"""

import argparse
import json
import os
import tempfile
from datetime import datetime

from config import BACKUP_DIR, LOG_DIR
from .list_backups import list_backups
from .run_drill import run_drill
from .print_report import print_report


def main():
    parser = argparse.ArgumentParser(description="备份恢复演练")
    parser.add_argument("--backup", help="指定备份目录名，默认最新一份")
    parser.add_argument("--list", action="store_true", help="只列出可用备份")
    parser.add_argument("--password", help="加密备份的解密密码，默认取服务端保存的库密码")
    parser.add_argument("--no-compare", action="store_true", help="不与线上库比对行数")
    parser.add_argument("--keep", action="store_true", help="保留临时解压目录")
    parser.add_argument("--json-out", help="报告 JSON 输出路径")
    args = parser.parse_args()

    backups = list_backups()
    if args.list:
        if not backups:
            print(f"没有可用备份（目录: {BACKUP_DIR}）")
            return 1
        for b in backups:
            m = b["manifest"]
            print(f"{b['name']}  encrypted={m.get('encrypted')}  "
                  f"method={m.get('method', '-')}  integrity={m.get('integrity', '-')}")
        return 0

    if not backups:
        print(f"没有可用备份（目录: {BACKUP_DIR}）")
        return 1

    if args.backup:
        matched = [b for b in backups if b["name"] == args.backup]
        if not matched:
            print(f"找不到备份: {args.backup}")
            return 1
        backup = matched[0]
    else:
        backup = backups[0]

    password = args.password
    if not password and backup["manifest"].get("encrypted"):
        from database import get_db_password
        password = get_db_password()

    report = run_drill(
        backup,
        password=password,
        compare_live=not args.no_compare,
        keep=args.keep,
    )
    report["drill_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print_report(report)

    out_path = args.json_out
    if not out_path:
        os.makedirs(LOG_DIR, exist_ok=True)
        out_path = os.path.join(
            LOG_DIR, f"restore_drill_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已写入: {out_path}")
    except PermissionError:
        # 以普通用户手动跑时 logs/ 可能属 root，退到临时目录，别让报告静默丢失
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(out_path))
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n报告目录无写权限，已改写到: {fallback}")
        except Exception as e:
            print(f"\n报告写入失败: {e}")
    except Exception as e:
        print(f"\n报告写入失败: {e}")

    return 0 if report["result"] == "PASS" else 1
