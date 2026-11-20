"""database 包基础状态 + 函数出口。

模块级状态（Base / _db_password / _engine / _SessionFactory / DB_PATH / logger）
保留在本模块：models 与 database/functions 直接 `from ._base import Base / get_session`。
各函数实现已拆到 _base_funcs/，函数内部通过 `from .. import _base` 读写同一份
状态，不存在多份 engine 或 session 工厂。
"""
import logging

from sqlalchemy.orm import declarative_base

from config import DB_PATH

SERVICE_NAME = "population-query-system"
logger = logging.getLogger('population_system')

Base = declarative_base()

_db_password = None
_engine = None
_SessionFactory = None


from ._base_funcs import (  # noqa: E402,F401
    set_db_password,
    get_db_password,
    _derive_key,
    encrypt_database,
    decrypt_database,
    is_database_encrypted,
    get_engine,
    reset_engine,
    get_session,
    init_db,
    _migrate_db,
)

__all__ = [
    'SERVICE_NAME', 'logger', 'Base', 'DB_PATH',
    '_db_password', '_engine', '_SessionFactory',
    'set_db_password', 'get_db_password', '_derive_key',
    'encrypt_database', 'decrypt_database', 'is_database_encrypted',
    'get_engine', 'reset_engine', 'get_session', 'init_db', '_migrate_db',
]
