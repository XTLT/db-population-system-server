#!/usr/bin/env python3
"""
证书管理工具

用于管理 SSL 自签名证书的生成、备份、导出和部署。

使用方法:
    python cert_manager.py generate              # 生成新证书
    python cert_manager.py backup /path/to/dir   # 备份证书到指定目录
    python cert_manager.py export                # 导出到客户端
    python cert_manager.py restore /path/to/dir  # 从备份恢复证书
    python cert_manager.py status                # 查看证书状态
    python cert_manager.py deploy user@host      # 部署到远程服务器

注意: 证书文件包含私钥，请妥善保管，不要上传到代码仓库！
"""

import os
import sys
import shutil
import subprocess
import argparse
from datetime import datetime

# 添加 server 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    from config import CERT_DIR
    from ssl_utils import generate_self_signed_cert
except ImportError:
    # 默认路径
    CERT_DIR = os.path.join(os.path.dirname(__file__), 'server', 'data', 'certs')


def get_cert_files():
    """获取证书文件路径"""
    cert_file = os.path.join(CERT_DIR, "server.crt")
    key_file = os.path.join(CERT_DIR, "server.key")
    return cert_file, key_file


def cmd_generate(args):
    """生成新证书"""
    cert_file, key_file = get_cert_files()
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("⚠️  证书已存在！")
        print(f"   证书位置: {cert_file}")
        print(f"   私钥位置: {key_file}")
        
        if not args.force:
            print("\n如需重新生成，请使用 --force 参数")
            return False
        
        # 备份旧证书
        backup_dir = os.path.join(os.path.dirname(cert_file), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if os.path.exists(cert_file):
            shutil.copy2(cert_file, os.path.join(backup_dir, f"server_{timestamp}.crt"))
            os.remove(cert_file)  # 删除旧证书
        if os.path.exists(key_file):
            shutil.copy2(key_file, os.path.join(backup_dir, f"server_{timestamp}.key"))
            os.remove(key_file)  # 删除旧私钥
        
        print(f"✓ 旧证书已备份到: {backup_dir}")
    
    # 生成证书
    print("\n正在生成证书...")
    os.makedirs(CERT_DIR, exist_ok=True)
    
    try:
        cert_file, key_file = generate_self_signed_cert()
        if cert_file and key_file:
            print("\n✓ 证书生成成功！")
            print(f"   证书位置: {cert_file}")
            print(f"   私钥位置: {key_file}")
            print("   有效期: 10 年")
            print("\n⚠️  请立即备份证书文件！")
            print("   私钥文件请妥善保管，不要上传到代码仓库！")
            return True
        else:
            print("✗ 证书生成失败")
            return False
    except Exception as e:
        print(f"✗ 证书生成失败: {e}")
        return False


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


def cmd_export(args):
    """导出证书到客户端"""
    cert_file, key_file = get_cert_files()
    
    if not os.path.exists(cert_file):
        print("✗ 证书文件不存在，请先生成证书")
        print("  运行: python cert_manager.py generate")
        return False
    
    script_dir = os.path.dirname(__file__)
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
    script_dir = os.path.dirname(__file__)
    
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


def main():
    parser = argparse.ArgumentParser(
        description="证书管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s generate                    # 生成新证书
  %(prog)s backup ~/certs_backup       # 备份到 ~/certs_backup
  %(prog)s export --all                # 导出到所有客户端
  %(prog)s restore ~/certs_backup      # 从备份恢复
  %(prog)s deploy user@192.168.1.100:/opt/app/data/certs  # 部署到远程服务器

⚠️  证书文件包含私钥，请妥善保管，不要上传到代码仓库！
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # generate
    p_gen = subparsers.add_parser("generate", help="生成新证书")
    p_gen.add_argument("--force", action="store_true", help="强制重新生成")
    p_gen.set_defaults(func=cmd_generate)
    
    # backup
    p_backup = subparsers.add_parser("backup", help="备份证书")
    p_backup.add_argument("destination", nargs="?", help="备份目录")
    p_backup.set_defaults(func=cmd_backup)
    
    # export
    p_export = subparsers.add_parser("export", help="导出到客户端")
    p_export.add_argument("--desktop", action="store_true", help="导出到 Desktop")
    p_export.add_argument("--mobile", action="store_true", help="导出到 Mobile")
    p_export.add_argument("--all", action="store_true", help="导出到所有客户端")
    p_export.set_defaults(func=cmd_export)
    
    # restore
    p_restore = subparsers.add_parser("restore", help="从备份恢复")
    p_restore.add_argument("source", nargs="?", help="备份目录")
    p_restore.set_defaults(func=cmd_restore)
    
    # deploy
    p_deploy = subparsers.add_parser("deploy", help="部署到远程服务器")
    p_deploy.add_argument("host", nargs="?", help="远程服务器 (user@host:/path)")
    p_deploy.set_defaults(func=cmd_deploy)
    
    # status
    p_status = subparsers.add_parser("status", help="查看证书状态")
    p_status.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    if hasattr(args, 'func'):
        args.func(args)


if __name__ == "__main__":
    main()
