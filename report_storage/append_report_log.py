import os
import json


def append_report_log(report_dir: str, log_entry: dict):
    log_path = os.path.join(report_dir, "operation_log.json")
    logs = {"logs": []}
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs["logs"].append(log_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
