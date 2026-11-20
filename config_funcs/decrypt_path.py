"""解密配置文件里的数据目录路径。"""

import base64

from .get_fernet import get_fernet


def decrypt_path(token):
    fernet = get_fernet()
    encrypted = base64.b64decode(token)
    return fernet.decrypt(encrypted).decode("utf-8")
