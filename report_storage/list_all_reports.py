import os
import json
from config import REPORTS_DIR


def list_all_reports() -> list:
    reports = []
    if not os.path.exists(REPORTS_DIR):
        return reports
    for year in os.listdir(REPORTS_DIR):
        year_path = os.path.join(REPORTS_DIR, year)
        if not os.path.isdir(year_path):
            continue
        for month in os.listdir(year_path):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue
            for day in os.listdir(month_path):
                day_path = os.path.join(month_path, day)
                if not os.path.isdir(day_path):
                    continue
                for user in os.listdir(day_path):
                    user_path = os.path.join(day_path, user)
                    if not os.path.isdir(user_path):
                        continue
                    for report_name in os.listdir(user_path):
                        report_path = os.path.join(user_path, report_name)
                        meta_path = os.path.join(report_path, "meta.json")
                        if os.path.exists(meta_path):
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            meta["server_path"] = report_path
                            reports.append(meta)
    return reports
