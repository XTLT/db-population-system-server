import os
import secrets
from database import _derive_key


def _encrypt_backup(backup_dir: str, password: str):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    salt = secrets.token_bytes(32)
    key = _derive_key(password, salt)

    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath) and filename != "backup_complete.txt":
            with open(filepath, "rb") as f:
                data = f.read()
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(key)
            encrypted = aesgcm.encrypt(nonce, data, None)
            with open(filepath + ".enc", "wb") as f:
                f.write(salt + nonce + encrypted)
            os.remove(filepath)
