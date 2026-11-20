"""用机器标识派生本机专属的配置加密密钥。"""

import base64
import os
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_machine_key():
    import config as _cfg

    if sys.platform == "win32":
        info = (os.environ.get("COMPUTERNAME", "") + os.environ.get("USERNAME", "")).encode()
    else:
        info = (os.environ.get("HOSTNAME", "") + os.environ.get("USER", "")).encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_cfg._SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(info))
    return key
