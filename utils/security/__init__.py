# utils/security 包 — 向后兼容 shim
# 原 utils/security.py 已按"一函数一文件"拆分到本子包各文件。
from ._base import (
    ARGON2_AVAILABLE,
    logger,
    MAX_CONCURRENT_SESSIONS,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
    _id_card_query_times,
    ID_CARD_QUERY_LIMIT,
    ID_CARD_QUERY_WINDOW,
    _TOKEN_SALT,
)
from ._get_or_create_salt import _get_or_create_salt, _SALT_FILE
from ._hash_token import _hash_token
from .hash_password import hash_password
from .verify_password import verify_password
from .create_token import create_token
from .get_token_data import get_token_data
from .remove_token import remove_token
from .remove_all_user_tokens import remove_all_user_tokens
from .cleanup_expired_tokens import cleanup_expired_tokens
from .require_auth import require_auth
from .check_id_card_rate_limit import check_id_card_rate_limit

__all__ = [
    'ARGON2_AVAILABLE',
    'logger',
    'MAX_CONCURRENT_SESSIONS',
    'DEFAULT_ADMIN_USERNAME',
    'DEFAULT_ADMIN_PASSWORD',
    '_SALT_FILE',
    '_get_or_create_salt',
    '_TOKEN_SALT',
    '_hash_token',
    'hash_password',
    'verify_password',
    'create_token',
    'get_token_data',
    'remove_token',
    'remove_all_user_tokens',
    'cleanup_expired_tokens',
    'require_auth',
    '_id_card_query_times',
    'ID_CARD_QUERY_LIMIT',
    'ID_CARD_QUERY_WINDOW',
    'check_id_card_rate_limit',
]
