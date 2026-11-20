"""把 SQLite 数据库文件加密成 DB_PATH + '.enc'（AES-GCM）。"""

import os
import secrets

from .derive_key import derive_key


def encrypt_database(password: str):
    from .. import _base

    DB_PATH = _base.DB_PATH
    if not os.path.exists(DB_PATH):
        return
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception as e:
        _base.logger.warning(f"数据库检查点失败: {e}")
    salt = secrets.token_bytes(32)
    key = derive_key(password, salt)
    with open(DB_PATH, 'rb') as f:
        data = f.read()

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, data, None)

    with open(DB_PATH + '.enc', 'wb') as f:
        f.write(salt + nonce + encrypted)

    os.remove(DB_PATH)
    for ext in ['-wal', '-shm']:
        p = DB_PATH + ext
        if os.path.exists(p):
            os.remove(p)

    key_path = DB_PATH + '.key'
    if os.path.exists(key_path):
        os.remove(key_path)
