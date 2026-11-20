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

各子命令实现见 cert_manager_funcs/（一函数一文件）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_manager_funcs import (  # noqa: E402
    CERT_DIR, SCRIPT_DIR, get_cert_files,
    cmd_generate, cmd_backup, cmd_export, cmd_restore, cmd_deploy, cmd_status, main,
)

__all__ = [
    'CERT_DIR', 'SCRIPT_DIR', 'get_cert_files',
    'cmd_generate', 'cmd_backup', 'cmd_export', 'cmd_restore', 'cmd_deploy',
    'cmd_status', 'main',
]

if __name__ == "__main__":
    main()
