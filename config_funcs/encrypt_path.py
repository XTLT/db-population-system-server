"""加密数据目录路径（写入配置文件用）。"""

import base64

from .get_fernet import get_fernet


def encrypt_path(path):
    fernet = get_fernet()
    encrypted = fernet.encrypt(path.encode("utf-8"))
    return base64.b64encode(encrypted).decode("ascii")
