"""database._base 中各函数的统一调度出口。

私有函数沿用拆分前的下划线名，保证 `from ._base import _migrate_db` 等
既有引用不需要改动。
"""

from .set_db_password import set_db_password
from .get_db_password import get_db_password
from .derive_key import derive_key as _derive_key
from .encrypt_database import encrypt_database
from .decrypt_database import decrypt_database
from .is_database_encrypted import is_database_encrypted
from .get_engine import get_engine
from .reset_engine import reset_engine
from .get_session import get_session
from .init_db import init_db
from .migrate_db import migrate_db as _migrate_db

__all__ = [
    'set_db_password', 'get_db_password', '_derive_key',
    'encrypt_database', 'decrypt_database', 'is_database_encrypted',
    'get_engine', 'reset_engine', 'get_session', 'init_db', '_migrate_db',
]
