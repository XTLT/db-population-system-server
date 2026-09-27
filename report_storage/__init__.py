# report_storage 包 — 向后兼容 shim
from ._derive_key import _derive_key
from ._get_storage_password import _get_storage_password
from .encrypt_file import encrypt_file
from .decrypt_file import decrypt_file
from .get_report_dir import get_report_dir
from .save_report import save_report
from .load_report import load_report
from .list_all_reports import list_all_reports
from .find_report_by_id import find_report_by_id
from .append_report_log import append_report_log
from .update_report import update_report

__all__ = [
    '_derive_key',
    '_get_storage_password',
    'encrypt_file',
    'decrypt_file',
    'get_report_dir',
    'save_report',
    'load_report',
    'list_all_reports',
    'find_report_by_id',
    'append_report_log',
    'update_report',
]
