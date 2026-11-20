"""config 模块函数的统一调度出口（常量仍留在 config.py）。"""

from .migrate_old_appdata import migrate_old_appdata
from .get_machine_key import get_machine_key
from .get_fernet import get_fernet
from .encrypt_path import encrypt_path
from .decrypt_path import decrypt_path
from .get_data_dir import get_data_dir
from .ensure_dirs import ensure_dirs

__all__ = [
    'migrate_old_appdata', 'get_machine_key', 'get_fernet',
    'encrypt_path', 'decrypt_path', 'get_data_dir', 'ensure_dirs',
]
