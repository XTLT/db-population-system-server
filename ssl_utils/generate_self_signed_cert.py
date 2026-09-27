import os
import subprocess
import stat
from config import CERT_DIR
from .ensure_cert_dir import ensure_cert_dir


def generate_self_signed_cert():
    """生成自签名证书

    证书文件位置：
    - server.crt: 公钥证书（需分发到客户端）
    - server.key: 私钥（仅服务端保留，权限600）
    """
    ensure_cert_dir()

    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")

    if os.path.exists(cert_file) and os.path.exists(key_file):
        os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
        return cert_file, key_file

    try:
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_file, "-out", cert_file,
            "-days", "3650", "-nodes",  # 10年有效期
            "-subj", "/C=CN/ST=Local/L=Local/O=PopulationSystem/CN=localhost"
        ], check=True, capture_output=True)
        os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)  # 私钥仅所有者可读写
        os.chmod(cert_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 公钥可读
        return cert_file, key_file
    except Exception as e:
        print(f"证书生成失败: {e}")
        return None, None
