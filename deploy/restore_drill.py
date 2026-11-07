"""备份恢复演练：解备份 → integrity_check → 比对各表行数 → 输出报告。

只在临时目录里操作，**不碰线上库**：把备份里的库文件复制到临时目录再打开，
演练结束删除临时目录（--keep 可保留）。

用法：
    python deploy/restore_drill.py                     # 演练最近一份完整备份
    python deploy/restore_drill.py --list               # 列出可用备份
    python deploy/restore_drill.py --backup backup_20261107_214248
    python deploy/restore_drill.py --password 你的库密码  # 加密备份（默认取库密码）
    python deploy/restore_drill.py --no-compare         # 不与线上库比对行数
    python deploy/restore_drill.py --keep               # 保留临时目录

退出码：0 = PASS，1 = FAIL。
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import BACKUP_DIR, DB_PATH, LOG_DIR  # noqa: E402

# 用户口径的必检表：人员 + 6 张补贴表
CORE_TABLES = [
    ("persons", "人员"),
    ("land_subsidy", "地力补贴"),
    ("dibao_payment", "低保"),
    ("tekun_payment", "特困"),
    ("elderly_allowance", "高龄补贴"),
    ("disability_care_payment", "残疾人护理补贴"),
    ("pension_insurance", "养老保险"),
]

# 附加信息（报告里展示，不影响 PASS/FAIL 判定）
EXTRA_TABLES = [
    ("users", "用户"),
    ("student_education", "就读信息"),
    ("education_history", "就读历史"),
    ("operation_logs", "操作日志"),
    ("report_operation_logs", "报表日志"),
    ("deleted_persons", "已删除人员"),
]

MANIFEST_NAME = "backup_complete.txt"
DB_FILE_NAME = "population.db"
ENC_FILE_NAME = "population.db.enc"


def list_backups():
    """列出所有带 manifest 的备份目录，按目录名（即时间）倒序。"""
    items = []
    if not os.path.isdir(BACKUP_DIR):
        return items
    for name in os.listdir(BACKUP_DIR):
        if not name.startswith("backup_"):
            continue
        path = os.path.join(BACKUP_DIR, name)
        if not os.path.isdir(path):
            continue
        manifest_path = os.path.join(path, MANIFEST_NAME)
        if not os.path.exists(manifest_path):
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            continue
        items.append({"name": name, "path": path, "manifest": manifest})
    items.sort(key=lambda x: x["name"], reverse=True)
    return items


def _table_counts(db_path, tables):
    """返回 {table: count}；表不存在或读取失败记 None。"""
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


def _integrity_check(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return "; ".join(str(r[0]) for r in rows)
    finally:
        conn.close()


def _prepare_tmp_backup(src_dir):
    """把备份里的库文件复制到临时目录（只复制 db / enc / manifest，照片不参与演练）。"""
    tmp_dir = tempfile.mkdtemp(prefix="restore_drill_")
    for name in (DB_FILE_NAME, ENC_FILE_NAME, MANIFEST_NAME):
        src = os.path.join(src_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(tmp_dir, name))
    return tmp_dir


def run_drill(backup, password=None, compare_live=True, keep=False):
    name = backup["name"]
    manifest = backup["manifest"]
    encrypted = bool(manifest.get("encrypted"))
    problems = []

    if not manifest.get("complete"):
        return {
            "result": "FAIL",
            "backup": name,
            "problems": ["备份清单标记为不完整（complete != true）"],
        }

    tmp_dir = _prepare_tmp_backup(backup["path"])
    try:
        if encrypted:
            if not password:
                return {
                    "result": "FAIL",
                    "backup": name,
                    "problems": ["备份已加密，但未提供解密密码"],
                }
            from excel_importer import _decrypt_backup
            _decrypt_backup(tmp_dir, password)

        db_file = os.path.join(tmp_dir, DB_FILE_NAME)
        if not os.path.exists(db_file):
            return {
                "result": "FAIL",
                "backup": name,
                "problems": ["备份目录里没有可用的 population.db（解密失败或文件缺失）"],
            }

        integrity = _integrity_check(db_file)
        if integrity.lower() != "ok":
            problems.append(f"integrity_check 未通过: {integrity}")

        counts = _table_counts(db_file, CORE_TABLES)
        extra_counts = _table_counts(db_file, EXTRA_TABLES)
        for table, _label in CORE_TABLES:
            if counts.get(table) is None:
                problems.append(f"关键表缺失或不可读: {table}")

        live_counts = {}
        if compare_live and os.path.exists(DB_PATH):
            try:
                live_counts = _table_counts(DB_PATH, CORE_TABLES + EXTRA_TABLES)
            except Exception as e:
                problems.append(f"读取线上库失败（仅影响比对，不影响备份可用性）: {e}")

        table_rows = []
        for table, label in CORE_TABLES + EXTRA_TABLES:
            backup_rows = counts.get(table) if table in counts else extra_counts.get(table)
            live_rows = live_counts.get(table)
            row = {
                "table": table,
                "label": label,
                "backup_rows": backup_rows,
                "live_rows": live_rows,
            }
            if backup_rows is not None and live_rows is not None:
                row["delta_since_backup"] = live_rows - backup_rows
            table_rows.append(row)

        return {
            "result": "FAIL" if problems else "PASS",
            "backup": name,
            "backup_timestamp": manifest.get("timestamp"),
            "encrypted": encrypted,
            "integrity": integrity,
            "integrity_ok": integrity.lower() == "ok",
            "manifest_method": manifest.get("method", ""),
            "tables": table_rows,
            "problems": problems,
        }
    finally:
        if keep:
            print(f"[keep] 临时目录保留在: {tmp_dir}")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _print_report(report):
    print(f"备份: {report['backup']}  时间戳: {report.get('backup_timestamp', '-')}")
    print(f"加密: {'是' if report.get('encrypted') else '否'}  "
          f"integrity_check: {report.get('integrity', '-')}")
    print("")
    print(f"{'表':28s}{'备份行数':>10s}{'线上行数':>10s}{'差异':>10s}  说明")
    print("-" * 78)
    for row in report.get("tables", []):
        left = row["backup_rows"]
        right = row["live_rows"]
        delta = row.get("delta_since_backup")
        left_s = "-" if left is None else str(left)
        right_s = "-" if right is None else str(right)
        delta_s = "-" if delta is None else f"{delta:+d}"
        print(f"{row['label'] + '(' + row['table'] + ')':28s}{left_s:>10s}{right_s:>10s}{delta_s:>10s}")
    print("")
    if report.get("problems"):
        print("问题:")
        for p in report["problems"]:
            print(f"  - {p}")
    print(f"结论: {report['result']}")


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

    _print_report(report)

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


if __name__ == "__main__":
    sys.exit(main())
