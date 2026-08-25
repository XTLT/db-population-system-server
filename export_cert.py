#!/usr/bin/env python3
"""
导出服务端证书到客户端

使用方法:
    python export_cert.py [--desktop] [--mobile]

选项:
    --desktop   导出到 Desktop 客户端
    --mobile    导出到 Mobile 客户端
    --all       导出到所有客户端
"""

import os
import sys
import shutil
import argparse

# 添加 server 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CERT_DIR
from ssl_utils import generate_self_signed_cert


def export_to_desktop():
    """导出证书到 Desktop 客户端"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    
    if not os.path.exists(cert_file):
        print("错误: 服务端证书不存在，请先启动服务端生成证书")
        return False
    
    dest_dir = os.path.join(os.path.dirname(__file__), "..", "desktop", "certs")
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_file = os.path.join(dest_dir, "server.crt")
    shutil.copy2(cert_file, dest_file)
    
    print(f"✓ 已导出证书到 Desktop: {dest_file}")
    return True


def export_to_mobile():
    """导出证书到 Mobile 客户端"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    
    if not os.path.exists(cert_file):
        print("错误: 服务端证书不存在，请先启动服务端生成证书")
        return False
    
    dest_dir = os.path.join(os.path.dirname(__file__), "..", "mobile", "assets", "certs")
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_file = os.path.join(dest_dir, "server.crt")
    shutil.copy2(cert_file, dest_file)
    
    print(f"✓ 已导出证书到 Mobile: {dest_file}")
    print("  提示: Mobile 端需要重新构建 APP 才能生效")
    return True


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


def main():
    parser = argparse.ArgumentParser(description="导出服务端证书到客户端")
    parser.add_argument("--desktop", action="store_true", help="导出到 Desktop 客户端")
    parser.add_argument("--mobile", action="store_true", help="导出到 Mobile 客户端")
    parser.add_argument("--all", action="store_true", help="导出到所有客户端")
    parser.add_argument("--info", action="store_true", help="显示证书信息")
    parser.add_argument("--generate", action="store_true", help="生成新证书")
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if not any([args.desktop, args.mobile, args.all, args.info, args.generate]):
        parser.print_help()
        show_cert_info()
        return
    
    if args.info:
        show_cert_info()
        return
    
    if args.generate:
        print("正在生成自签名证书...")
        cert_file, key_file = generate_self_signed_cert()
        if cert_file:
            print(f"✓ 证书已生成: {cert_file}")
            print(f"✓ 私钥已生成: {key_file}")
        else:
            print("✗ 证书生成失败")
        return
    
    if args.all:
        args.desktop = True
        args.mobile = True
    
    if args.desktop:
        export_to_desktop()
    
    if args.mobile:
        export_to_mobile()
    
    print("\n部署完成！")


if __name__ == "__main__":
    main()
