import secrets
from ._get_storage_password import _get_storage_password
from ._derive_key import _derive_key


def encrypt_file(data: bytes) -> bytes:
    password = _get_storage_password()
    salt = secrets.token_bytes(32)
    key = _derive_key(password, salt)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + encrypted
