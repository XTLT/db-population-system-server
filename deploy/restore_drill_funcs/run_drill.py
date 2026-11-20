"""备份恢复演练主流程：解备份 → integrity_check → 比对各表行数 → 返回报告。"""

import os
import shutil

from config import DB_PATH
from .constants import (
    CORE_TABLES, EXTRA_TABLES, DB_FILE_NAME,
)
from .prepare_tmp_backup import prepare_tmp_backup
from .integrity_check import integrity_check
from .table_counts import table_counts


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

    tmp_dir = prepare_tmp_backup(backup["path"])
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

        integrity = integrity_check(db_file)
        if integrity.lower() != "ok":
            problems.append(f"integrity_check 未通过: {integrity}")

        counts = table_counts(db_file, CORE_TABLES)
        extra_counts = table_counts(db_file, EXTRA_TABLES)
        for table, _label in CORE_TABLES:
            if counts.get(table) is None:
                problems.append(f"关键表缺失或不可读: {table}")

        live_counts = {}
        if compare_live and os.path.exists(DB_PATH):
            try:
                live_counts = table_counts(DB_PATH, CORE_TABLES + EXTRA_TABLES)
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
