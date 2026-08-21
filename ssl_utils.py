import os
import subprocess
import stat
from config import CERT_DIR


def ensure_cert_dir():
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR, exist_ok=True)
    os.chmod(CERT_DIR, stat.S_IRWXU)


def generate_self_signed_cert():
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
            "-days", "365", "-nodes",
            "-subj", "/C=CN/ST=Local/L=Local/O=Population/CN=localhost"
        ], check=True, capture_output=True)
        os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
        os.chmod(cert_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        return cert_file, key_file
    except Exception as e:
        print(f"证书生成失败: {e}")
        return None, None


def get_cert_paths():
    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")
    return cert_file, key_file
