"""导出证书到客户端（Desktop / Mobile）。"""

import os
import shutil

from .cert_env import SCRIPT_DIR
from .get_cert_files import get_cert_files


def cmd_export(args):
    """导出证书到客户端"""
    cert_file, key_file = get_cert_files()

    if not os.path.exists(cert_file):
        print("✗ 证书文件不存在，请先生成证书")
        print("  运行: python cert_manager.py generate")
        return False

    script_dir = SCRIPT_DIR
    exported = []

    # 导出到 Desktop
    if args.desktop or args.all:
        desktop_dir = os.path.join(script_dir, "desktop", "certs")
        os.makedirs(desktop_dir, exist_ok=True)
        shutil.copy2(cert_file, os.path.join(desktop_dir, "server.crt"))
        print(f"✓ 已导出到 Desktop: {desktop_dir}/server.crt")
        exported.append("desktop")

    # 导出到 Mobile
    if args.mobile or args.all:
        mobile_dir = os.path.join(script_dir, "mobile", "assets", "certs")
        os.makedirs(mobile_dir, exist_ok=True)
        shutil.copy2(cert_file, os.path.join(mobile_dir, "server.crt"))
        print(f"✓ 已导出到 Mobile: {mobile_dir}/server.crt")
        print("  提示: Mobile 端需要重新构建 APP")
        exported.append("mobile")

    if not exported:
        print("请指定导出目标: --desktop, --mobile 或 --all")
        return False

    print("\n✓ 导出完成！")
    if "mobile" in exported:
        print("\n下一步: 构建 Mobile APP")
        print("  cd mobile && flutter build apk")

    return True
