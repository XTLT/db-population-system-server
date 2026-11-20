"""按本机密钥构造 Fernet 实例。"""

from cryptography.fernet import Fernet

from .get_machine_key import get_machine_key


def get_fernet():
    key = get_machine_key()
    return Fernet(key)
