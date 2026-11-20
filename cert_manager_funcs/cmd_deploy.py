"""用 scp 部署证书到远程服务器。"""

import os
import subprocess

from .cert_env import CERT_DIR
from .get_cert_files import get_cert_files


def cmd_deploy(args):
    """部署证书到远程服务器"""
    cert_file, key_file = get_cert_files()

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("✗ 证书文件不存在，请先生成证书")
        return False

    if not args.host:
        print("✗ 请指定远程服务器")
        print("  用法: python cert_manager.py deploy user@server:/path")
        return False

    print(f"正在部署证书到: {args.host}")

    # 解析主机和路径
    if ':' in args.host:
        host_part, remote_path = args.host.split(':', 1)
    else:
        host_part = args.host
        remote_path = CERT_DIR

    # 使用 scp 部署
    try:
        subprocess.run([
            "scp", cert_file, key_file,
            f"{host_part}:{remote_path}"
        ], check=True)

        print(f"✓ 证书已部署到: {args.host}")
        print("\n下一步: 重启服务端")
        print(f"  ssh {host_part} 'cd /path/to/server && ./start_server.sh restart'")

        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 部署失败: {e}")
        return False
    except FileNotFoundError:
        print("✗ scp 命令不存在，请安装 openssh-client")
        return False
