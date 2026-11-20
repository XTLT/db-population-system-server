"""argparse 子命令定义与入口调度。"""

import argparse

from .cmd_generate import cmd_generate
from .cmd_backup import cmd_backup
from .cmd_export import cmd_export
from .cmd_restore import cmd_restore
from .cmd_deploy import cmd_deploy
from .cmd_status import cmd_status


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
