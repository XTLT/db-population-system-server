import os
import json
import secrets
import hashlib
from datetime import datetime
from config import REPORTS_DIR


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)


def _get_storage_password():
    from database import get_db_password
    pw = get_db_password()
    if pw:
        return pw
    return "default_report_key"


def encrypt_file(data: bytes) -> bytes:
    password = _get_storage_password()
    salt = secrets.token_bytes(32)
    key = _derive_key(password, salt)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + encrypted


def decrypt_file(encrypted_data: bytes) -> bytes:
    password = _get_storage_password()
    salt = encrypted_data[:32]
    nonce = encrypted_data[32:44]
    data = encrypted_data[44:]
    key = _derive_key(password, salt)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, data, None)


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


def load_report(report_dir: str, stored_filename: str) -> bytes:
    filepath = os.path.join(report_dir, stored_filename)
    with open(filepath, 'rb') as f:
        encrypted = f.read()
    return decrypt_file(encrypted)


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


def find_report_by_id(report_id: str) -> dict | None:
    all_reports = list_all_reports()
    for r in all_reports:
        if r.get("report_id") == report_id:
            return r
    return None


def append_report_log(report_dir: str, log_entry: dict):
    log_path = os.path.join(report_dir, "operation_log.json")
    logs = {"logs": []}
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs["logs"].append(log_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


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
