import argparse
from ssl_utils import generate_self_signed_cert
from .export_to_desktop import export_to_desktop
from .export_to_mobile import export_to_mobile
from .show_cert_info import show_cert_info


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
