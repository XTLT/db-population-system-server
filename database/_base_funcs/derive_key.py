"""从口令与盐派生 AES 密钥（PBKDF2-HMAC-SHA256）。"""

import hashlib


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
