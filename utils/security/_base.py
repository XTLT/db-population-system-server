import os
import secrets
import hashlib
import functools
import logging
import json
from datetime import datetime, timedelta
from flask import request, jsonify

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    logging.warning("argon2-cffi 未安装，使用 SHA256 密码哈希")

logger = logging.getLogger('population_system')

# Argon2 密码哈希器
if ARGON2_AVAILABLE:
    _ph = PasswordHasher(
        time_cost=3,        # 迭代次数
        memory_cost=65536,  # 内存成本 (64MB)
        parallelism=4,      # 并行度
        hash_len=32,        # 哈希长度
        salt_len=16         # 盐值长度
    )

MAX_CONCURRENT_SESSIONS = 3
DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')

_id_card_query_times = {}
ID_CARD_QUERY_LIMIT = 30
ID_CARD_QUERY_WINDOW = 60

from ._get_or_create_salt import _get_or_create_salt
_TOKEN_SALT = _get_or_create_salt()
