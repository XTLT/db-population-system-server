import os
from config import CERT_DIR


def get_cert_paths():
    """获取证书文件路径"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")
    return cert_file, key_file
