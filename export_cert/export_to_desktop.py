import os
import shutil
from config import CERT_DIR


def export_to_desktop():
    """导出证书到 Desktop 客户端"""
    cert_file = os.path.join(CERT_DIR, "server.crt")

    if not os.path.exists(cert_file):
        print("错误: 服务端证书不存在，请先启动服务端生成证书")
        return False

    dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "desktop", "certs")
    os.makedirs(dest_dir, exist_ok=True)

    dest_file = os.path.join(dest_dir, "server.crt")
    shutil.copy2(cert_file, dest_file)

    print(f"✓ 已导出证书到 Desktop: {dest_file}")
    return True
