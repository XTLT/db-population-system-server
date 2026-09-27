import os
from database import _derive_key


def _decrypt_backup(backup_dir: str, password: str):
    """解密备份文件"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    for filename in os.listdir(backup_dir):
        if filename.endswith(".enc"):
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, "rb") as f:
                content = f.read()

            salt = content[:32]
            nonce = content[32:44]
            encrypted = content[44:]

            key = _derive_key(password, salt)
            aesgcm = AESGCM(key)
            data = aesgcm.decrypt(nonce, encrypted, None)

            # 写入解密后的文件
            decrypted_path = filepath[:-4]  # 移除 .enc 后缀
            with open(decrypted_path, "wb") as f:
                f.write(data)
