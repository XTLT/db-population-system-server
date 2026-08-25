import os
import subprocess
import stat
from config import CERT_DIR


def ensure_cert_dir():
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR, exist_ok=True)
    os.chmod(CERT_DIR, stat.S_IRWXU)


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


def get_cert_paths():
    """获取证书文件路径"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")
    return cert_file, key_file


def get_certificate_pem() -> str:
    """获取证书 PEM 内容（用于客户端证书固定）"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    if os.path.exists(cert_file):
        with open(cert_file, 'r') as f:
            return f.read()
    return ""


def get_certificate_fingerprint() -> str:
    """获取证书 SHA256 指纹（用于客户端验证）"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    if not os.path.exists(cert_file):
        return ""
    
    try:
        result = subprocess.run(
            ["openssl", "x509", "-in", cert_file, "-noout", "-fingerprint", "-sha256"],
            capture_output=True, text=True
        )
        # 输出格式: SHA256 Fingerprint=XX:XX:XX:...
        fingerprint = result.stdout.strip().split('=')[1] if '=' in result.stdout else ""
        return fingerprint.replace(':', '').lower()
    except Exception:
        return ""
