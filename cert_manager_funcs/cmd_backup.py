"""备份证书到指定目录。"""

import os
import shutil

from .get_cert_files import get_cert_files


def cmd_backup(args):
    """备份证书到指定目录"""
    cert_file, key_file = get_cert_files()

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("✗ 证书文件不存在，请先生成证书")
        print("  运行: python cert_manager.py generate")
        return False

    if not args.destination:
        print("✗ 请指定备份目录")
        print("  用法: python cert_manager.py backup /path/to/backup")
        return False

    dest_dir = os.path.abspath(args.destination)
    os.makedirs(dest_dir, exist_ok=True)

    # 复制证书
    dest_cert = os.path.join(dest_dir, "server.crt")
    dest_key = os.path.join(dest_dir, "server.key")

    shutil.copy2(cert_file, dest_cert)
    shutil.copy2(key_file, dest_key)

    # 设置私钥权限
    os.chmod(dest_key, 0o600)

    print(f"✓ 证书已备份到: {dest_dir}")
    print(f"   证书: {dest_cert}")
    print(f"   私钥: {dest_key}")
    print("\n⚠️  备份目录请妥善保管，建议:")
    print("   1. 复制到U盘或移动硬盘")
    print("   2. 上传到私有云盘（不要上传到公共仓库！）")
    print("   3. 记录备份位置")

    return True
