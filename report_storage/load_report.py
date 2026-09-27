import os
from .decrypt_file import decrypt_file


def load_report(report_dir: str, stored_filename: str) -> bytes:
    filepath = os.path.join(report_dir, stored_filename)
    with open(filepath, 'rb') as f:
        encrypted = f.read()
    return decrypt_file(encrypted)
