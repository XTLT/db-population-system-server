import os
import stat
from config import CERT_DIR


def ensure_cert_dir():
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR, exist_ok=True)
    os.chmod(CERT_DIR, stat.S_IRWXU)
