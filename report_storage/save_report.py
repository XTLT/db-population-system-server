import os
import json
import hashlib
from datetime import datetime
from .get_report_dir import get_report_dir
from .encrypt_file import encrypt_file


def save_report(username: str, report_name: str, file_data: bytes, file_ext: str) -> dict:
    report_dir = get_report_dir(username, report_name)
    encrypted = encrypt_file(file_data)
    filename = f"report{file_ext}"
    filepath = os.path.join(report_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(encrypted)

    report_id = hashlib.sha256(f"{username}_{report_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    meta = {
        "report_id": report_id,
        "username": username,
        "original_name": report_name,
        "stored_filename": filename,
        "file_ext": file_ext,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_size": len(file_data),
    }
    meta_path = os.path.join(report_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log_path = os.path.join(report_dir, "operation_log.json")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({"logs": []}, f, ensure_ascii=False, indent=2)

    return meta
