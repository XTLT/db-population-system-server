import os
import json
from datetime import datetime
from .find_report_by_id import find_report_by_id
from .encrypt_file import encrypt_file


def update_report(report_id: str, file_data: bytes, file_ext: str) -> dict | None:
    report = find_report_by_id(report_id)
    if not report:
        return None
    report_dir = report["server_path"]
    encrypted = encrypt_file(file_data)
    filename = f"report{file_ext}"
    filepath = os.path.join(report_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(encrypted)

    old_ext = report.get("file_ext", "")
    if old_ext and old_ext != file_ext:
        old_path = os.path.join(report_dir, f"report{old_ext}")
        if os.path.exists(old_path) and old_path != filepath:
            os.remove(old_path)

    meta_path = os.path.join(report_dir, "meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["stored_filename"] = filename
    meta["file_ext"] = file_ext
    meta["upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["file_size"] = len(file_data)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta
