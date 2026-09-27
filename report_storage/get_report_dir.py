import os
from datetime import datetime
from config import REPORTS_DIR


def get_report_dir(username: str, report_name: str) -> str:
    now = datetime.now()
    safe_name = report_name.replace("/", "_").replace("\\", "_")
    path = os.path.join(
        REPORTS_DIR,
        str(now.year), str(now.month).zfill(2), str(now.day).zfill(2),
        username, safe_name
    )
    os.makedirs(path, exist_ok=True)
    return path
