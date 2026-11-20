"""解密 DB_PATH + '.enc' 回写为明文数据库；无加密文件视为成功。"""

import os

from .derive_key import derive_key


def decrypt_database(password: str) -> bool:
    from .._base import DB_PATH

    enc_path = DB_PATH + '.enc'
    if not os.path.exists(enc_path):
        return True
    try:
        with open(enc_path, 'rb') as f:
            content = f.read()

        if len(content) < 44:
            return False

        salt = content[:32]
        nonce = content[32:44]
        encrypted = content[44:]

        key = derive_key(password, salt)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        data = aesgcm.decrypt(nonce, encrypted, None)

        with open(DB_PATH, 'wb') as f:
            f.write(data)
        return True
    except Exception:
        return False
