import os
from config import CERT_DIR


def show_cert_info():
    """显示证书信息"""
    cert_file = os.path.join(CERT_DIR, "server.crt")

    if not os.path.exists(cert_file):
        print("服务端证书不存在")
        return

    print(f"\n证书文件位置: {cert_file}")
    print(f"证书目录: {CERT_DIR}")
    print()

    # 显示证书内容
    try:
        with open(cert_file, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print("证书内容预览:")
            print("-" * 40)
            for line in lines[:5]:
                print(line)
            print("...")
            for line in lines[-3:]:
                print(line)
            print("-" * 40)
    except Exception as e:
        print(f"读取证书失败: {e}")
