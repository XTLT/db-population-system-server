"""从备份目录恢复证书到服务端。"""

import os
import shutil

from .cert_env import CERT_DIR
from .get_cert_files import get_cert_files


def cmd_restore(args):
    """从备份恢复证书"""
    if not args.source:
        print("✗ 请指定备份目录")
        print("  用法: python cert_manager.py restore /path/to/backup")
        return False

    source_dir = os.path.abspath(args.source)
    source_cert = os.path.join(source_dir, "server.crt")
    source_key = os.path.join(source_dir, "server.key")

    if not os.path.exists(source_cert) or not os.path.exists(source_key):
        print("✗ 备份目录中未找到证书文件")
        print(f"   需要: {source_cert}")
        print(f"   需要: {source_key}")
        return False

    # 恢复到服务端
    os.makedirs(CERT_DIR, exist_ok=True)

    dest_cert, dest_key = get_cert_files()
    shutil.copy2(source_cert, dest_cert)
    shutil.copy2(source_key, dest_key)
    os.chmod(dest_key, 0o600)

    print(f"✓ 证书已恢复到服务端: {CERT_DIR}")
    print(f"   证书: {dest_cert}")
    print(f"   私钥: {dest_key}")

    return True
