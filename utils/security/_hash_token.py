import hashlib
from ._base import _TOKEN_SALT


def _hash_token(token: str) -> str:
    """对 token 进行哈希处理"""
    return hashlib.sha256(f"{_TOKEN_SALT}{token}".encode()).hexdigest()
