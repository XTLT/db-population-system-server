"""获取证书文件路径。"""

import os

from .cert_env import CERT_DIR


def get_cert_files():
    """获取证书文件路径"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")
    return cert_file, key_file
