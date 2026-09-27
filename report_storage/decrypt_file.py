from ._get_storage_password import _get_storage_password
from ._derive_key import _derive_key


def decrypt_file(encrypted_data: bytes) -> bytes:
    password = _get_storage_password()
    salt = encrypted_data[:32]
    nonce = encrypted_data[32:44]
    data = encrypted_data[44:]
    key = _derive_key(password, salt)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, data, None)
