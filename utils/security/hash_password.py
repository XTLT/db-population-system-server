import secrets
import hashlib
from . import _base


def hash_password(password: str) -> str:
    """使用 Argon2 哈希密码（如果可用），否则使用 SHA256"""
    if _base.ARGON2_AVAILABLE:
        return f"argon2:{_base._ph.hash(password)}"
    else:
        salt = secrets.token_hex(16)
        password_sha256 = hashlib.sha256(password.encode()).hexdigest()
        password_hash = hashlib.sha256((salt + password_sha256).encode()).hexdigest()
        return f"sha256:{salt}:{password_hash}"
