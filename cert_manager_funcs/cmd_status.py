"""查看服务端与各客户端证书状态。"""

import os
import subprocess

from .cert_env import CERT_DIR, SCRIPT_DIR
from .get_cert_files import get_cert_files


def cmd_status(args):
    """查看证书状态"""
    cert_file, key_file = get_cert_files()

    print("证书状态")
    print("=" * 50)
    print(f"证书目录: {CERT_DIR}")
    print()

    # 检查证书文件
    if os.path.exists(cert_file):
        print(f"✓ 证书文件存在: {cert_file}")

        # 获取证书信息
        try:
            result = subprocess.run(
                ["openssl", "x509", "-in", cert_file, "-noout", "-subject", "-dates"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("\n证书信息:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
        except FileNotFoundError:
            print("  (openssl 未安装，无法查看详细信息)")
    else:
        print(f"✗ 证书文件不存在: {cert_file}")

    print()

    if os.path.exists(key_file):
        print(f"✓ 私钥文件存在: {key_file}")
        # 检查权限
        mode = oct(os.stat(key_file).st_mode)[-3:]
        if mode == "600":
            print(f"  权限正确: {mode}")
        else:
            print(f"  ⚠️ 权限不安全: {mode}，应为 600")
    else:
        print(f"✗ 私钥文件不存在: {key_file}")

    # 检查客户端证书
    print("\n客户端证书状态:")
    script_dir = SCRIPT_DIR

    desktop_cert = os.path.join(script_dir, "desktop", "certs", "server.crt")
    if os.path.exists(desktop_cert):
        print(f"✓ Desktop: {desktop_cert}")
    else:
        print("✗ Desktop: 未部署")

    mobile_cert = os.path.join(script_dir, "mobile", "assets", "certs", "server.crt")
    if os.path.exists(mobile_cert):
        print(f"✓ Mobile: {mobile_cert}")
    else:
        print("✗ Mobile: 未部署")

    print("\n" + "=" * 50)
    print("提示:")
    print("  - 生成证书: python cert_manager.py generate")
    print("  - 备份证书: python cert_manager.py backup /path/to/backup")
    print("  - 导出证书: python cert_manager.py export --all")
    print("  - 部署证书: python cert_manager.py deploy user@server:/path")
